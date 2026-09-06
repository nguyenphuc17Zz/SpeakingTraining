import numpy as np
import pytest

from app.domains.ai.bandit import ContextualFeatureExtractor, LinUCBBandit
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask


def test_feature_extractor_dimensions_and_ranges():
    """Verify feature extractor produces normalized 8-dimensional context vectors."""
    req = AIRequest(
        task=AITask.CONVERSATION,
        messages=[AIMessage(role=AIMessageRole.USER, content="こんにちは！")],
        max_output_tokens=250,
    )

    x = ContextualFeatureExtractor.extract_features(AITask.CONVERSATION, req, is_streaming=False)
    assert isinstance(x, np.ndarray)
    assert x.shape == (8,)
    assert x[0] == 1.0  # Bias
    assert x[1] == 1.0  # Conversational task
    assert 0.0 <= x[2] <= 1.0  # Latency tier
    assert 0.0 <= x[3] <= 1.0  # Prompt tokens
    assert x[4] == 0.0  # No audio/image
    assert x[5] == 0.0  # Non-streaming
    assert 0.0 <= x[7] <= 1.0  # Cyclic hour


def test_linucb_bandit_online_learning_and_convergence():
    """Verify LinUCB learns arm preferences and adapts to rewards."""
    bandit = LinUCBBandit(alpha=0.5, d=8)
    req = AIRequest(task=AITask.CONVERSATION, messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    x = ContextualFeatureExtractor.extract_features(AITask.CONVERSATION, req)

    arms = ["provider_fast", "provider_slow"]

    # Initial ranking: both have equal prior (identity matrix, zero b)
    initial_ranking = bandit.rank_arms(arms, x)
    assert len(initial_ranking) == 2
    # Scores should be identical initially due to symmetry
    assert abs(initial_ranking[0][1] - initial_ranking[1][1]) < 1e-5

    # Reward provider_fast heavily with high reward
    for _ in range(5):
        bandit.update("provider_fast", x, reward=0.9)

    # Penalize provider_slow with negative reward
    for _ in range(5):
        bandit.update("provider_slow", x, reward=-0.8)

    # Re-rank: provider_fast must now be strictly ranked #1
    updated_ranking = bandit.rank_arms(arms, x)
    assert updated_ranking[0][0] == "provider_fast"
    assert updated_ranking[0][1] > updated_ranking[1][1]


def test_linucb_reward_calculation():
    """Verify multi-objective scalar reward calculation."""
    # Fast success
    r_fast = LinUCBBandit.calculate_reward(latency_ms=250, success=True, fallback_occurred=False)
    assert r_fast > 0.8

    # Slow success
    r_slow = LinUCBBandit.calculate_reward(latency_ms=2800, success=True, fallback_occurred=False)
    assert r_slow < r_fast

    # Fallback success is penalized slightly
    r_fallback = LinUCBBandit.calculate_reward(latency_ms=250, success=True, fallback_occurred=True)
    assert r_fallback < r_fast

    # Total failure
    r_fail = LinUCBBandit.calculate_reward(latency_ms=0, success=False)
    assert r_fail == -1.0
