import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from pydantic import BaseModel

try:
    from .downloader import get_media_info, download_media
except ImportError:
    from downloader import get_media_info, download_media

try:
    from .icons import get_icon_bytes
except ImportError:
    from icons import get_icon_bytes

app = FastAPI(title="GI LINK Media Downloader", version="1.0.0")

class InfoRequest(BaseModel):
    url: str

def remove_temp_file(path: str):
    """Deletes temporary file after download completes."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>GI LINK - Universal Video & Audio Downloader</title>
  <meta name="description" content="Download videos and audio from Instagram Reels, YouTube, TikTok, Facebook, Twitter/X, and 1000+ sites." />
  <!-- PWA Meta Tags -->
  <meta name="theme-color" content="#090d16" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="GI LINK" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="apple-touch-icon" href="/icon-192.png" />
  <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fadeIn { animation: fadeIn 0.25s ease-out forwards; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col selection:bg-indigo-500 selection:text-white">

  <!-- Ambient Glow -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none -z-10">
    <div class="absolute -top-32 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-gradient-to-tr from-indigo-600/25 to-pink-500/20 blur-[100px] rounded-full"></div>
  </div>

  <!-- Navbar (Compact) -->
  <header class="border-b border-slate-800/80 backdrop-blur-md bg-slate-950/80 sticky top-0 z-50">
    <div class="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
      <div class="flex items-center space-x-2.5 cursor-pointer" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">
        <img src="/icon-192.png" alt="GI LINK" class="w-8 h-8 rounded-lg shadow-md shadow-indigo-500/30 object-cover" />
        <span class="text-lg font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">GI LINK</span>
      </div>
      
      <div class="flex items-center space-x-2">
        <button id="installBtn" class="hidden items-center space-x-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1.5 rounded-lg transition font-medium shadow-sm">
          <i data-lucide="download-cloud" class="w-3.5 h-3.5"></i>
          <span>Install</span>
        </button>
        <button id="historyBtn" class="flex items-center space-x-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1.5 rounded-lg transition border border-slate-700">
          <i data-lucide="history" class="w-3.5 h-3.5"></i>
          <span class="hidden sm:inline">History</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Content (Single-Screen Mobile Friendly) -->
  <main class="flex-1 max-w-3xl mx-auto px-3.5 py-5 sm:py-8 w-full">
    
    <!-- Hero Title (Clean & Short) -->
    <div class="text-center space-y-1.5 mb-5">
      <h1 class="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
        Download <span class="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Video &amp; Audio</span>
      </h1>
      <p class="text-xs sm:text-sm text-slate-400">
        Instagram Reels, YouTube, TikTok, Facebook &amp; more
      </p>
    </div>

    <!-- URL Input Card -->
    <div class="bg-slate-900/95 border border-slate-800 rounded-xl p-2.5 sm:p-3 shadow-xl backdrop-blur-md">
      <form id="urlForm" class="flex flex-col sm:flex-row items-stretch gap-2">
        <div class="relative flex-1">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <i data-lucide="link-2" class="w-4 h-4"></i>
          </div>
          <input 
            type="url" 
            id="urlInput"
            placeholder="Paste video or reel link here..." 
            required
            class="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-20 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
          />
          <div class="absolute inset-y-0 right-1 flex items-center space-x-1">
            <button 
              type="button" 
              id="pasteBtn"
              title="Paste from clipboard"
              class="px-2 py-1 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:text-white transition flex items-center space-x-1 border border-slate-700"
            >
              <i data-lucide="clipboard" class="w-3 h-3"></i>
              <span>Paste</span>
            </button>
            <button 
              type="button" 
              id="clearBtn"
              title="Clear input"
              class="hidden p-1 text-slate-400 hover:text-white rounded"
            >
              <i data-lucide="x" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>

        <button 
          type="submit" 
          id="fetchBtn"
          class="px-5 py-2.5 rounded-lg font-bold text-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-md transition active:scale-95 flex items-center justify-center space-x-1.5 shrink-0"
        >
          <i data-lucide="search" class="w-4 h-4" id="fetchIcon"></i>
          <span id="fetchText">Fetch</span>
          <div id="fetchSpinner" class="hidden w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </form>
    </div>

    <!-- Supported Platforms Pills (Ultra Compact) -->
    <div class="mt-3.5 flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-400">
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="instagram" class="w-3 h-3 text-pink-500"></i>
        <span>Instagram</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="youtube" class="w-3 h-3 text-red-500"></i>
        <span>YouTube</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="video" class="w-3 h-3 text-cyan-400"></i>
        <span>TikTok</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="facebook" class="w-3 h-3 text-blue-500"></i>
        <span>Facebook</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="twitter" class="w-3 h-3 text-slate-300"></i>
        <span>X / Twitter</span>
      </span>
    </div>

    <!-- Media Details Card (Compact) -->
    <div id="mediaCard" class="hidden mt-4 bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-xl animate-fadeIn">
      <div class="flex flex-col sm:flex-row gap-3.5">
        <!-- Thumbnail -->
        <div class="relative w-full sm:w-44 aspect-video sm:aspect-square max-h-48 bg-slate-950 rounded-lg overflow-hidden shrink-0 border border-slate-800 flex items-center justify-center">
          <img id="mediaThumb" src="" alt="Thumbnail" class="w-full h-full object-cover" />
          <span id="mediaDuration" class="absolute bottom-1.5 right-1.5 bg-black/80 text-[10px] font-mono px-1.5 py-0.5 rounded text-white font-medium"></span>
          <span id="mediaPlatform" class="absolute top-1.5 left-1.5 bg-indigo-600/90 text-[10px] font-semibold px-2 py-0.5 rounded text-white shadow"></span>
        </div>

        <!-- Info & Formats -->
        <div class="flex-1 flex flex-col justify-between">
          <div>
            <h3 id="mediaTitle" class="text-sm sm:text-base font-bold text-white line-clamp-2 leading-snug"></h3>
            <p id="mediaAuthor" class="text-xs text-slate-400 mt-1 flex items-center space-x-1">
              <i data-lucide="user" class="w-3.5 h-3.5 text-slate-500"></i>
              <span id="authorText">Creator</span>
            </p>
          </div>

          <!-- Format Selection -->
          <div class="mt-3">
            <label class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Choose Download Option:</label>
            <div id="formatPresets" class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-1.5">
              <!-- Preset buttons inserted dynamically -->
            </div>
          </div>

          <!-- Action Status / Progress Bar -->
          <div id="downloadStatus" class="hidden mt-2.5 p-2 rounded-lg bg-slate-950 border border-slate-800">
            <div class="flex items-center justify-between text-xs text-slate-300 mb-1">
              <span id="statusText" class="font-medium flex items-center space-x-1.5 text-indigo-300">
                <i data-lucide="loader-2" class="w-3 h-3 animate-spin"></i>
                <span>Preparing download...</span>
              </span>
            </div>
            <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div id="statusBar" class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full w-2/3 animate-pulse"></div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Error Alert Card -->
    <div id="errorCard" class="hidden mt-3.5 p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-start space-x-2">
      <i data-lucide="alert-circle" class="w-4 h-4 text-red-400 shrink-0 mt-0.5"></i>
      <div>
        <p class="font-semibold text-red-300" id="errorTitle">Fetch Error</p>
        <p class="text-red-200/80 mt-0.5" id="errorMessage">Could not fetch video. Please check link.</p>
      </div>
    </div>

  </main>

  <!-- History Drawer Modal -->
  <div id="historyModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex justify-end">
    <div class="w-full max-w-sm bg-slate-900 border-l border-slate-800 h-full p-4 overflow-y-auto flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <i data-lucide="history" class="w-4 h-4 text-indigo-400"></i>
            <h3 class="font-bold text-white text-base">Download History</h3>
          </div>
          <button id="closeHistoryBtn" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>
        <div id="historyList" class="mt-3 space-y-2 text-xs">
          <!-- History items -->
        </div>
      </div>
      <div class="pt-3 border-t border-slate-800">
        <button id="clearHistoryBtn" class="w-full py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded transition border border-red-500/20">
          Clear History
        </button>
      </div>
    </div>
  </div>

  <!-- Footer (Minimal) -->
  <footer class="border-t border-slate-800/60 py-3.5 bg-slate-950 text-center text-[11px] text-slate-500 mt-auto">
    <p>&copy; 2026 GI LINK. Fast &amp; Free Media Downloader.</p>
    <p class="mt-1 text-slate-600">Created by <span class="text-slate-400 font-medium">Ghalib Kamal</span></p>
  </footer>

  <script>
  document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const urlInput = document.getElementById('urlInput');
    const fetchBtn = document.getElementById('fetchBtn');
    const fetchIcon = document.getElementById('fetchIcon');
    const fetchText = document.getElementById('fetchText');
    const fetchSpinner = document.getElementById('fetchSpinner');
    const mediaCard = document.getElementById('mediaCard');
    const errorCard = document.getElementById('errorCard');
    const errorMessage = document.getElementById('errorMessage');
    const mediaThumb = document.getElementById('mediaThumb');
    const mediaTitle = document.getElementById('mediaTitle');
    const mediaAuthor = document.getElementById('authorText');
    const mediaDuration = document.getElementById('mediaDuration');
    const mediaPlatform = document.getElementById('mediaPlatform');
    const formatPresets = document.getElementById('formatPresets');
    const downloadStatus = document.getElementById('downloadStatus');
    const statusText = document.getElementById('statusText');
    const historyBtn = document.getElementById('historyBtn');
    const historyModal = document.getElementById('historyModal');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const historyList = document.getElementById('historyList');
    const pasteBtn = document.getElementById('pasteBtn');
    const clearBtn = document.getElementById('clearBtn');

    const updateHistory = (item) => {
      const div = document.createElement('div');
      div.className = 'p-2 rounded bg-slate-800/50 border border-slate-700/60';
      div.innerHTML = `<a href="#" class="text-indigo-300 hover:underline line-clamp-1" data-url="${item.url}">${item.title}</a><span class="text-slate-500 text-[10px]">${item.platform}</span>`;
      historyList.prepend(div);
      div.querySelector('a').addEventListener('click', (e) => {
        e.preventDefault();
        urlInput.value = item.url;
        fetchMedia();
        historyModal.classList.add('hidden');
      });
    };

    const fetchMedia = async () => {
      const url = urlInput.value.trim();
      if (!url) return;
      fetchSpinner.classList.remove('hidden');
      fetchIcon.classList.add('hidden');
      fetchBtn.disabled = true;
      errorCard.classList.add('hidden');
      mediaCard.classList.add('hidden');
      downloadStatus.classList.add('hidden');

      try {
        const resp = await fetch('/api/info', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'Failed to retrieve media');
        const info = data.data;
        mediaThumb.src = info.thumbnail || '';
        mediaTitle.textContent = info.title;
        mediaAuthor.textContent = info.uploader;
        mediaDuration.textContent = info.duration || '';
        mediaPlatform.textContent = info.platform;
        formatPresets.innerHTML = '';

        info.presets.forEach(p => {
          const btn = document.createElement('button');
          btn.className = 'w-full px-3 py-2 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 transition flex items-center justify-between font-medium active:scale-98';
          btn.innerHTML = `<span>${p.name}</span><span class="text-[10px] text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">${p.badge || p.ext}</span>`;
          btn.addEventListener('click', () => startDownload(url, p.id, p.ext === 'mp3'));
          formatPresets.appendChild(btn);
        });

        mediaCard.classList.remove('hidden');
        updateHistory({ url, title: info.title, platform: info.platform });
      } catch (e) {
        errorMessage.textContent = e.message;
        errorCard.classList.remove('hidden');
      } finally {
        fetchSpinner.classList.add('hidden');
        fetchIcon.classList.remove('hidden');
        fetchBtn.disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();
      }
    };

    const startDownload = async (url, formatSpec, isAudio) => {
      downloadStatus.classList.remove('hidden');
      statusText.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Downloading media file...</span>`;
      if (typeof lucide !== 'undefined') lucide.createIcons();

      const dlUrl = `/api/download?url=${encodeURIComponent(url)}&format_spec=${encodeURIComponent(formatSpec)}&is_audio=${isAudio}`;

      try {
        const res = await fetch(dlUrl);
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Download request failed (' + res.status + ')');
        }

        // Get filename from Content-Disposition header
        let filename = 'media_download.mp4';
        const disposition = res.headers.get('content-disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
          const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
          if (matches != null && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
          }
        }

        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(blobUrl);
        a.remove();

        statusText.innerHTML = `<i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-400"></i><span class="text-emerald-400">Download complete!</span>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
        setTimeout(() => downloadStatus.classList.add('hidden'), 4000);
      } catch (err) {
        statusText.innerHTML = `<i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-red-400"></i><span class="text-red-400">${err.message}</span>`;
        if (typeof lucide !== 'undefined') lucide.createIcons();
      }
    };

    urlForm.addEventListener('submit', (e) => { e.preventDefault(); fetchMedia(); });

    pasteBtn.addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text) urlInput.value = text;
      } catch (_) {}
    });

    urlInput.addEventListener('input', () => {
      clearBtn.style.display = urlInput.value ? 'block' : 'none';
    });
    clearBtn.addEventListener('click', () => { urlInput.value = ''; clearBtn.style.display = 'none'; });

    historyBtn.addEventListener('click', () => historyModal.classList.remove('hidden'));
    closeHistoryBtn.addEventListener('click', () => historyModal.classList.add('hidden'));
    clearHistoryBtn.addEventListener('click', () => { historyList.innerHTML = ''; });

    if (typeof lucide !== 'undefined') lucide.createIcons();
  });

  // --- PWA: Service Worker Registration ---
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      console.log('SW registered:', reg.scope);
    }).catch(err => console.log('SW registration failed:', err));
  }

  // --- PWA: Install Prompt ---
  let deferredPrompt = null;
  const installBtn = document.getElementById('installBtn');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
      installBtn.classList.remove('hidden');
      installBtn.classList.add('flex');
    }
  });

  if (installBtn) {
    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      deferredPrompt = null;
      installBtn.classList.add('hidden');
      installBtn.classList.remove('flex');
    });
  }

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    if (installBtn) {
      installBtn.classList.add('hidden');
      installBtn.classList.remove('flex');
    }
  });
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=INDEX_HTML)

# --- PWA Endpoints ---

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
const CACHE_NAME = 'gilink-v2';
const STATIC_ASSETS = [
  '/',
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
    return Response(content=SW_JS, media_type="application/javascript",
                    headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})

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
    background_tasks: BackgroundTasks,
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

        # Schedule automatic cleanup of downloaded media after sending
        background_tasks.add_task(remove_temp_file, filepath)

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "GI LINK Media Downloader"}
