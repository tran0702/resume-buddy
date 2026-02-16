"""
Integration tests for /generate-resume, /generate-cover-letter,
/generate-interview-prep, and /health.
All AI calls are mocked — no network required.
"""
import base64
import pytest

from .conftest import MINIMAL_PROFILE, MINIMAL_JOB, RESUME_OPTIONS


# ===== Health ==================================================================

class TestHealthRoute:

    def test_health_returns_ok(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['status'] == 'ok'
        assert 'version' in body


# ===== /generate-resume ========================================================

class TestGenerateResumeRoute:

    def test_returns_200_with_docx(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'docx_base64' in body
        assert 'filename' in body
        assert 'preview_text' in body
        assert 'ats_match_score' in body
        assert 'tailoring_notes' in body

    def test_docx_base64_is_decodable(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 200
        decoded = base64.b64decode(resp.get_json()['docx_base64'])
        assert len(decoded) > 0

    def test_filename_contains_job_title(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert 'Software Engineer' in resp.get_json()['filename']
        assert resp.get_json()['filename'].endswith('.docx')

    def test_filename_sanitized_of_illegal_chars(self, client, mock_ai_provider):
        bad_title_job = {**MINIMAL_JOB, 'job_title': 'Dev: <Backend> & APIs / "Staff"'}
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': bad_title_job,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 200
        filename = resp.get_json()['filename']
        for char in r'\/*?:"<>|':
            assert char not in filename, f"Illegal char '{char}' found in filename: {filename}"

    def test_modern_template_returns_200(self, client, mock_ai_provider):
        options = {**RESUME_OPTIONS, 'template': 'modern'}
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': options
        })
        assert resp.status_code == 200

    def test_harvard_template_is_default(self, client, mock_ai_provider):
        """Options with no 'template' key → defaults to Harvard, returns 200."""
        options = {k: v for k, v in RESUME_OPTIONS.items() if k != 'template'}
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': options
        })
        assert resp.status_code == 200

    def test_missing_profile_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 400

    def test_missing_job_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 400

    def test_profile_without_name_returns_422(self, client, mock_ai_provider):
        profile = {**MINIMAL_PROFILE, 'contact': {'email': 'jane@example.com'}}
        resp = client.post('/generate-resume', json={
            'profile': profile,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 422

    def test_no_body_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-resume',
                           data='not json',
                           content_type='text/plain')
        assert resp.status_code == 400

    def test_ai_error_returns_502(self, client, mock_ai_provider):
        from backend.api.ai.base import AIProviderError
        mock_ai_provider.tailor_bullets.side_effect = AIProviderError(
            'API quota exceeded', provider='mock'
        )
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        assert resp.status_code == 502
        assert 'error' in resp.get_json()

    def test_ats_score_in_response(self, client, mock_ai_provider):
        resp = client.post('/generate-resume', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': RESUME_OPTIONS
        })
        score = resp.get_json()['ats_match_score']
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


# ===== /generate-cover-letter ==================================================

class TestGenerateCoverLetterRoute:

    def test_returns_200_with_docx(self, client, mock_ai_provider):
        resp = client.post('/generate-cover-letter', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': {'include_header': True, 'include_footer': False}
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'docx_base64' in body
        assert 'filename' in body
        assert 'preview_text' in body

    def test_docx_base64_is_decodable(self, client, mock_ai_provider):
        resp = client.post('/generate-cover-letter', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': {'include_header': True, 'include_footer': False}
        })
        decoded = base64.b64decode(resp.get_json()['docx_base64'])
        assert len(decoded) > 0

    def test_missing_profile_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-cover-letter', json={
            'job_analysis': MINIMAL_JOB,
            'options': {}
        })
        assert resp.status_code == 400

    def test_missing_job_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-cover-letter', json={
            'profile': MINIMAL_PROFILE,
            'options': {}
        })
        assert resp.status_code == 400

    def test_ai_error_returns_502(self, client, mock_ai_provider):
        from backend.api.ai.base import AIProviderError
        mock_ai_provider.generate_cover_letter_text.side_effect = AIProviderError(
            'Rate limited', provider='mock'
        )
        resp = client.post('/generate-cover-letter', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB,
            'options': {}
        })
        assert resp.status_code == 502


# ===== /generate-interview-prep ================================================

class TestGenerateInterviewPrepRoute:

    def test_returns_200_with_all_sections(self, client, mock_ai_provider):
        resp = client.post('/generate-interview-prep', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'behavioural_questions' in body
        assert 'technical_questions' in body
        assert 'questions_to_ask' in body

    def test_sections_are_lists(self, client, mock_ai_provider):
        resp = client.post('/generate-interview-prep', json={
            'profile': MINIMAL_PROFILE,
            'job_analysis': MINIMAL_JOB
        })
        body = resp.get_json()
        assert isinstance(body['behavioural_questions'], list)
        assert isinstance(body['technical_questions'], list)
        assert isinstance(body['questions_to_ask'], list)

    def test_missing_profile_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-interview-prep', json={
            'job_analysis': MINIMAL_JOB
        })
        assert resp.status_code == 400

    def test_missing_job_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-interview-prep', json={
            'profile': MINIMAL_PROFILE
        })
        assert resp.status_code == 400

    def test_no_body_returns_400(self, client, mock_ai_provider):
        resp = client.post('/generate-interview-prep',
                           data='{}',
                           content_type='text/plain')
        assert resp.status_code == 400
