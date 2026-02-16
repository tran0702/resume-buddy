"""
Anthropic Claude AI provider — STUB implementation.
The API key is TBD. This stub allows the codebase to import without a valid key
and raises a clear AIProviderError if any method is actually called.

To activate:
  1. Obtain an Anthropic API key
  2. Set ANTHROPIC_API_KEY in .env
  3. Set AI_PROVIDER=claude in .env
  4. Replace the stub methods below with the commented-out implementation template.
"""
import logging

from backend.api.ai.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Stub for Anthropic Claude. Raises AIProviderError on any AI call."""

    def __init__(self, api_key: str, model: str = 'claude-opus-4-5-20250929') -> None:
        self._model = model
        self._api_key = api_key
        logger.warning(
            '[ClaudeProvider] Initialized in STUB mode. '
            'Set AI_PROVIDER=gemini in .env to use the active provider.'
        )

    @property
    def provider_name(self) -> str:
        return 'claude'

    def extract_profile(self, resume_text: str) -> dict:
        raise AIProviderError(
            'Claude provider is not yet implemented. Set AI_PROVIDER=gemini in .env.',
            provider='claude'
        )

    def analyze_job(self, job_description_text: str) -> dict:
        raise AIProviderError(
            'Claude provider is not yet implemented. Set AI_PROVIDER=gemini in .env.',
            provider='claude'
        )

    def tailor_bullets(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        raise AIProviderError(
            'Claude provider is not yet implemented. Set AI_PROVIDER=gemini in .env.',
            provider='claude'
        )

    def generate_cover_letter_text(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        raise AIProviderError(
            'Claude provider is not yet implemented. Set AI_PROVIDER=gemini in .env.',
            provider='claude'
        )

    def generate_interview_prep(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        raise AIProviderError(
            'Claude provider is not yet implemented. Set AI_PROVIDER=gemini in .env.',
            provider='claude'
        )

    # ---- Implementation template (uncomment when API key is available) ----
    # def _generate_json(self, system_prompt: str, user_prompt: str) -> dict:
    #     import anthropic, json
    #     client = anthropic.Anthropic(api_key=self._api_key)
    #     message = client.messages.create(
    #         model=self._model,
    #         max_tokens=8192,
    #         system=system_prompt,
    #         messages=[{'role': 'user', 'content': user_prompt}]
    #     )
    #     return json.loads(message.content[0].text)
