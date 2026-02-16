"""
Shared pytest fixtures for Resume Buddy backend tests.
All AI providers are patched at the orchestrator level — no API keys needed.
"""
import io
import os
import pytest
from unittest.mock import MagicMock, patch

# ---- Flask test client -------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """
    Create a Flask app configured for testing.
    Sets dummy env vars so Config's class-level reads don't raise.
    """
    os.environ.setdefault('GEMINI_API_KEY', 'test-key-gemini')
    os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-anthropic')
    os.environ.setdefault('AI_PROVIDER', 'gemini')
    os.environ.setdefault('FLASK_DEBUG', 'false')

    from backend.api import create_app
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture()
def client(app):
    """Flask test client — fresh for each test."""
    return app.test_client()


# ---- Fixture file helpers ----------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def fixture_bytes(filename: str) -> bytes:
    """Read a fixture file as bytes."""
    with open(os.path.join(FIXTURES_DIR, filename), 'rb') as f:
        return f.read()


# ---- Minimal valid data ------------------------------------------------------

MINIMAL_PROFILE = {
    'contact': {'name': 'Jane Doe', 'email': 'jane@example.com'},
    'work_experience': [],
    'education': [],
    'skills': ['Python'],
    'summary': None,
    'certifications': [],
    'projects': [],
    'languages': [],
    'volunteer': []
}

MINIMAL_JOB = {
    'job_title': 'Software Engineer',
    'required_skills': ['Python'],
    'preferred_skills': [],
    'key_responsibilities': ['Build software'],
    'keywords_for_ats': ['Python'],
    'raw_requirements': [],
    'company_name': 'Acme Corp',
}

RESUME_OPTIONS = {
    'include_skills': True,
    'include_projects': False,
    'include_certifications': True,
    'include_volunteer': False,
    'max_pages': 1,
    'template': 'harvard'
}


# ---- Mock AI provider --------------------------------------------------------

@pytest.fixture()
def mock_ai_provider():
    """
    Patches get_ai_provider() to return a MagicMock.
    Avoids any network calls. Tests that need AI behavior import this fixture.
    """
    mock = MagicMock()
    mock.provider_name = 'mock'
    mock.extract_profile.return_value = MINIMAL_PROFILE
    mock.analyze_job.return_value = MINIMAL_JOB
    mock.tailor_bullets.return_value = {
        'tailored_experience': [],
        'tailoring_notes': ['Added Python keyword'],
        'ats_match_score': 80
    }
    mock.generate_cover_letter_text.return_value = {
        'subject_line': 'Application for Software Engineer',
        'cover_letter_text': (
            'Dear Hiring Manager,\n\n'
            'I am excited to apply for the Software Engineer role.\n\n'
            'I bring strong Python skills.\n\n'
            'Sincerely,\nJane Doe'
        )
    }
    mock.generate_interview_prep.return_value = {
        'behavioural_questions': [
            {'question': 'Tell me about yourself.', 'suggested_answer': 'I am Jane.'}
        ],
        'technical_questions': [
            {'question': 'What is Python?', 'suggested_answer': 'A programming language.'}
        ],
        'questions_to_ask': ['What does success look like here?']
    }

    # Patch at the point of use in each blueprint module
    with patch('backend.api.generation.get_ai_provider', return_value=mock), \
         patch('backend.api.profiles.get_ai_provider', return_value=mock), \
         patch('backend.api.jobs.get_ai_provider', return_value=mock):
        yield mock
