"""
Flask application factory.
Call create_app() to get a configured Flask application instance.
"""
from flask import Flask, jsonify
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
    # In production it loads from file:// — Electron's origin for local files.
    CORS(app, resources={
        r'/*': {
            'origins': [
                'http://localhost:5173',
                'http://localhost:4173',
                'file://*'
            ]
        }
    })

    # Register route blueprints
    from backend.api.documents import documents_bp
    from backend.api.jobs import jobs_bp
    from backend.api.profiles import profiles_bp

    app.register_blueprint(documents_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(profiles_bp)

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'version': '0.1.0'})

    return app
