"""
AI Orchestrator — selects and returns the correct AIProvider instance.
Selection is driven by the AI_PROVIDER environment variable (default: 'gemini').
Call get_ai_provider() from route handlers to get the active provider.
"""
from flask import current_app

from backend.api.ai.base import AIProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function — returns an initialized AIProvider for the configured provider.

    Raises:
        ValueError: If AI_PROVIDER specifies an unknown provider name.
    """
    provider_name: str = current_app.config.get('AI_PROVIDER', 'gemini').lower()

    if provider_name == 'gemini':
        from backend.api.ai.gemini import GeminiProvider
        return GeminiProvider(
            api_key=current_app.config['GEMINI_API_KEY'],
            model=current_app.config['GEMINI_MODEL']
        )

    if provider_name == 'claude':
        from backend.api.ai.claude import ClaudeProvider
        return ClaudeProvider(
            api_key=current_app.config['ANTHROPIC_API_KEY'],
            model=current_app.config['ANTHROPIC_MODEL']
        )

    raise ValueError(
        f"Unknown AI_PROVIDER: '{provider_name}'. "
        f"Valid values: 'gemini', 'claude'"
    )
