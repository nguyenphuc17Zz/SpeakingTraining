import math
import threading
import time
from typing import Any
import numpy as np

from app.core.logging import logger
from app.domains.ai.contracts import AIRequest, AITask


class ContextualFeatureExtractor:
    """Extracts normalized feature vector x_t in R^d for AI Routing."""

    FEATURE_DIM: int = 8

    @classmethod
    def extract_features(
        cls,
        task: AITask,
        request: AIRequest,
        is_streaming: bool = False,
    ) -> np.ndarray:
        x = np.zeros(cls.FEATURE_DIM, dtype=np.float64)

        # 0: Bias
        x[0] = 1.0

        # 1: Task Category (1.0 for conversational/realtime, 0.0 for deep analysis, 0.5 for others)
        if task in (AITask.CONVERSATION, AITask.COACH_CHAT):
            x[1] = 1.0
        elif task in (AITask.DEEP_ANALYSIS, AITask.SESSION_ANALYSIS):
            x[1] = 0.0
        else:
            x[1] = 0.5

        # 2: Latency Tier (Fast=1.0, Balanced=0.5, Deep=0.0)
        from app.domains.ai.registry import ModelRegistry, TaskTier

        tier = ModelRegistry.get_task_tier(task)
        if tier == TaskTier.FAST:
            x[2] = 1.0
        elif tier == TaskTier.BALANCED:
            x[2] = 0.5
        else:
            x[2] = 0.0

        # 3: Normalized estimated prompt tokens
        total_chars = sum(len(m.content) for m in request.messages)
        if request.system_instruction:
            total_chars += len(request.system_instruction)
        est_tokens = max(1, int(total_chars / 2.5))
        x[3] = min(1.0, est_tokens / 4000.0)

        # 4: Multimodal / Audio presence
        has_media = any(m.audio_bytes is not None or m.image_url is not None for m in request.messages)
        x[4] = 1.0 if has_media else 0.0

        # 5: Streaming flag
        x[5] = 1.0 if is_streaming else 0.0

        # 6: Target max output tokens normalized
        x[6] = min(1.0, (request.max_output_tokens or 500) / 2000.0)

        # 7: Time-of-day cyclic feature (hour / 24)
        hour = time.localtime().tm_hour
        x[7] = (math.sin(2 * math.pi * hour / 24.0) + 1.0) / 2.0

        return x


class LinUCBBandit:
    """Contextual Multi-Armed Bandit using the LinUCB (Disjoint Linear Models) algorithm.

    Paper: Li, Chu, Langford, Schapire (2010) - "A Contextual-Bandit Approach to Personalized Recommendation"
    For each arm a:
        A_a = D_a^T D_a + I_d
        b_a = D_a^T c_a
        theta_hat_a = A_a^{-1} b_a
        p_{t,a} = theta_hat_a^T x_t + alpha * sqrt(x_t^T A_a^{-1} x_t)
    """

    def __init__(self, alpha: float = 0.8, d: int = 8):
        self.alpha = alpha
        self.d = d
        self._lock = threading.Lock()
        # Per-arm state: {arm_id: {"A": np.ndarray (d,d), "b": np.ndarray (d,), "pulls": int}}
        self._arms: dict[str, dict[str, Any]] = {}

    def _get_arm_state(self, arm_id: str) -> dict[str, Any]:
        if arm_id not in self._arms:
            self._arms[arm_id] = {
                "A": np.identity(self.d, dtype=np.float64),
                "b": np.zeros(self.d, dtype=np.float64),
                "pulls": 0,
            }
        return self._arms[arm_id]

    def rank_arms(self, arm_candidates: list[str], context_x: np.ndarray) -> list[tuple[str, float]]:
        """Computes LinUCB score for each candidate arm and returns sorted list of (arm_id, ucb_score)."""
        with self._lock:
            scored: list[tuple[str, float]] = []
            for arm_id in arm_candidates:
                arm = self._get_arm_state(arm_id)
                a_mat = arm["A"]
                b_vec = arm["b"]

                try:
                    a_inv = np.linalg.inv(a_mat)
                except np.linalg.LinAlgError:
                    a_inv = np.identity(self.d, dtype=np.float64)

                theta = a_inv @ b_vec
                expected_reward = float(np.dot(theta, context_x))
                variance = float(context_x.T @ a_inv @ context_x)
                ucb = expected_reward + self.alpha * math.sqrt(max(1e-6, variance))
                scored.append((arm_id, ucb))

            # Rank descending
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored

    def update(
        self,
        arm_id: str,
        context_x: np.ndarray,
        reward: float,
    ) -> None:
        """Updates the ridge regression matrices A_a and b_a with observed reward r_t."""
        with self._lock:
            arm = self._get_arm_state(arm_id)
            # A_a <- A_a + x_t * x_t^T
            arm["A"] += np.outer(context_x, context_x)
            # b_a <- b_a + r_t * x_t
            arm["b"] += reward * context_x
            arm["pulls"] += 1
            logger.debug(
                f"[LinUCBBandit] Updated arm '{arm_id}': reward={reward:.2f}, total_pulls={arm['pulls']}"
            )

    @classmethod
    def calculate_reward(
        cls,
        latency_ms: int,
        success: bool,
        fallback_occurred: bool = False,
        quality_score: float = 1.0,
    ) -> float:
        """Calculates multi-objective scalar reward r_t in [-1.0, 1.0].

        Rewards speed, penalizes failures and fallbacks, and considers semantic quality.
        """
        if not success:
            return -1.0

        # Latency score: 0 to 1.0 (sub-300ms is 1.0, 3000ms+ is 0.0)
        norm_lat = max(0.0, 1.0 - min(1.0, latency_ms / 3000.0))
        reward = 0.5 * norm_lat + 0.5 * quality_score
        if fallback_occurred:
            reward -= 0.25

        return float(np.clip(reward, -1.0, 1.0))


linucb_bandit = LinUCBBandit(alpha=0.8, d=8)
