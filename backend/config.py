"""
Application configuration.
Reads from environment variables populated by python-dotenv in app.py.
All values are read at class-definition time — load_dotenv() must run first.
"""
import os


class Config:
    # Flask
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    DEBUG: bool = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    # AI provider selection
    AI_PROVIDER: str = os.environ.get('AI_PROVIDER', 'gemini').lower()

    # Google Gemini
    GEMINI_API_KEY: str = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = os.environ.get('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL: str = os.environ.get('ANTHROPIC_MODEL', 'claude-opus-4-5-20250929')

    # Flask server
    HOST: str = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORT: int = int(os.environ.get('FLASK_PORT', '5001'))
