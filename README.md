# OmniDrop Media Downloader

A **FastAPI** based universal media downloader that supports YouTube, Instagram Reels, TikTok, Facebook, Twitter/X, Reddit, Pinterest, and many more platforms via **yt‑dlp**.  The web UI is built with **Tailwind CSS** and offers one‑click download presets (1080p, 720p, 480p, best audio, etc.).

## Features
- Server‑side extraction using `yt‑dlp` – works with > 1000 sites.
- Optional `static‑ffmpeg` bundle for headless FFmpeg on macOS (no external binary needed).
- Clean responsive UI with dark mode support.
- Download history stored in the browser session.
- Automatic cleanup of temporary files after download.

## Project Structure
```
media-downloader/
├─ app/
│  ├─ __init__.py
│  ├─ main.py            # FastAPI entry point
│  ├─ downloader.py      # yt‑dlp wrapper & helper functions
│  ├─ templates/
│  │   └─ index.html     # UI template (Jinja2)
│  └─ static/
│      ├─ style.css      # custom Tailwind overrides & animation
│      └─ app.js         # client‑side logic
├─ downloads/            # (generated) downloaded files
├─ requirements.txt      # python dependencies
├─ .gitignore            # ignored files for Git
└─ README.md             # this document
```

## Prerequisites
- macOS (the sandbox used macOS 12+).  The code works on Linux/Windows as well.
- Python 3.14 (or any 3.9+).
- **Homebrew** (optional, only for installing system `ffmpeg` if you prefer).

## Quick Start (local development)
```bash
# 1️⃣ Clone the repo (or copy the folder you just created)
git clone https://github.com/<YOUR_USERNAME>/omnidrop.git
cd omnidrop/media-downloader

# 2️⃣ Create a virtual environment (already prepared in the scratch folder)
python3 -m venv venv
source venv/bin/activate

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run the server
uvicorn app.main:app --reload
```
Open your browser at **http://127.0.0.1:8000** – you should see the OmniDrop UI.

### Why the `static‑ffmpeg` package?
The sandbox cannot resolve external hostnames, so the regular `ffmpeg` binary is unavailable.  `static‑ffmpeg` bundles a pre‑compiled FFmpeg that works out‑of‑the‑box on macOS (the installer already ran during setup).  If you have system `ffmpeg` installed via Homebrew, you can skip this package – just remove it from `requirements.txt`.

## Deploying to GitHub
1. **Create a repository** on GitHub (public or private).
2. In your local project folder run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit – OmniDrop media downloader"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/omnidrop.git
   git push -u origin main
   ```
3. (Optional) Add a **GitHub Actions** workflow to automatically lint and test the code.
   ```yaml
   # .github/workflows/ci.yml
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: macos-latest
       steps:
         - uses: actions/checkout@v4
         - name: Set up Python
           uses: actions/setup-python@v5
           with:
             python-version: "3.14"
         - name: Install deps
           run: |
             python -m venv venv
             source venv/bin/activate
             pip install -r requirements.txt
         - name: Run lint
           run: |
             source venv/bin/activate
             pip install flake8
             flake8 app
   ```
   Add the file under `.github/workflows/ci.yml` and push – GitHub will run the CI on each push.

## Common Tasks
| Task | Command |
|------|---------|
| **Run server (production)** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Re‑install deps** | `pip install -r requirements.txt --upgrade` |
| **Clean download folder** | `rm -rf downloads/*` |
| **Add a new Python package** | `pip install <pkg> && pip freeze > requirements.txt` |
| **Create a Git tag** | `git tag v1.0.0 && git push --tags` |

## FAQ
- **Do I need to run `static‑ffmpeg` each time?** No – once installed it stays in the virtual environment.
- **Can I host this on a cloud platform?** Absolutely. Deploy the FastAPI app on any PaaS that supports Python (Render, Fly.io, Railway, Vercel with a serverless adapter, etc.).
- **Where are the downloaded files stored?** Under the `downloads/` directory inside the project. They are removed automatically after the response is sent, but you can change the cleanup behavior in `app/main.py`.
- **How to add more preset qualities?** Edit the `presets` list in `downloader.py` – each entry maps a `format_id` string that `yt‑dlp` understands.

---
*Happy downloading!*
