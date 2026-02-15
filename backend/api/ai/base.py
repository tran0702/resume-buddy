"""
Abstract base class that all AI providers must implement.
This is the interface contract — adding a new provider means implementing AIProvider.
"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Common interface for all LLM providers.

    Every method that generates structured output MUST return a plain Python dict
    that is JSON-serializable and conforms to the schemas in schemas.py.
    """

    @abstractmethod
    def extract_profile(self, resume_text: str) -> dict:
        """
        Given raw resume text, extract and return a MasterProfile-shaped dict.

        Args:
            resume_text: Full plain text of the resume.

        Returns:
            A dict conforming to the MasterProfile schema.

        Raises:
            AIProviderError: If the AI call fails or returns malformed JSON.
        """
        ...

    @abstractmethod
    def analyze_job(self, job_description_text: str) -> dict:
        """
        Given a job description, extract and return a JobAnalysis-shaped dict.

        Args:
            job_description_text: Full text of the job posting.

        Returns:
            A dict conforming to the JobAnalysis schema.

        Raises:
            AIProviderError: If the AI call fails or returns malformed JSON.
        """
        ...

    @abstractmethod
    def tailor_bullets(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        """
        Rewrite the resume's experience bullets to match the job's ATS keywords.

        Args:
            profile_dict: MasterProfile-shaped dict.
            job_analysis_dict: JobAnalysis-shaped dict.

        Returns:
            A dict with keys:
              "tailored_experience": list of { company, title, tailored_bullets }
              "tailoring_notes": list of strings describing what was changed
              "ats_match_score": int 0–100

        Raises:
            AIProviderError: If the AI call fails.
        """
        ...

    @abstractmethod
    def generate_cover_letter_text(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        """
        Generate professional cover letter text for the given profile and job.

        Args:
            profile_dict: MasterProfile-shaped dict.
            job_analysis_dict: JobAnalysis-shaped dict.

        Returns:
            A dict with keys:
              "cover_letter_text": str — full letter text, paragraphs separated by \\n\\n
              "subject_line": str

        Raises:
            AIProviderError: If the AI call fails.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier, e.g. 'gemini' or 'claude'."""
        ...


class AIProviderError(Exception):
    """Raised when an AI provider call fails in a recoverable way."""

    def __init__(
        self,
        message: str,
        provider: str,
        original_error: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
