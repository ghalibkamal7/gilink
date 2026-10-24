import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

try:
    from .downloader import get_media_info, download_media
except ImportError:
    from downloader import get_media_info, download_media

app = FastAPI(title="OmniDrop Media Downloader", version="1.0.0")

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
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OmniDrop - Universal Social Media & Video Downloader</title>
  <meta name="description" content="Download videos and audio from YouTube, Instagram Reels, TikTok, Facebook, Twitter/X, Reddit, and 1000+ sites in high quality." />
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eef2ff',
              100: '#e0e7ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
            }
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Inter', system-ui, sans-serif; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fadeIn { animation: fadeIn 0.3s ease-out forwards; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans selection:bg-indigo-500 selection:text-white">

  <!-- Background Gradients -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none -z-10">
    <div class="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-indigo-600/25 to-pink-500/20 blur-[130px] rounded-full"></div>
    <div class="absolute bottom-0 right-10 w-[500px] h-[350px] bg-gradient-to-br from-purple-700/15 to-blue-600/15 blur-[120px] rounded-full"></div>
  </div>

  <!-- Navbar -->
  <header class="border-b border-slate-800/80 backdrop-blur-md bg-slate-950/70 sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3 cursor-pointer" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <i data-lucide="download" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <span class="text-xl font-black tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">OmniDrop</span>
          <span class="hidden sm:inline-block text-xs uppercase px-2 py-0.5 ml-2 rounded-full bg-indigo-500/10 text-indigo-400 font-semibold border border-indigo-500/20">Universal Downloader</span>
        </div>
      </div>
      
      <div class="flex items-center space-x-3">
        <a href="#how-it-works" class="text-sm text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-slate-800/50">How it Works</a>
        <a href="#supported" class="text-sm text-slate-400 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-slate-800/50">Platforms</a>
        <button id="historyBtn" class="flex items-center space-x-1.5 text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-1.5 rounded-lg transition border border-slate-700">
          <i data-lucide="history" class="w-4 h-4"></i>
          <span>History</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Hero Content -->
  <main class="flex-1 max-w-4xl mx-auto px-4 py-12 w-full">
    
    <!-- Hero Title -->
    <div class="text-center space-y-4 mb-10">
      <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold">
        <span class="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
        <span>Supports 1000+ Sites &amp; Social Media Apps</span>
      </div>
      <h1 class="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white">
        Download <span class="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Any Video or Audio</span> Instantly
      </h1>
      <p class="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
        YouTube, Instagram Reels, TikTok, Facebook, Twitter / X, Reddit, and more. Paste your link below to get HD video or MP3 audio in seconds.
      </p>
    </div>

    <!-- URL Input Card -->
    <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 sm:p-4 shadow-2xl backdrop-blur-xl transition hover:border-slate-700">
      <form id="urlForm" class="flex flex-col sm:flex-row items-center gap-3">
        <div class="relative w-full flex-1">
          <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <i data-lucide="link-2" class="w-5 h-5"></i>
          </div>
          <input 
            type="url" 
            id="urlInput"
            placeholder="Paste media link here (e.g. Instagram Reel, YouTube, TikTok...)" 
            required
            class="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-11 pr-24 py-3.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition text-sm sm:text-base"
          />
          <div class="absolute inset-y-0 right-1.5 flex items-center space-x-1">
            <button 
              type="button" 
              id="pasteBtn"
              title="Paste from clipboard"
              class="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition flex items-center space-x-1 border border-slate-700"
            >
              <i data-lucide="clipboard" class="w-3.5 h-3.5"></i>
              <span>Paste</span>
            </button>
            <button 
              type="button" 
              id="clearBtn"
              title="Clear input"
              class="hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <i data-lucide="x" class="w-4 h-4"></i>
            </button>
          </div>
        </div>

        <button 
          type="submit" 
          id="fetchBtn"
          class="w-full sm:w-auto px-7 py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition active:scale-95 flex items-center justify-center space-x-2 shrink-0"
        >
          <i data-lucide="search" class="w-4 h-4" id="fetchIcon"></i>
          <span id="fetchText">Fetch Media</span>
          <div id="fetchSpinner" class="hidden w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </form>
    </div>

    <!-- Supported Platforms Grid -->
    <div id="supported" class="mt-8 pt-4">
      <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-3">Popular Supported Platforms</p>
      <div class="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3 text-xs sm:text-sm text-slate-300">
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-red-500/40 transition">
          <i data-lucide="youtube" class="w-4 h-4 text-red-500"></i>
          <span>YouTube</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-pink-500/40 transition">
          <i data-lucide="instagram" class="w-4 h-4 text-pink-500"></i>
          <span>Instagram Reels</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-cyan-500/40 transition">
          <i data-lucide="video" class="w-4 h-4 text-cyan-400"></i>
          <span>TikTok (No Watermark)</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-blue-500/40 transition">
          <i data-lucide="facebook" class="w-4 h-4 text-blue-500"></i>
          <span>Facebook</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-slate-400 transition">
          <i data-lucide="twitter" class="w-4 h-4 text-slate-200"></i>
          <span>Twitter / X</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-orange-500/40 transition">
          <i data-lucide="message-square" class="w-4 h-4 text-orange-500"></i>
          <span>Reddit</span>
        </span>
        <span class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-1.5 hover:border-red-600/40 transition">
          <i data-lucide="image" class="w-4 h-4 text-red-400"></i>
          <span>Pinterest</span>
        </span>
      </div>
    </div>

    <!-- Media Details Card (Initially Hidden) -->
    <div id="mediaCard" class="hidden mt-8 bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-2xl transition animate-fadeIn">
      <div class="flex flex-col md:flex-row gap-6">
        <!-- Thumbnail -->
        <div class="relative w-full md:w-72 aspect-video bg-slate-950 rounded-xl overflow-hidden shrink-0 border border-slate-800 flex items-center justify-center">
          <img id="mediaThumb" src="" alt="Thumbnail" class="w-full h-full object-cover" />
          <span id="mediaDuration" class="absolute bottom-2 right-2 bg-black/80 backdrop-blur-sm text-xs font-mono px-2 py-0.5 rounded text-white font-medium"></span>
          <span id="mediaPlatform" class="absolute top-2 left-2 bg-indigo-600/90 backdrop-blur-sm text-xs font-semibold px-2.5 py-1 rounded-md text-white shadow"></span>
        </div>

        <!-- Info & Formats -->
        <div class="flex-1 flex flex-col justify-between">
          <div>
            <h3 id="mediaTitle" class="text-lg sm:text-xl font-bold text-white line-clamp-2 leading-snug"></h3>
            <p id="mediaAuthor" class="text-sm text-slate-400 mt-1 flex items-center space-x-1.5">
              <i data-lucide="user" class="w-4 h-4 text-slate-500"></i>
              <span id="authorText">Creator</span>
            </p>
          </div>

          <!-- Format Selection -->
          <div class="mt-5 space-y-3">
            <label class="text-xs uppercase font-bold text-slate-400 tracking-wider">Choose Download Quality / Format:</label>
            <div id="formatPresets" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <!-- Preset buttons inserted dynamically -->
            </div>
          </div>

          <!-- Action Status / Progress Bar -->
          <div id="downloadStatus" class="hidden mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div class="flex items-center justify-between text-xs text-slate-300 mb-1.5">
              <span id="statusText" class="font-medium flex items-center space-x-1.5">
                <i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin text-indigo-400"></i>
                <span>Processing media on server...</span>
              </span>
            </div>
            <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div id="statusBar" class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full w-2/3 animate-pulse"></div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Error Alert Card -->
    <div id="errorCard" class="hidden mt-6 p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-200 text-sm flex items-start space-x-3">
      <i data-lucide="alert-circle" class="w-5 h-5 text-red-400 shrink-0 mt-0.5"></i>
      <div>
        <p class="font-semibold text-red-300" id="errorTitle">Download Error</p>
        <p class="text-xs text-red-200/80 mt-1" id="errorMessage">Could not fetch video. Please make sure the URL is public and valid.</p>
      </div>
    </div>

    <!-- Feature Highlights -->
    <div class="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-4">
          <i data-lucide="sparkles" class="w-5 h-5"></i>
        </div>
        <h4 class="font-bold text-white mb-1">No Watermarks</h4>
        <p class="text-sm text-slate-400">Download TikTok, Instagram, and Shorts without any annoying watermarks or logos.</p>
      </div>

      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div class="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-4">
          <i data-lucide="zap" class="w-5 h-5"></i>
        </div>
        <h4 class="font-bold text-white mb-1">Lightning Fast</h4>
        <p class="text-sm text-slate-400">Direct server-side extraction and MP4/MP3 conversion powered by high-speed engines.</p>
      </div>

      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div class="w-10 h-10 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center mb-4">
          <i data-lucide="shield-check" class="w-5 h-5"></i>
        </div>
        <h4 class="font-bold text-white mb-1">100% Free &amp; Secure</h4>
        <p class="text-sm text-slate-400">No account required, no registration, no hidden limits. Safe and privacy focused.</p>
      </div>
    </div>

    <!-- How It Works Section -->
    <div id="how-it-works" class="mt-16 pt-8 border-t border-slate-800/80">
      <h2 class="text-2xl font-bold text-center text-white mb-8">How to Download in 3 Steps</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
        <div class="flex flex-col items-center p-4">
          <div class="w-12 h-12 rounded-full bg-slate-800 text-indigo-400 font-extrabold text-lg flex items-center justify-center mb-3 border border-slate-700">1</div>
          <h4 class="font-semibold text-white mb-1">Copy Link</h4>
          <p class="text-xs text-slate-400">Copy the video or reel link from Instagram, YouTube, TikTok, or any social app.</p>
        </div>
        <div class="flex flex-col items-center p-4">
          <div class="w-12 h-12 rounded-full bg-slate-800 text-indigo-400 font-extrabold text-lg flex items-center justify-center mb-3 border border-slate-700">2</div>
          <h4 class="font-semibold text-white mb-1">Paste &amp; Fetch</h4>
          <p class="text-xs text-slate-400">Paste the URL in the box above and click "Fetch Media" to extract formats.</p>
        </div>
        <div class="flex flex-col items-center p-4">
          <div class="w-12 h-12 rounded-full bg-slate-800 text-indigo-400 font-extrabold text-lg flex items-center justify-center mb-3 border border-slate-700">3</div>
          <h4 class="font-semibold text-white mb-1">Download File</h4>
          <p class="text-xs text-slate-400">Select MP4 video resolution or MP3 audio and enjoy your download offline.</p>
        </div>
      </div>
    </div>

  </main>

  <!-- History Drawer Modal -->
  <div id="historyModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex justify-end">
    <div class="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between pb-4 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <i data-lucide="history" class="w-5 h-5 text-indigo-400"></i>
            <h3 class="font-bold text-white text-lg">Download History</h3>
          </div>
          <button id="closeHistoryBtn" class="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>
        <div id="historyList" class="mt-4 space-y-3">
          <!-- History items -->
        </div>
      </div>
      <div class="pt-4 border-t border-slate-800">
        <button id="clearHistoryBtn" class="w-full py-2 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded-lg transition border border-red-500/20">
          Clear History
        </button>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 py-6 mt-16 bg-slate-950 text-center text-xs text-slate-500">
    <div class="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
      <p>&copy; 2026 OmniDrop. All rights reserved. For personal and fair-use only.</p>
      <p class="text-slate-400">FastAPI &amp; yt-dlp Fullstack Application</p>
    </div>
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
    const statusBar = document.getElementById('statusBar');
    const historyBtn = document.getElementById('historyBtn');
    const historyModal = document.getElementById('historyModal');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const historyList = document.getElementById('historyList');
    const pasteBtn = document.getElementById('pasteBtn');
    const clearBtn = document.getElementById('clearBtn');

    const updateHistory = (item) => {
      const div = document.createElement('div');
      div.className = 'p-3 rounded-lg bg-slate-800/50 border border-slate-700';
      div.innerHTML = `<a href="#" class="text-indigo-300 hover:underline" data-url="${item.url}">${item.title}</a> - ${item.platform}`;
      historyList.prepend(div);
      div.querySelector('a').addEventListener('click', (e) => {
        e.preventDefault();
        urlInput.value = item.url;
        fetchMedia();
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
      try {
        const resp = await fetch('/api/info', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });
        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'Unknown error');
        const info = data.data;
        mediaThumb.src = info.thumbnail || '';
        mediaTitle.textContent = info.title;
        mediaAuthor.textContent = info.uploader;
        mediaDuration.textContent = info.duration;
        mediaPlatform.textContent = info.platform;
        formatPresets.innerHTML = '';
        info.presets.forEach(p => {
          const btn = document.createElement('button');
          btn.className = 'w-full px-3 py-2 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition';
          btn.textContent = p.name;
          btn.dataset.format = p.id;
          btn.dataset.audio = p.ext === "mp3" ? 'true' : 'false';
          btn.addEventListener('click', () => startDownload(url, p.id, p.ext === "mp3"));
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
      }
    };

    const startDownload = (url, formatSpec, isAudio) => {
      downloadStatus.classList.remove('hidden');
      statusText.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin text-indigo-400"></i> Preparing download...`;
      const dlUrl = `/api/download?url=${encodeURIComponent(url)}&format_spec=${encodeURIComponent(formatSpec)}&is_audio=${isAudio}`;
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = dlUrl;
      document.body.appendChild(iframe);
      setTimeout(() => downloadStatus.classList.add('hidden'), 3000);
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

    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=INDEX_HTML)

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
    format_spec: str = Query("bestvideo+bestaudio/best"),
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
    return {"status": "ok", "app": "OmniDrop Media Downloader"}
