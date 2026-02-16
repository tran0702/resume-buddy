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


_TAILOR_BULLETS_PROMPT = """\
You are a professional resume writer specializing in ATS optimization.
Given a candidate's profile and a job analysis, rewrite the experience bullets
to highlight achievements relevant to the job. Use exact keywords from keywords_for_ats
where they fit naturally. Keep bullets concise (under 120 chars), start with action verbs,
and quantify impact where the original data supports it.

Master Profile:
{profile_json}

Job Analysis:
{job_analysis_json}

Return a single JSON object following this schema exactly:
{{
  "tailored_experience": [
    {{
      "company": "string — must match the profile exactly",
      "title": "string — must match the profile exactly",
      "tailored_bullets": ["string", ...]
    }}
  ],
  "tailoring_notes": [
    "string — one sentence describing a key change made, e.g. 'Emphasized Python and REST APIs to match required_skills'"
  ],
  "ats_match_score": 75
}}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- tailored_experience must include an entry for EVERY position in the profile.
- ats_match_score: integer 0–100 estimating keyword alignment after tailoring.
- tailoring_notes: 2–5 concise notes about what was changed and why.
- Do not invent experience or skills not present in the profile."""

_COVER_LETTER_PROMPT = """\
You are a professional career coach writing a cover letter.
Write a concise, compelling cover letter (4 paragraphs, max 400 words total)
for the candidate applying to this job.

Master Profile:
{profile_json}

Job Analysis:
{job_analysis_json}

Return a single JSON object following this schema exactly:
{{
  "subject_line": "Application for [Job Title] — [Candidate Name]",
  "cover_letter_text": "Full letter text. Use \\n\\n to separate paragraphs.\\n\\nParagraph 1: Express enthusiasm for the specific role and company. Reference the company name if available.\\n\\nParagraph 2: Connect 2–3 of the candidate's strongest experiences to the job's key requirements.\\n\\nParagraph 3: Highlight a specific achievement or skill from the profile that directly addresses a required skill.\\n\\nParagraph 4: Strong closing — request an interview, express eagerness, provide contact info."
}}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- cover_letter_text must be plain text only — no markdown, no asterisks, no headers.
- Paragraphs must be separated by \\n\\n.
- Use the candidate's actual name, experiences, and skills from the profile.
- Do not begin with "I am writing to" — use an engaging opening instead."""


_INTERVIEW_PREP_PROMPT = """\
You are a professional interview coach preparing a candidate for a job interview.
Generate targeted interview questions and suggested answers based on the candidate's
profile and the job they are applying for.

Master Profile:
{profile_json}

Job Analysis:
{job_analysis_json}

Return a single JSON object following this schema exactly:
{{
  "behavioural_questions": [
    {{
      "question": "string — STAR-format behavioural question relevant to this role",
      "suggested_answer": "string — 3-5 sentence STAR answer using the candidate's actual experience"
    }}
  ],
  "technical_questions": [
    {{
      "question": "string — technical question testing required_skills for this role",
      "suggested_answer": "string — concise correct answer, 2-4 sentences"
    }}
  ],
  "questions_to_ask": [
    "string — thoughtful question the candidate should ask the interviewer"
  ]
}}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- behavioural_questions: exactly 5 questions using the candidate's real work history.
- technical_questions: exactly 5 questions drawn from required_skills and key_responsibilities.
- questions_to_ask: exactly 4 questions that show genuine interest in the role/company.
- Do not invent experience or skills not present in the profile.
- suggested_answer must reference specific companies, technologies, or achievements from the profile."""


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

    def tailor_bullets(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        logger.info('[GeminiProvider] Tailoring resume bullets...')
        import json as _json
        prompt = _TAILOR_BULLETS_PROMPT.format(
            profile_json=_json.dumps(profile_dict, indent=2),
            job_analysis_json=_json.dumps(job_analysis_dict, indent=2)
        )
        return self._generate_json(prompt)

    def generate_cover_letter_text(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        logger.info('[GeminiProvider] Generating cover letter text...')
        import json as _json
        prompt = _COVER_LETTER_PROMPT.format(
            profile_json=_json.dumps(profile_dict, indent=2),
            job_analysis_json=_json.dumps(job_analysis_dict, indent=2)
        )
        return self._generate_json(prompt)

    def generate_interview_prep(self, profile_dict: dict, job_analysis_dict: dict) -> dict:
        logger.info('[GeminiProvider] Generating interview prep...')
        import json as _json
        prompt = _INTERVIEW_PREP_PROMPT.format(
            profile_json=_json.dumps(profile_dict, indent=2),
            job_analysis_json=_json.dumps(job_analysis_dict, indent=2)
        )
        return self._generate_json(prompt)
