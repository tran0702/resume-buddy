"""
Google Gemini AI provider implementation.
Uses the google-genai SDK (the new unified GA SDK — NOT the deprecated google-generativeai).

Key API difference:
  OLD (deprecated): import google.generativeai as genai; genai.GenerativeModel(...)
  NEW (correct):    from google import genai; genai.Client(api_key=...)
"""
import json
import logging

from google import genai
from google.genai import types as genai_types

from backend.api.ai.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


# ---- Prompt templates ------------------------------------------------
# Module-level constants. Move to prompts.py if they grow large.

_EXTRACT_PROFILE_PROMPT = """\
You are a resume parsing assistant. Extract all information from the resume text below
and return it as a single JSON object that strictly follows this schema:

{{
  "contact": {{
    "name": "string",
    "email": "string",
    "phone": "string or null",
    "location": "string or null",
    "linkedin": "string or null",
    "github": "string or null",
    "portfolio": "string or null"
  }},
  "summary": "string or null",
  "work_experience": [
    {{
      "company": "string",
      "title": "string",
      "start_date": "YYYY-MM string",
      "end_date": "YYYY-MM string or null (null = present)",
      "location": "string or null",
      "bullets": ["string", ...]
    }}
  ],
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "graduation_date": "YYYY-MM string",
      "gpa": "number or null",
      "honors": ["string", ...]
    }}
  ],
  "skills": ["string", ...],
  "certifications": ["string", ...],
  "projects": [
    {{
      "name": "string",
      "description": "string",
      "technologies": ["string", ...],
      "url": "string or null"
    }}
  ],
  "languages": ["string", ...],
  "volunteer": ["string", ...]
}}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- Use null for optional fields with no data; use [] for optional arrays with no data.
- Do not invent information not present in the resume.

Resume text:
---
{resume_text}
---"""

_ANALYZE_JOB_PROMPT = """\
You are a job description analyst. Extract all information from the job posting below
and return it as a single JSON object that strictly follows this schema:

{{
  "job_title": "string",
  "company_name": "string or null",
  "required_skills": ["string", ...],
  "preferred_skills": ["string", ...],
  "key_responsibilities": ["string", ...],
  "years_experience_required": "integer or null",
  "education_required": "string or null",
  "industry": "string or null",
  "seniority_level": "entry | mid | senior | lead | executive | null",
  "keywords_for_ats": ["string", ...],
  "company_values": ["string", ...],
  "raw_requirements": [
    {{
      "skill": "string",
      "importance": "required | preferred | nice-to-have"
    }}
  ]
}}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- keywords_for_ats: curated list of 10–20 high-value ATS keywords from the posting.
- raw_requirements: enumerate every specific skill or tool mentioned.
- Use null for optional fields with no data; use [] for optional arrays.

Job description:
---
{job_description_text}
---"""


class GeminiProvider(AIProvider):

    def __init__(self, api_key: str, model: str = 'gemini-1.5-flash') -> None:
        if not api_key:
            raise AIProviderError(
                'GEMINI_API_KEY is not set. Add it to your .env file.',
                provider='gemini'
            )
        self._model = model
        self._client = genai.Client(api_key=api_key)
        logger.info(f'[GeminiProvider] Initialized with model={model}')

    @property
    def provider_name(self) -> str:
        return 'gemini'

    def _generate_json(self, prompt: str) -> dict:
        """
        Send a prompt to Gemini with JSON mode enabled and return the parsed dict.
        response_mime_type='application/json' guarantees the model emits valid JSON.
        Note: this mode cannot be combined with function-calling tools — acceptable here.
        """
        raw_text = ''
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.1,          # low temp for deterministic structured output
                    max_output_tokens=8192,
                )
            )
            raw_text = response.text or ''
            if not raw_text:
                raise AIProviderError('Gemini returned an empty response.', provider='gemini')
            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            logger.error(f'[GeminiProvider] JSON decode error: {e}')
            logger.error(f'[GeminiProvider] Raw response (first 500 chars): {raw_text[:500]}')
            raise AIProviderError(
                f'Gemini returned malformed JSON: {e}',
                provider='gemini',
                original_error=e
            ) from e

        except AIProviderError:
            raise

        except Exception as e:
            logger.error(f'[GeminiProvider] API error: {e}')
            raise AIProviderError(
                f'Gemini API call failed: {e}',
                provider='gemini',
                original_error=e
            ) from e

    def extract_profile(self, resume_text: str) -> dict:
        logger.info('[GeminiProvider] Extracting profile...')
        prompt = _EXTRACT_PROFILE_PROMPT.format(resume_text=resume_text)
        return self._generate_json(prompt)

    def analyze_job(self, job_description_text: str) -> dict:
        logger.info('[GeminiProvider] Analyzing job description...')
        prompt = _ANALYZE_JOB_PROMPT.format(job_description_text=job_description_text)
        return self._generate_json(prompt)
