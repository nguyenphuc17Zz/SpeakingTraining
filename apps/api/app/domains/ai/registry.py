
from app.domains.ai.adapters.gemini import GeminiAdapter
from app.domains.ai.adapters.groq import GroqAdapter
from app.domains.ai.adapters.openrouter import OpenRouterAdapter
from app.domains.ai.contracts import AIProvider, AITask
from app.domains.providers.contracts import (
    ModelCapability,
    ModelMetadata,
    ProviderMetadata,
)
from app.domains.providers.registry import PROVIDERS_REGISTRY


class ProviderRegistry:
    """Registry managing AI Provider adapter instances."""

    def __init__(self):
        self._providers: dict[str, AIProvider] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(GeminiAdapter())
        self.register(GroqAdapter())
        self.register(OpenRouterAdapter())

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.provider_id.lower()] = provider

    def get(self, provider_id: str) -> AIProvider | None:
        return self._providers.get(provider_id.lower().strip())

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def has_provider(self, provider_id: str) -> bool:
        return provider_id.lower().strip() in self._providers


from enum import Enum


class TaskTier(str, Enum):
    FAST = "fast"          # High speed, low latency, low cost (e.g. grammar correction, translation, quick suggestions)
    BALANCED = "balanced"  # Natural persona conversation, interactive coaching
    DEEP = "deep"          # Comprehensive linguistics, curriculum synthesis, weekly reviews


TASK_TIER_MAPPING: dict[AITask, TaskTier] = {
    AITask.CONVERSATION: TaskTier.BALANCED,
    AITask.COACH: TaskTier.BALANCED,
    AITask.PLAYGROUND: TaskTier.BALANCED,
    AITask.GENERAL: TaskTier.BALANCED,
    AITask.DEEP_ANALYSIS: TaskTier.DEEP,
    AITask.SESSION_ANALYSIS: TaskTier.DEEP,
    AITask.CURRICULUM: TaskTier.DEEP,
    AITask.WEEKLY_REVIEW: TaskTier.DEEP,
    AITask.SHADOWING_ANALYSIS: TaskTier.DEEP,
    AITask.PRONUNCIATION_ANALYSIS: TaskTier.BALANCED,
    AITask.CONVERSATION_ANALYSIS: TaskTier.BALANCED,
    AITask.GRAMMAR_ANALYSIS: TaskTier.FAST,
    AITask.NATURALNESS_ANALYSIS: TaskTier.FAST,
    AITask.GRAMMAR_CORRECTION: TaskTier.FAST,
    AITask.TRANSLATION: TaskTier.FAST,
    AITask.SUMMARIZATION: TaskTier.FAST,
    AITask.FEEDBACK_PRIORITIZATION: TaskTier.FAST,
    AITask.INSIGHT_EXPLANATION: TaskTier.FAST,
    AITask.EXERCISE_GENERATION: TaskTier.BALANCED,
    AITask.EXERCISE_EVALUATION: TaskTier.FAST,
    AITask.RECOMMENDATION_EXPLANATION: TaskTier.FAST,
    AITask.MEMORY: TaskTier.FAST,
    AITask.VIDEO_ANALYSIS: TaskTier.BALANCED,
    AITask.SHADOWING_RECOMMENDATION: TaskTier.FAST,
    AITask.SPEECH_GENERATION: TaskTier.BALANCED,
    AITask.SPEECH_EVALUATION: TaskTier.BALANCED,
    AITask.SPEECH_COHERENCE: TaskTier.BALANCED,
    AITask.SPEECH_RELEVANCE: TaskTier.BALANCED,
    AITask.SPEECH_NATURALNESS: TaskTier.BALANCED,
    AITask.SPEECH_NATIVE_UPGRADE: TaskTier.BALANCED,
}


class ModelRegistry:
    """Registry managing model metadata and task-to-model recommendations."""

    @staticmethod
    def get_task_tier(task: AITask) -> TaskTier:
        return TASK_TIER_MAPPING.get(task, TaskTier.BALANCED)

    @staticmethod
    def get_provider_metadata(provider_id: str) -> ProviderMetadata | None:
        return PROVIDERS_REGISTRY.get(provider_id.lower().strip())

    @staticmethod
    def get_all_providers() -> list[ProviderMetadata]:
        return list(PROVIDERS_REGISTRY.values())

    @staticmethod
    def get_model(model_id: str) -> ModelMetadata | None:
        for provider in PROVIDERS_REGISTRY.values():
            for m in provider.models:
                if m.id.lower() == model_id.lower():
                    return m
        return None

    @staticmethod
    def get_models_for_provider(provider_id: str) -> list[ModelMetadata]:
        p = PROVIDERS_REGISTRY.get(provider_id.lower().strip())
        return p.models if p else []

    @staticmethod
    def get_default_model(provider_id: str) -> str:
        pid = provider_id.lower().strip()
        p = PROVIDERS_REGISTRY.get(pid)
        if p and p.default_model:
            return p.default_model
        if pid == "gemini":
            return "gemini-2.0-flash"
        elif pid == "groq":
            return "llama-3.3-70b-versatile"
        elif pid == "openrouter":
            return "anthropic/claude-3.5-sonnet"
        return "gemini-2.0-flash"

    @staticmethod
    def get_recommended_model_for_task(task: AITask, provider_id: str) -> str:
        """Selects best model for specific speaking/linguistic task based on tier and provider."""
        from app.domains.ai.discovery import model_discovery_service
        return model_discovery_service.get_recommended_model_for_task(task, provider_id)

    @staticmethod
    def supports_capability(model_id: str, capability: ModelCapability) -> bool:
        model = ModelRegistry.get_model(model_id)
        if not model:
            # If unknown custom model, assume basic text/streaming
            return capability in (ModelCapability.TEXT, ModelCapability.STREAMING)
        return capability in model.capabilities


# Global singleton registry instance
provider_registry = ProviderRegistry()
