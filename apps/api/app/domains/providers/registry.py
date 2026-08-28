
from app.domains.providers.contracts import (
    ModelCapability,
    ModelMetadata,
    ProviderMetadata,
)

PROVIDERS_REGISTRY: dict[str, ProviderMetadata] = {
    "gemini": ProviderMetadata(
        id="gemini",
        display_name="Google Gemini",
        description="Default AI provider with high-fidelity Japanese nuance, audio comprehension, and low latency.",
        default_model="gemini-1.5-flash",
        documentation_url="https://ai.google.dev/",
        models=[
            ModelMetadata(
                id="gemini-1.5-flash",
                provider_id="gemini",
                display_name="Gemini 1.5 Flash (Ultra Fast)",
                context_window=1000000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="gemini-1.5-pro",
                provider_id="gemini",
                display_name="Gemini 1.5 Pro (Deep Reasoning & Nuance)",
                context_window=2000000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.REASONING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=False,
            ),
            ModelMetadata(
                id="gemini-2.0-flash-exp",
                provider_id="gemini",
                display_name="Gemini 2.0 Flash (Next-Gen Realtime Voice Ready)",
                context_window=1000000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
        ],
    ),
    "groq": ProviderMetadata(
        id="groq",
        display_name="Groq LPU",
        description="Ultra-fast LPU inference engine for rapid conversational turns and low-latency speech feedback.",
        default_model="llama-3.3-70b-versatile",
        documentation_url="https://console.groq.com/",
        models=[
            ModelMetadata(
                id="llama-3.3-70b-versatile",
                provider_id="groq",
                display_name="Llama 3.3 70B Versatile",
                context_window=128000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="mixtral-8x7b-32768",
                provider_id="groq",
                display_name="Mixtral 8x7B 32k",
                context_window=32768,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                ],
                is_recommended=False,
            ),
        ],
    ),
    "openrouter": ProviderMetadata(
        id="openrouter",
        display_name="OpenRouter",
        description="Multi-model gateway providing access to Claude, DeepSeek, and custom models.",
        default_model="anthropic/claude-3.5-sonnet",
        documentation_url="https://openrouter.ai/",
        models=[
            ModelMetadata(
                id="anthropic/claude-3.5-sonnet",
                provider_id="openrouter",
                display_name="Claude 3.5 Sonnet",
                context_window=200000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="deepseek/deepseek-chat",
                provider_id="openrouter",
                display_name="DeepSeek V3",
                context_window=64000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=False,
            ),
        ],
    ),
}


def get_all_providers_metadata() -> list[ProviderMetadata]:
    return list(PROVIDERS_REGISTRY.values())


def get_provider_metadata(provider_id: str) -> ProviderMetadata | None:
    return PROVIDERS_REGISTRY.get(provider_id)
