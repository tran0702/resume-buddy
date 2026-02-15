"""
Blueprint: /parse-document
Accepts a file upload (PDF, DOCX, TXT) and returns the extracted plain text.
No AI call — this is pure document parsing.
"""
import io
import logging

from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
documents_bp = Blueprint('documents', __name__)


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfminer.six."""
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams

    output = io.StringIO()
    extract_text_to_fp(
        io.BytesIO(file_bytes),
        output,
        laparams=LAParams(),
        output_type='text',
        codec='utf-8'
    )
    return output.getvalue()


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return '\n'.join(paragraphs)


def _extract_txt(file_bytes: bytes) -> str:
    """Decode plain text; UTF-8 with latin-1 fallback."""
    try:
        return file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return file_bytes.decode('latin-1')


@documents_bp.post('/parse-document')
def parse_document():
    """
    POST /parse-document
    Accepts: multipart/form-data with a 'file' field.
    Returns: { "text": "...", "filename": "..." }
    """
    if 'file' not in request.files:
        return jsonify({
            'error': 'No file provided. Send multipart/form-data with a "file" field.'
        }), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Uploaded file has no name.'}), 400

    filename: str = file.filename
    file_bytes: bytes = file.read()

    if not file_bytes:
        return jsonify({'error': 'Uploaded file is empty.'}), 400

    try:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if ext == 'pdf':
            text = _extract_pdf(file_bytes)
        elif ext == 'docx':
            text = _extract_docx(file_bytes)
        elif ext == 'txt':
            text = _extract_txt(file_bytes)
        else:
            return jsonify({
                'error': f'Unsupported file type: .{ext}. Supported: pdf, docx, txt.'
            }), 415

        text = text.strip()
        if not text:
            return jsonify({'error': 'No text could be extracted from the file.'}), 422

        logger.info(f'[parse-document] Extracted {len(text)} chars from {filename}')
        return jsonify({'text': text, 'filename': filename}), 200

    except Exception as e:
        logger.exception(f'[parse-document] Failed to parse {filename}: {e}')
        return jsonify({'error': f'Failed to parse document: {str(e)}'}), 500
