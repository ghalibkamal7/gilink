import os
import re
import socket
import ipaddress
import urllib.parse
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from .downloader import get_media_info, download_media, get_youtube_direct_stream, detect_platform, media_type_for_file
except ImportError:
    from downloader import get_media_info, download_media, get_youtube_direct_stream, detect_platform, media_type_for_file

try:
    from .icons import get_icon_bytes, get_favicon_bytes
except ImportError:
    from icons import get_icon_bytes, get_favicon_bytes

try:
    from .pages import (
        render_layout,
        get_home_html,
        get_about_html,
        get_privacy_html,
        get_terms_html,
        get_dmca_html,
        get_contact_html,
        HOME_SCRIPTS,
        SUBPAGE_SCRIPTS,
    )
except ImportError:
    from pages import (
        render_layout,
        get_home_html,
        get_about_html,
        get_privacy_html,
        get_terms_html,
        get_dmca_html,
        get_contact_html,
        HOME_SCRIPTS,
        SUBPAGE_SCRIPTS,
    )

app = FastAPI(title="GI LINK Media Downloader", version="1.1.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# --- Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' https:; media-src 'self' https: blob:; "
        "style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
    )
    return response

class InfoRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)

def remove_temp_file(path: str):
    """Deletes temporary file after download completes."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

HOME_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "@id": "https://gilinkdl.vercel.app/#webapp",
    "name": "GI LINK",
    "url": "https://gilinkdl.vercel.app/",
    "description": "Retrieve media from supported public links and choose from the formats GI LINK can provide.",
    "applicationCategory": "MultimediaApplication",
    "operatingSystem": "Web",
    "author": {
        "@type": "Person",
        "name": "Ghalib Kamal"
    }
}

# --- HTML Public Routes ---

@app.get("/", response_class=HTMLResponse)
async def home():
    html = render_layout(
        title="GI LINK — Download public media links",
        description="Check a public media link, review the available file formats, and download media you have permission to use.",
        canonical_path="",
        content_html=get_home_html(),
        schema_json=HOME_SCHEMA,
        extra_scripts=HOME_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/about", response_class=HTMLResponse)
async def about_page():
    html = render_layout(
        title="About GI LINK — Public media link downloader",
        description="Learn how GI LINK retrieves media from public links and how to use it responsibly.",
        canonical_path="/about",
        content_html=get_about_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    html = render_layout(
        title="Privacy Policy - GI LINK Media Downloader",
        description="Read the GI LINK privacy policy, including how submitted links and temporary downloads are handled.",
        canonical_path="/privacy",
        content_html=get_privacy_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    html = render_layout(
        title="Terms of Service - GI LINK Media Downloader",
        description="Read the terms for using GI LINK responsibly with public media links you are authorized to download.",
        canonical_path="/terms",
        content_html=get_terms_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/dmca", response_class=HTMLResponse)
async def dmca_page():
    html = render_layout(
        title="DMCA & Copyright Policy - GI LINK",
        description="Contact GI LINK with copyright concerns or requests about links processed by the service.",
        canonical_path="/dmca",
        content_html=get_dmca_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/contact", response_class=HTMLResponse)
async def contact_page():
    html = render_layout(
        title="Contact Us - GI LINK Media Downloader",
        description="Get in touch with the creator of GI LINK for bug reports, extractor suggestions, copyright queries, or feedback.",
        canonical_path="/contact",
        content_html=get_contact_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)


# --- SEO & Crawler Endpoints ---

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /api/

Sitemap: https://gilinkdl.vercel.app/sitemap.xml
"""

@app.get("/robots.txt")
async def robots_txt():
    return Response(
        content=ROBOTS_TXT,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://gilinkdl.vercel.app/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://gilinkdl.vercel.app/about</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://gilinkdl.vercel.app/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://gilinkdl.vercel.app/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://gilinkdl.vercel.app/dmca</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://gilinkdl.vercel.app/contact</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
"""

@app.get("/sitemap.xml")
async def sitemap_xml():
    return Response(
        content=SITEMAP_XML,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/ads.txt")
async def ads_txt():
    # If user configures ADS_TXT_CONTENT in Vercel environment variables, use that
    custom_ads_txt = os.environ.get("ADS_TXT_CONTENT")
    if custom_ads_txt and custom_ads_txt.strip():
        content = custom_ads_txt.strip() + "\n"
    else:
        content = (
            "google.com, pub-6837969928640726, DIRECT, f08c47fec0942fa0\n"
        )
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )


# --- PWA & Icon Endpoints ---

MANIFEST = {
    "name": "GI LINK - Public Media Link Downloader",
    "short_name": "GI LINK",
    "description": "Check supported public media links, review available formats, and download media you are authorized to use.",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#f7f8fa",
    "theme_color": "#f7f8fa",
    "orientation": "any",
    "categories": ["utilities", "entertainment"],
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
    ],
    "screenshots": []
}

@app.get("/manifest.json")
async def manifest():
    return JSONResponse(content=MANIFEST, media_type="application/manifest+json")

@app.get("/icon-192.png")
async def icon_192_png():
    return Response(
        content=get_icon_bytes(192, "png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/icon-192.jpg")
async def icon_192_jpg():
    return Response(
        content=get_icon_bytes(192, "jpg"),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/icon-512.png")
async def icon_512_png():
    return Response(
        content=get_icon_bytes(512, "png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/icon-512.jpg")
async def icon_512_jpg():
    return Response(
        content=get_icon_bytes(512, "jpg"),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/favicon.ico")
async def favicon():
    return Response(
        content=get_favicon_bytes(),
        media_type="image/vnd.microsoft.icon",
        headers={"Cache-Control": "public, max-age=86400"}
    )

SW_JS = """
const CACHE_NAME = 'gilink-v15';
const STATIC_ASSETS = [
  '/',
  '/static/style.css?v=15',
  '/static/app.js?v=15',
  '/icon-192.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response.ok) caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()));
        return response;
      }).catch(async () => (await caches.match(event.request)) || caches.match('/'))
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((response) => {
        if (response.ok) caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()));
        return response;
      });
      return cached || fetched;
    })
  );
});
"""

@app.get("/sw.js")
async def service_worker():
    return Response(
        content=SW_JS,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
    )


# --- API Routes & Security Validation ---

def is_safe_media_url(url: str) -> tuple[bool, str]:
    """Validates URL against SSRF, loopback, link-local, private, and reserved network addresses."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "Malformed URL."

    if parsed.scheme.lower() not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are supported."

    if not parsed.netloc:
        return False, "Missing host domain."

    if "@" in parsed.netloc or parsed.username is not None or parsed.password is not None:
        return False, "URLs containing user credentials are not allowed."

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        return False, "Missing hostname."
    try:
        parsed.port
    except ValueError:
        return False, "Invalid port."

    # Direct hostnames representing local/internal networks
    if hostname in ("localhost", "localtest.me") or hostname.endswith(".local") or hostname.endswith(".internal"):
        return False, "Access to local network hosts is forbidden."

    # Numeric or IP literal checks (including decimal representations e.g. 2130706433 or hex 0x7f000001)
    try:
        ip_val = int(hostname, 0) if (hostname.isdigit() or hostname.startswith("0x")) else hostname
        ip = ipaddress.ip_address(ip_val)
        if not ip.is_global:
            return False, "Access to private or local IP addresses is forbidden."
        return True, ""
    except ValueError:
        pass

    # DNS Resolution check to catch DNS rebinding & domains resolving to private/internal IPs
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if not ip.is_global:
                    return False, f"Domain resolves to forbidden private address ({ip_str})."
            except ValueError:
                continue
    except socket.gaierror:
        return False, "The host could not be resolved."
    except Exception:
        return False, "URL validation failed."

    if not addr_info:
        return False, "The host did not resolve to a public address."

    return True, ""


def public_media_error(error: Exception, platform: str) -> str:
    message = str(error).lower()
    if platform == "Instagram" and any(term in message for term in ("login", "checkpoint", "cookie", "empty media response")):
        return "Instagram did not provide this media. The post must be public and available without signing in."
    if platform == "YouTube" and any(term in message for term in ("sign in", "bot", "confirm you")):
        return "YouTube declined this request. Try a publicly available link again later."
    if "unsupported url" in message or "no suitable extractor" in message:
        return "This source or link format is not currently supported."
    return "Could not retrieve this media. Check that the link is public and try again."

@app.post("/api/info")
async def fetch_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        return JSONResponse(status_code=400, content={"success": False, "error": "URL cannot be empty."})
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    safe, err_reason = is_safe_media_url(url)
    if not safe:
        return JSONResponse(status_code=400, content={"success": False, "error": f"Invalid URL: {err_reason}"})

    try:
        data = get_media_info(url)
        return JSONResponse(content={"success": True, "data": data})
    except Exception as e:
        platform = detect_platform(url)
        print(f"Media info failed for {platform}: {type(e).__name__}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": public_media_error(e, platform)},
        )

def stream_remote(proxy_url: str):
    """Stream chunks directly from proxied media pipeline to eliminate memory and disk overhead."""
    import requests
    with requests.get(proxy_url, stream=True, timeout=60) as resp:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if chunk:
                yield chunk

def make_direct_stream_response(direct: Dict[str, Any]):
    """Construct a streaming response that forwards Content-Length for real-time progress bars.
    Returns None if the remote stream is invalid/expired so caller can try next fallback."""
    import requests
    safe_ascii = re.sub(r'[^\x20-\x7E]', '_', direct["filename"]).replace('"', '').replace(';', '')
    if not safe_ascii.strip():
        safe_ascii = "media_download.mp4"
    encoded_fn = urllib.parse.quote(direct["filename"])
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded_fn}'
    }

    try:
        remote_resp = requests.get(direct["stream_url"], stream=True, timeout=60)
    except Exception as e:
        print(f"Stream URL request failed: {e}")
        return None

    # Check if response is actually media (not an error page or expired URL text)
    ct = remote_resp.headers.get("content-type", "")
    cl_raw = remote_resp.headers.get("content-length")

    # If response is tiny text (like "Videoplayback URL has expired."), it's an error
    if cl_raw and int(cl_raw) < 200 and ("text/" in ct or "application/json" in ct):
        remote_resp.close()
        return None

    # If HTTP error status
    if remote_resp.status_code >= 400:
        remote_resp.close()
        return None

    cl = cl_raw or direct.get("content_length")
    if cl:
        headers["Content-Length"] = str(cl)

    def iter_remote():
        first_chunk = True
        try:
            for chunk in remote_resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    # Detect error response masquerading as media on first chunk
                    if first_chunk and len(chunk) < 200:
                        text_check = chunk.decode('utf-8', errors='ignore').strip().lower()
                        if 'expired' in text_check or 'error' in text_check or '<html' in text_check:
                            return
                    first_chunk = False
                    yield chunk
        finally:
            remote_resp.close()

    return StreamingResponse(
        iter_remote(),
        media_type=direct["media_type"],
        headers=headers
    )

def file_iterator(file_path: str, chunk_size: int = 64 * 1024):
    """Yield file chunks to bypass serverless response payload limits and clean up upon completion."""
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
    finally:
        remove_temp_file(file_path)

@app.get("/api/download")
async def trigger_download(
    url: str = Query(..., max_length=2048),
    format_spec: str = Query("best", max_length=128),
    is_audio: bool = Query(False)
):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Invalid URL: URL cannot be empty.")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    safe, err_reason = is_safe_media_url(url)
    if not safe:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {err_reason}")

    # Fast direct streaming proxy for YouTube to bypass datacenter IP restrictions
    if detect_platform(url) == "YouTube" and not is_audio:
        direct = get_youtube_direct_stream(url, is_audio=is_audio, format_spec=format_spec)
        if direct:
            direct_resp = make_direct_stream_response(direct)
            if direct_resp:
                return direct_resp

    filepath = None
    try:
        result = download_media(url, format_spec, is_audio)
        filepath = result["filepath"]
        filename = result["filename"]
        filesize = result.get("filesize") or (os.path.getsize(filepath) if os.path.exists(filepath) else 0)

        media_type = media_type_for_file(filename, is_audio)

        safe_ascii_filename = re.sub(r'[^\x20-\x7E]', '_', filename).replace('"', '').replace(';', '')
        if not safe_ascii_filename.strip():
            safe_ascii_filename = "media_download.mp4"
        encoded_filename = urllib.parse.quote(filename)

        headers = {
            "Content-Disposition": f'attachment; filename="{safe_ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        }
        if filesize > 0:
            headers["Content-Length"] = str(filesize)

        return StreamingResponse(
            file_iterator(filepath),
            media_type=media_type,
            headers=headers,
            background=BackgroundTask(remove_temp_file, filepath)
        )
    except Exception as e:
        if filepath:
            remove_temp_file(filepath)
        # Final safety net for YouTube if bot detection still triggers
        if detect_platform(url) == "YouTube" and not is_audio:
            direct = get_youtube_direct_stream(url, is_audio=is_audio, format_spec=format_spec)
            if direct:
                direct_resp = make_direct_stream_response(direct)
                if direct_resp:
                    return direct_resp

        err_msg = str(e).lower()
        if "sign in to confirm" in err_msg or "bot" in err_msg:
            raise HTTPException(
                status_code=403,
                detail=public_media_error(e, "YouTube")
            )
        if "Instagram requires" in err_msg or "INSTAGRAM_COOKIES" in err_msg:
            raise HTTPException(
                status_code=403,
                detail=public_media_error(e, "Instagram")
            )
        print(f"Media download failed for {detect_platform(url)}: {type(e).__name__}")
        raise HTTPException(
            status_code=502,
            detail=public_media_error(e, detect_platform(url)),
        )

@app.get("/api/health")
async def health():
    yt_c = os.environ.get("YOUTUBE_COOKIES") or ""
    ig_c = os.environ.get("INSTAGRAM_COOKIES") or ""
    from .downloader import get_cookies_filepath, has_ffmpeg
    ck_path = get_cookies_filepath()
    ck_lines = 0
    if ck_path and os.path.exists(ck_path):
        with open(ck_path, "r", encoding="utf-8") as f:
            ck_lines = len(f.readlines())
    return {
        "status": "ok",
        "app": "GI LINK Media Downloader",
        "version": "1.1.0",
        "ffmpeg_available": has_ffmpeg(),
        "yt_cookies_configured": bool(yt_c.strip()),
        "yt_cookies_char_length": len(yt_c.strip()),
        "ig_cookies_configured": bool(ig_c.strip()),
        "cookie_file_active": bool(ck_path),
        "cookie_lines_parsed": ck_lines
    }
