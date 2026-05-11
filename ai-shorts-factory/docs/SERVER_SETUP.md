# Server setup (Ubuntu GPU host)

1. Clone this repository on the server.
2. Run `bash scripts/install_server.sh` (installs Python venv, FFmpeg, dependencies).
3. Ensure `ffmpeg` is on your PATH (`ffmpeg -version`).
4. Optional: install ComfyUI using `bash scripts/install_comfyui.sh` and follow `docs/MODEL_SETUP.md`.
5. Copy `.env.example` to `.env` and fill keys only if you use external APIs.
6. Start the app: `bash scripts/start_app.sh`.
7. Open `http://SERVER_IP:7860/ui` in a browser.

Windows developers can use Python 3.10+ directly: create a venv, `pip install -r requirements.txt`, install FFmpeg for Windows, then `python app/webui.py`.
