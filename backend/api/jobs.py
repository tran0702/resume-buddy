"""
Blueprint: /analyze-job
Accepts job description text, returns structured JobAnalysis JSON via AI.
"""
import logging

from flask import Blueprint, request, jsonify

from backend.api.ai.orchestrator import get_ai_provider
from backend.api.ai.base import AIProviderError

logger = logging.getLogger(__name__)
jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.post('/analyze-job')
def analyze_job():
    """
    POST /analyze-job
    Body: { "text": "full job description text" }
    Returns: JobAnalysis JSON
    """
    body = request.get_json(silent=True)
    if not body or 'text' not in body:
        return jsonify({'error': 'Request body must be JSON with a "text" field.'}), 400

    job_text: str = str(body['text']).strip()
    if not job_text:
        return jsonify({'error': '"text" field cannot be empty.'}), 400
    if len(job_text) < 50:
        return jsonify({'error': 'Job description is too short (minimum 50 characters).'}), 422

    try:
        provider = get_ai_provider()
        result = provider.analyze_job(job_text)
        logger.info(f'[analyze-job] Success via {provider.provider_name}')
        return jsonify(result), 200

    except AIProviderError as e:
        logger.error(f'[analyze-job] AI error ({e.provider}): {e}')
        return jsonify({'error': str(e), 'detail': f'Provider: {e.provider}'}), 502

    except ValueError as e:
        logger.error(f'[analyze-job] Config error: {e}')
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.exception(f'[analyze-job] Unexpected error: {e}')
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
