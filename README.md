# GI LINK

GI LINK is a FastAPI application for checking public media links and retrieving available downloads with yt-dlp. The interface is rendered by FastAPI and uses plain CSS and JavaScript; no frontend build step or external UI CDN is required.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. FFmpeg enables audio/video muxing and MP3 conversion. On read-only serverless runtimes, GI LINK caches the FFmpeg binary under the writable temporary directory; if FFmpeg is unavailable, the interface only offers formats the server can return without conversion.

## Test

```bash
python -m unittest discover -s tests -p 'test_verified_issues.py'
python tests/test_suite.py
```

The existing suite includes a live media extraction/download test, which requires outbound network access and a working source URL.

## Deployment and security notes

The app is currently configured for Vercel through `vercel.json`. Configure platform cookies only in server-side environment variables when needed; never put them in browser code or commit them.

The API rejects malformed URLs and destinations that resolve to non-public IP addresses. Media extractors and source platforms can follow redirects and perform their own DNS lookups, so application-level checks cannot fully eliminate SSRF risks from DNS rebinding or redirect chains. Production deployments should apply network-level egress restrictions where available.

The UI only supports public media links. Use the service only for media you are authorized to download, and respect copyright and source-platform terms.
