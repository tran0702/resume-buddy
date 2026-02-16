"""
Flask application factory.
Call create_app() to get a configured Flask application instance.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.config import Config


def create_app(config_class: type = Config) -> Flask:
    """
    Factory function — creates and configures the Flask app.

    Using a factory (rather than module-level `app = Flask(__name__)`) means:
    - Config can be swapped per environment (dev/test/prod)
    - No circular imports — blueprints are imported inside this function
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS — allow requests from Electron renderer.
    # In dev the renderer runs on localhost:5173 (Vite dev server).
    # In production, Electron's Chromium sends Origin: null for file:// requests.
    # flask-cors cannot match 'null' as a string pattern, so we use an
    # after_request hook to inject the correct header for all localhost/null origins.
    # Flask is bound to 127.0.0.1 only, so no external requests are possible.
    CORS(app, origins=['http://localhost:5173', 'http://localhost:4173'])

    @app.after_request
    def _add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        # Allow: dev Vite server, Electron production (null origin), and empty origin
        if origin in ('null', '') or origin.startswith('http://localhost'):
            response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    @app.route('/<path:path>', methods=['OPTIONS'])
    def _options_handler(path):  # noqa: ARG001
        """Handle CORS preflight requests for all routes."""
        return '', 200

    # Register route blueprints
    from backend.api.documents import documents_bp
    from backend.api.jobs import jobs_bp
    from backend.api.profiles import profiles_bp
    from backend.api.generation import generation_bp

    app.register_blueprint(documents_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(generation_bp)

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'version': '0.1.0'})

    return app
