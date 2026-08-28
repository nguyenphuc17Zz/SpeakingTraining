import time
from app.core.logging import logger
from app.domains.ai.contracts import AITask, ModelCapability, ModelMetadata
from app.domains.ai.registry import TASK_TIER_MAPPING, TaskTier, provider_registry


class ModelDiscoveryService:
    """Service providing dynamic model discovery, TTL caching, and tier matching for AI providers."""

    def __init__(self, ttl_seconds: float = 1800.0):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[list[ModelMetadata], float]] = {}

    def clear_cache(self, provider_id: str | None = None) -> None:
        if provider_id:
            self._cache.pop(provider_id.lower().strip(), None)
        else:
            self._cache.clear()

    async def get_models_for_provider(
        self,
        provider_id: str,
        api_key: str | None = None,
        force_refresh: bool = False,
    ) -> list[ModelMetadata]:
        pid = provider_id.lower().strip()
        now = time.time()

        if not force_refresh and pid in self._cache:
            models, expires_at = self._cache[pid]
            if now < expires_at and models:
                return models

        adapter = provider_registry.get(pid)
        if not adapter:
            return []

        try:
            models = await adapter.list_models(api_key or "")
            if models:
                self._cache[pid] = (models, now + self.ttl_seconds)
                return models
        except Exception as e:
            logger.warning(f"[ModelDiscoveryService] Failed to dynamically list models for {pid}: {e}")

        # If cache had stale data, use it as fallback
        if pid in self._cache:
            return self._cache[pid][0]

        # Otherwise fallback from adapter if available
        if hasattr(adapter, "_fallback_models"):
            return getattr(adapter, "_fallback_models")()
        return []

    async def get_all_models(
        self,
        credentials_map: dict[str, str] | None = None,
        force_refresh: bool = False,
    ) -> list[ModelMetadata]:
        all_models: list[ModelMetadata] = []
        creds = credentials_map or {}

        for pid in provider_registry.list_providers():
            api_key = creds.get(pid)
            models = await self.get_models_for_provider(
                provider_id=pid,
                api_key=api_key,
                force_refresh=force_refresh,
            )
            all_models.extend(models)

        return all_models

    def get_recommended_model_for_task(
        self,
        task: AITask,
        provider_id: str,
        available_models: list[ModelMetadata] | None = None,
    ) -> str:
        """Dynamically matches best model from available models for the given task and provider."""
        pid = provider_id.lower().strip()
        tier = TASK_TIER_MAPPING.get(task, TaskTier.BALANCED)
        models = available_models or (self._cache.get(pid, ([], 0))[0])

        if not models:
            # Safe defaults if no dynamic list available yet
            if pid == "gemini":
                return "gemini-1.5-pro" if tier == TaskTier.DEEP else "gemini-2.0-flash"
            elif pid == "groq":
                return "llama-3.1-8b-instant" if tier == TaskTier.FAST else "llama-3.3-70b-versatile"
            elif pid == "openrouter":
                return "meta-llama/llama-3.1-8b-instruct" if tier == TaskTier.FAST else "anthropic/claude-3.5-sonnet"
            return "gemini-2.0-flash"

        # Model IDs in lower case
        model_ids = [m.id for m in models]

        if pid == "gemini":
            if tier == TaskTier.DEEP:
                for candidate in ["gemini-1.5-pro", "gemini-2.0-pro-exp", "gemini-pro"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())
            else:
                for candidate in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())

        elif pid == "groq":
            if tier == TaskTier.FAST:
                for candidate in ["llama-3.1-8b", "llama3-8b", "gemma"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())
            else:
                for candidate in ["llama-3.3-70b", "llama-3.1-70b", "mixtral-8x7b"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())

        elif pid == "openrouter":
            if tier == TaskTier.FAST:
                for candidate in ["llama-3.1-8b", "flash", "mini", "haiku"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())
            else:
                for candidate in ["claude-3.5-sonnet", "deepseek-chat", "gpt-4o"]:
                    if any(candidate in mid.lower() for mid in model_ids):
                        return next(mid for mid in model_ids if candidate in mid.lower())

        # Fallback to recommended or first model
        recommended = [m.id for m in models if m.is_recommended]
        if recommended:
            return recommended[0]
        return models[0].id


# Global singleton instance
model_discovery_service = ModelDiscoveryService()
