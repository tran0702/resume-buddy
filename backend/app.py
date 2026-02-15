"""
Flask entry point for Resume Buddy backend.

Run from the project root as:
    python -m backend.app

This ensures 'backend' is resolved as a package from the project root,
so all `from backend.xxx import yyy` imports work correctly.
"""
import os
from dotenv import load_dotenv

# Load .env BEFORE importing application modules.
# Config reads from os.environ at class-definition time,
# so .env must be populated first.
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=_env_path)

from backend.api import create_app  # noqa: E402

application = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    print(f'[Flask] Starting on http://127.0.0.1:{port}  debug={debug}')
    application.run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        use_reloader=False  # Disable reloader to prevent double-spawn on Windows
    )
