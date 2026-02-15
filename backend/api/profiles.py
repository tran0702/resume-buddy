"""
Blueprint: /extract-profile
Accepts raw resume text, returns structured MasterProfile JSON via AI.
"""
import logging

from flask import Blueprint, request, jsonify

from backend.api.ai.orchestrator import get_ai_provider
from backend.api.ai.base import AIProviderError

logger = logging.getLogger(__name__)
profiles_bp = Blueprint('profiles', __name__)


@profiles_bp.post('/extract-profile')
def extract_profile():
    """
    POST /extract-profile
    Body: { "text": "raw resume text" }
    Returns: MasterProfile JSON
    """
    body = request.get_json(silent=True)
    if not body or 'text' not in body:
        return jsonify({'error': 'Request body must be JSON with a "text" field.'}), 400

    resume_text: str = str(body['text']).strip()
    if not resume_text:
        return jsonify({'error': '"text" field cannot be empty.'}), 400
    if len(resume_text) < 100:
        return jsonify({'error': 'Resume text is too short (minimum 100 characters).'}), 422

    try:
        provider = get_ai_provider()
        result = provider.extract_profile(resume_text)
        logger.info(f'[extract-profile] Success via {provider.provider_name}')
        return jsonify(result), 200

    except AIProviderError as e:
        logger.error(f'[extract-profile] AI error ({e.provider}): {e}')
        return jsonify({'error': str(e), 'detail': f'Provider: {e.provider}'}), 502

    except ValueError as e:
        logger.error(f'[extract-profile] Config error: {e}')
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.exception(f'[extract-profile] Unexpected error: {e}')
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
