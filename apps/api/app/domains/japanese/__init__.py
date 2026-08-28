"""Japanese language facade — centralized linguistic resources."""

from app.domains.japanese.provider import JapaneseLanguageResourceProvider, SudachiLanguageProvider, get_language_provider

__all__ = ["JapaneseLanguageResourceProvider", "SudachiLanguageProvider", "get_language_provider"]
