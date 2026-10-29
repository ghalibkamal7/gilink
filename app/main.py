import os
import re
import urllib.parse
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from pydantic import BaseModel

try:
    from .downloader import get_media_info, download_media
except ImportError:
    from downloader import get_media_info, download_media

try:
    from .icons import get_icon_bytes
except ImportError:
    from icons import get_icon_bytes

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

# --- Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

class InfoRequest(BaseModel):
    url: str

def remove_temp_file(path: str):
    """Deletes temporary file after download completes."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

# --- Rich Schema.org Structured Data for Homepage ---
HOME_SCHEMA = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebApplication",
            "@id": "https://gilinkdl.vercel.app/#webapp",
            "name": "GI LINK",
            "url": "https://gilinkdl.vercel.app/",
            "description": "Fast universal video and audio downloader for Instagram Reels, YouTube, TikTok, Facebook, and more.",
            "applicationCategory": "MultimediaApplication",
            "operatingSystem": "All",
            "author": {
                "@type": "Person",
                "name": "Ghalib Kamal"
            },
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD"
            }
        },
        {
            "@type": "FAQPage",
            "@id": "https://gilinkdl.vercel.app/#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Is GI LINK completely free to use?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes, GI LINK is 100% free with no registration, subscriptions, or hidden charges. You can download personal copies of public media whenever needed."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Which websites and social networks are supported?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "GI LINK supports Instagram Reels, YouTube videos/Shorts, TikTok, Facebook videos, Twitter/X clips, Reddit, Vimeo, SoundCloud, and hundreds of public video hosting sites."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Where are downloaded files saved on my device?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "On Android and PC/Mac, files are saved in your default Downloads folder. On iPhone/iPad, Safari prompts you to save the file into the Files app or photo gallery."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Does GI LINK store copies of downloaded videos?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "No. GI LINK operates as a transient bridge. We do not maintain any permanent database of files or user links. Media files temporarily created during streaming are immediately deleted once transmitted to your browser."
                    }
                },
                {
                    "@type": "Question",
                    "name": "Can I download private Instagram or Facebook videos?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "No. To protect user privacy, GI LINK only supports publicly accessible media links. Content from private accounts cannot be accessed or downloaded."
                    }
                }
            ]
        }
    ]
}

# --- HTML Public Routes ---

@app.get("/", response_class=HTMLResponse)
async def home():
    html = render_layout(
        title="GI LINK - Universal Video & Audio Downloader | Instagram Reels, YouTube & More",
        description="Download high-definition videos and MP3 audio from Instagram Reels, YouTube, TikTok, Facebook, Twitter/X, and 1000+ sites. Fast, free, and secure.",
        canonical_path="",
        content_html=get_home_html(),
        schema_json=HOME_SCHEMA,
        extra_scripts=HOME_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/about", response_class=HTMLResponse)
async def about_page():
    html = render_layout(
        title="About GI LINK - High-Speed Universal Media Downloader",
        description="Learn about GI LINK, our mission, technical architecture, and creator Ghalib Kamal. Designed for fast, privacy-first media archiving.",
        canonical_path="/about",
        content_html=get_about_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    html = render_layout(
        title="Privacy Policy - GI LINK Media Downloader",
        description="Read the GI LINK Privacy Policy. Learn how we safeguard user privacy with our strict zero-logging and ephemeral file-processing architecture.",
        canonical_path="/privacy",
        content_html=get_privacy_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    html = render_layout(
        title="Terms of Service - GI LINK Media Downloader",
        description="Review the terms and conditions governing the use of GI LINK. Fair use policy, intellectual property disclosures, and acceptable use guidelines.",
        canonical_path="/terms",
        content_html=get_terms_html(),
        extra_scripts=SUBPAGE_SCRIPTS
    )
    return HTMLResponse(content=html)

@app.get("/dmca", response_class=HTMLResponse)
async def dmca_page():
    html = render_layout(
        title="DMCA & Copyright Policy - GI LINK",
        description="GI LINK Digital Millennium Copyright Act (DMCA) compliance, non-hosting safe harbor disclosures, and copyright takedown contact information.",
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
    "name": "GI LINK - Universal Media Downloader",
    "short_name": "GI LINK",
    "description": "Download videos and audio from Instagram Reels, YouTube, TikTok, Facebook, Twitter/X and more.",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#020617",
    "theme_color": "#020617",
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
@app.get("/icon-192.jpg")
async def icon_192():
    return Response(
        content=get_icon_bytes(192),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/icon-512.png")
@app.get("/icon-512.jpg")
async def icon_512():
    return Response(
        content=get_icon_bytes(512),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/favicon.ico")
async def favicon():
    return Response(
        content=get_icon_bytes(192),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )

SW_JS = """
const CACHE_NAME = 'gilink-v3';
const STATIC_ASSETS = [
  '/',
  '/about',
  '/privacy',
  '/terms',
  '/dmca',
  '/contact',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/lucide@latest'
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
  if (url.pathname.startsWith('/api/')) {
    return event.respondWith(fetch(event.request));
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
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


# --- API Routes ---

@app.post("/api/info")
async def fetch_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    try:
        data = get_media_info(url)
        return JSONResponse(content={"success": True, "data": data})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/download")
async def trigger_download(
    url: str = Query(...),
    format_spec: str = Query("best"),
    is_audio: bool = Query(False)
):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        result = download_media(url, format_spec, is_audio)
        filepath = result["filepath"]
        filename = result["filename"]
        filesize = result.get("filesize") or (os.path.getsize(filepath) if os.path.exists(filepath) else 0)

        media_type = "audio/mpeg" if is_audio else "video/mp4"

        safe_ascii_filename = re.sub(r'[^\x20-\x7E]', '_', filename).replace('"', '').replace(';', '')
        if not safe_ascii_filename.strip():
            safe_ascii_filename = "media_download.mp4"
        encoded_filename = urllib.parse.quote(filename)

        headers = {
            "Content-Disposition": f'attachment; filename="{safe_ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        }
        if filesize > 0:
            headers["Content-Length"] = str(filesize)

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type,
            headers=headers,
            background=BackgroundTask(remove_temp_file, filepath)
        )
    except Exception as e:
        err_msg = str(e)
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm" in err_msg:
            raise HTTPException(
                status_code=403,
                detail="YouTube has blocked this cloud server IP (Bot Protection). To fix this, export cookies from YouTube and set YOUTUBE_COOKIES in Vercel Environment Variables, exactly like Instagram cookies."
            )
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "GI LINK Media Downloader", "version": "1.1.0"}
