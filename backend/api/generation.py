"""
Blueprint: /generate-resume and /generate-cover-letter
Orchestrates AI bullet tailoring + DOCX template building.
Returns base64-encoded DOCX + plain-text preview + metadata.
"""
import base64
import logging
import re

from flask import Blueprint, request, jsonify

from backend.api.ai.orchestrator import get_ai_provider
from backend.api.ai.base import AIProviderError

logger = logging.getLogger(__name__)
generation_bp = Blueprint('generation', __name__)


def _safe_filename(text: str) -> str:
    """Sanitize a string for use in a filename."""
    safe = re.sub(r'[\\/*?:"<>|]', '', text)
    return safe.strip()[:80]  # cap length


@generation_bp.post('/generate-resume')
def generate_resume():
    """
    POST /generate-resume
    Body: {
        "profile": MasterProfile,
        "job_analysis": JobAnalysis,
        "options": {
            "include_skills": bool,
            "include_projects": bool,
            "include_certifications": bool,
            "include_volunteer": bool,
            "max_pages": int  (1 or 2)
        }
    }
    Returns: {
        "docx_base64": str,
        "filename": str,
        "preview_text": str,
        "tailoring_notes": [str, ...],
        "ats_match_score": int
    }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({'error': 'Request body must be JSON.'}), 400

    profile = body.get('profile')
    job_analysis = body.get('job_analysis')
    options = body.get('options', {})

    if not profile or not isinstance(profile, dict):
        return jsonify({'error': '"profile" field is required and must be a JSON object.'}), 400
    if not job_analysis or not isinstance(job_analysis, dict):
        return jsonify({'error': '"job_analysis" field is required and must be a JSON object.'}), 400
    if not profile.get('contact', {}).get('name'):
        return jsonify({'error': 'Profile must include contact.name.'}), 422

    try:
        provider = get_ai_provider()
        logger.info(f'[generate-resume] Tailoring bullets via {provider.provider_name}...')
        tailored = provider.tailor_bullets(profile, job_analysis)

        from backend.api.templates import resume_builder
        logger.info('[generate-resume] Building DOCX...')
        docx_buf, preview_text = resume_builder.build(profile, tailored, options)

        docx_bytes = docx_buf.read()
        docx_base64 = base64.b64encode(docx_bytes).decode('utf-8')

        job_title = _safe_filename(job_analysis.get('job_title', 'Position'))
        filename = f'{job_title} - Resume - Applied.docx'

        logger.info(f'[generate-resume] Done. ATS score: {tailored.get("ats_match_score")}')
        return jsonify({
            'docx_base64': docx_base64,
            'filename': filename,
            'preview_text': preview_text,
            'tailoring_notes': tailored.get('tailoring_notes', []),
            'ats_match_score': tailored.get('ats_match_score', 0)
        }), 200

    except AIProviderError as e:
        logger.error(f'[generate-resume] AI error ({e.provider}): {e}')
        return jsonify({'error': str(e), 'detail': f'Provider: {e.provider}'}), 502
    except ValueError as e:
        logger.error(f'[generate-resume] Config error: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.exception(f'[generate-resume] Unexpected error: {e}')
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@generation_bp.post('/generate-cover-letter')
def generate_cover_letter():
    """
    POST /generate-cover-letter
    Body: {
        "profile": MasterProfile,
        "job_analysis": JobAnalysis,
        "options": {
            "include_header": bool,
            "include_footer": bool
        }
    }
    Returns: {
        "docx_base64": str,
        "filename": str,
        "preview_text": str
    }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({'error': 'Request body must be JSON.'}), 400

    profile = body.get('profile')
    job_analysis = body.get('job_analysis')
    options = body.get('options', {})

    if not profile or not isinstance(profile, dict):
        return jsonify({'error': '"profile" field is required and must be a JSON object.'}), 400
    if not job_analysis or not isinstance(job_analysis, dict):
        return jsonify({'error': '"job_analysis" field is required and must be a JSON object.'}), 400

    try:
        provider = get_ai_provider()
        logger.info(f'[generate-cover-letter] Generating text via {provider.provider_name}...')
        cl_result = provider.generate_cover_letter_text(profile, job_analysis)

        from backend.api.templates import cover_letter_builder
        logger.info('[generate-cover-letter] Building DOCX...')
        docx_buf, preview_text = cover_letter_builder.build(cl_result, profile, job_analysis, options)

        docx_bytes = docx_buf.read()
        docx_base64 = base64.b64encode(docx_bytes).decode('utf-8')

        job_title = _safe_filename(job_analysis.get('job_title', 'Position'))
        filename = f'{job_title} - Cover Letter - Applied.docx'

        logger.info('[generate-cover-letter] Done.')
        return jsonify({
            'docx_base64': docx_base64,
            'filename': filename,
            'preview_text': preview_text
        }), 200

    except AIProviderError as e:
        logger.error(f'[generate-cover-letter] AI error ({e.provider}): {e}')
        return jsonify({'error': str(e), 'detail': f'Provider: {e.provider}'}), 502
    except ValueError as e:
        logger.error(f'[generate-cover-letter] Config error: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.exception(f'[generate-cover-letter] Unexpected error: {e}')
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
