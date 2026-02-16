"""
scripts/run_backend.py

PyInstaller entry point for the Resume Buddy Flask backend.
This script is compiled into the frozen executable (run_backend.exe).

In development, use `python -m backend.app` from the project root instead.
When frozen, sys.frozen = True and PyInstaller adds sys._MEIPASS to sys.path,
so `from backend.api import create_app` resolves correctly.

API keys are passed in as environment variables by Electron main at spawn time.
No .env file is loaded here — that is only done in development via backend/app.py.
"""
import os
import sys


def main() -> None:
    from backend.api import create_app

    port = int(os.environ.get('FLASK_PORT', '5001'))
    app = create_app()
    print(f'[Flask] Frozen backend starting on http://127.0.0.1:{port}', flush=True)
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == '__main__':
    main()
