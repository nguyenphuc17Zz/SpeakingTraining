import time
from datetime import datetime, timezone

from app.domains.ai.contracts import ProviderHealth, ProviderHealthStatus
from app.domains.ai.errors import (
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class ProviderCircuitState:
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.consecutive_failures: int = 0
        self.total_failures: int = 0
        self.total_successes: int = 0
        self.last_failure_time: float | None = None
        self.last_success_time: float | None = None
        self.last_error_message: str | None = None
        self.cooldown_seconds: float = 30.0
        self.is_rate_limited: bool = False
        self.is_quota_exhausted: bool = False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.is_rate_limited = False
        self.is_quota_exhausted = False
        self.total_successes += 1
        self.last_success_time = time.time()
        self.last_error_message = None

    def record_failure(self, error: Exception) -> None:
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        self.last_error_message = str(error)

        if isinstance(error, ProviderRateLimitError):
            self.is_rate_limited = True
            self.cooldown_seconds = max(error.retry_after_seconds or 60.0, 30.0)
        elif isinstance(error, ProviderQuotaError):
            self.is_quota_exhausted = True
            self.cooldown_seconds = 300.0  # 5 minutes for quota
        elif isinstance(error, ProviderUnavailableError):
            self.cooldown_seconds = 30.0
        elif isinstance(error, ProviderTimeoutError):
            self.cooldown_seconds = 20.0
        else:
            self.cooldown_seconds = 15.0

    def is_available(self) -> bool:
        if self.consecutive_failures == 0:
            return True

        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        # In cooldown window
        if elapsed < self.cooldown_seconds:
            # If 3 or more consecutive failures or hard quota/rate limit, trip circuit
            if self.consecutive_failures >= 3 or self.is_rate_limited or self.is_quota_exhausted:
                return False

        # Cooldown expired -> half-open trial
        return True

    def get_status(self, is_configured: bool) -> ProviderHealthStatus:
        if not is_configured:
            return ProviderHealthStatus.NOT_CONFIGURED
        if not self.is_available():
            return ProviderHealthStatus.UNAVAILABLE
        if self.consecutive_failures > 0:
            return ProviderHealthStatus.DEGRADED
        return ProviderHealthStatus.HEALTHY


class CircuitBreakerManager:
    """In-memory circuit breaker and health telemetry for AI providers."""

    def __init__(self):
        self._states: dict[str, ProviderCircuitState] = {}

    def _get_state(self, provider_id: str) -> ProviderCircuitState:
        pid = provider_id.lower().strip()
        if pid not in self._states:
            self._states[pid] = ProviderCircuitState(pid)
        return self._states[pid]

    def is_available(self, provider_id: str) -> bool:
        return self._get_state(provider_id).is_available()

    def record_success(self, provider_id: str) -> None:
        self._get_state(provider_id).record_success()

    def record_failure(self, provider_id: str, error: Exception) -> None:
        self._get_state(provider_id).record_failure(error)

    def get_health(self, provider_id: str, is_configured: bool) -> ProviderHealth:
        state = self._get_state(provider_id)
        status = state.get_status(is_configured)
        return ProviderHealth(
            provider_id=provider_id,
            status=status,
            is_configured=is_configured,
            last_checked_at=datetime.fromtimestamp(state.last_success_time or state.last_failure_time or time.time(), tz=timezone.utc),
            error_message=state.last_error_message,
            metadata={
                "consecutive_failures": state.consecutive_failures,
                "total_successes": state.total_successes,
                "total_failures": state.total_failures,
                "in_cooldown": not state.is_available(),
            },
        )

    def reset(self, provider_id: str | None = None) -> None:
        if provider_id:
            pid = provider_id.lower().strip()
            if pid in self._states:
                del self._states[pid]
        else:
            self._states.clear()


circuit_breaker_manager = CircuitBreakerManager()
