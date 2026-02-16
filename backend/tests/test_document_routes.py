"""
Integration tests for POST /parse-document.
Uses the Flask test client with real multipart file uploads.
No AI calls involved — pure document parsing.
"""
import io
import pytest

from .conftest import fixture_bytes


def upload(client, file_bytes: bytes, filename: str, mime: str = 'application/octet-stream'):
    """Helper: POST a file to /parse-document as multipart/form-data."""
    data = {'file': (io.BytesIO(file_bytes), filename, mime)}
    return client.post('/parse-document', data=data, content_type='multipart/form-data')


# ===== Happy path ==============================================================

class TestParseDocumentHappyPath:

    def test_txt_returns_200_with_text(self, client):
        resp = upload(client, b'Jane Doe\nEngineer\njane@example.com', 'resume.txt')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['text'] == 'Jane Doe\nEngineer\njane@example.com'
        assert body['filename'] == 'resume.txt'

    def test_pdf_returns_200(self, client):
        pdf_bytes = fixture_bytes('sample_resume.pdf')
        resp = upload(client, pdf_bytes, 'resume.pdf', 'application/pdf')
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'text' in body
        assert len(body['text']) > 0

    def test_docx_returns_200(self, client):
        docx_bytes = fixture_bytes('sample_resume.docx')
        resp = upload(client, docx_bytes, 'resume.docx',
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'text' in body
        assert len(body['text']) > 0

    def test_response_includes_filename(self, client):
        resp = upload(client, b'Jane Doe', 'my_resume.txt')
        assert resp.get_json()['filename'] == 'my_resume.txt'

    def test_pdf_text_contains_jane_doe(self, client):
        pdf_bytes = fixture_bytes('sample_resume.pdf')
        resp = upload(client, pdf_bytes, 'resume.pdf')
        assert 'Jane Doe' in resp.get_json()['text']

    def test_docx_text_contains_jane_doe(self, client):
        docx_bytes = fixture_bytes('sample_resume.docx')
        resp = upload(client, docx_bytes, 'resume.docx')
        assert 'Jane Doe' in resp.get_json()['text']

    def test_utf8_txt_preserves_accents(self, client):
        raw = 'résumé Üniversität'.encode('utf-8')
        resp = upload(client, raw, 'resume.txt')
        assert resp.status_code == 200
        assert 'résumé' in resp.get_json()['text']


# ===== Error cases ============================================================

class TestParseDocumentErrors:

    def test_no_file_field_returns_400(self, client):
        resp = client.post('/parse-document', data={}, content_type='multipart/form-data')
        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_empty_filename_returns_400(self, client):
        data = {'file': (io.BytesIO(b'content'), '', 'text/plain')}
        resp = client.post('/parse-document', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_empty_file_content_returns_400(self, client):
        resp = upload(client, b'', 'resume.txt')
        assert resp.status_code == 400

    def test_unsupported_extension_returns_415(self, client):
        resp = upload(client, b'<html>not a resume</html>', 'resume.html')
        assert resp.status_code == 415
        assert 'Unsupported file type' in resp.get_json()['error']

    def test_no_extension_returns_415(self, client):
        resp = upload(client, b'some content', 'resume_no_extension')
        assert resp.status_code == 415

    def test_all_whitespace_txt_returns_422(self, client):
        resp = upload(client, b'   \n\t\n   ', 'resume.txt')
        assert resp.status_code == 422
        assert 'No text could be extracted' in resp.get_json()['error']

    def test_corrupt_pdf_returns_500(self, client):
        resp = upload(client, b'%PDF-1.4 CORRUPT DATA', 'bad.pdf', 'application/pdf')
        assert resp.status_code == 500
        assert 'error' in resp.get_json()

    def test_corrupt_docx_returns_500(self, client):
        resp = upload(client, b'\x00\x01\x02\x03 not valid', 'bad.docx')
        assert resp.status_code == 500

    def test_extension_case_insensitive(self, client):
        """Extensions like .TXT and .PDF should be handled (rsplit lowercases)."""
        resp = upload(client, b'Jane Doe\nEngineer', 'resume.TXT')
        assert resp.status_code == 200

    def test_multi_dot_filename(self, client):
        """my.resume.final.txt — rsplit('.', 1) takes the last segment."""
        resp = upload(client, b'Jane Doe\nEngineer', 'my.resume.final.txt')
        assert resp.status_code == 200

    def test_json_body_instead_of_multipart_returns_400(self, client):
        """Posting JSON instead of multipart/form-data should return 400."""
        resp = client.post('/parse-document',
                           data='{"text": "resume"}',
                           content_type='application/json')
        assert resp.status_code == 400
