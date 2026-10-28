"""
HTML Pages and Layout templates for GI LINK.
Engineered for Technical SEO, Semantic Accessibility, Performance, and AdSense readiness.
"""

import json
from typing import Optional

BASE_URL = "https://gilinkdl.vercel.app"

def render_layout(
    title: str,
    description: str,
    canonical_path: str,
    content_html: str,
    schema_json: Optional[dict] = None,
    extra_scripts: str = ""
) -> str:
    canonical_url = f"{BASE_URL}{canonical_path}"
    og_image = f"{BASE_URL}/icon-512.png"

    schema_tag = ""
    if schema_json:
        schema_tag = f'<script type="application/ld+json">{json.dumps(schema_json, ensure_ascii=False)}</script>'

    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta name="keywords" content="video downloader, reels downloader, instagram reel download, mp4 downloader, audio extractor, online media downloader, GI LINK, free video download" />
  <meta name="author" content="Ghalib Kamal" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{canonical_url}" />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:image" content="{og_image}" />
  <meta property="og:site_name" content="GI LINK" />
  <meta property="og:locale" content="en_US" />

  <!-- Twitter / X Cards -->
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:url" content="{canonical_url}" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{og_image}" />
  <meta name="twitter:creator" content="@ghalibkamal" />

  <!-- PWA & Mobile Meta Tags -->
  <meta name="theme-color" content="#090d16" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="GI LINK" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="apple-touch-icon" href="/icon-192.png" />
  <link rel="icon" type="image/jpeg" sizes="192x192" href="/icon-192.png" />
  <link rel="shortcut icon" href="/favicon.ico" />

  <!-- Resource Preconnects -->
  <link rel="preconnect" href="https://cdn.tailwindcss.com" crossorigin />
  <link rel="preconnect" href="https://unpkg.com" crossorigin />

  <!-- CSS & Icons -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>

  {schema_tag}

  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .animate-fadeIn {{ animation: fadeIn 0.25s ease-out forwards; }}
    details > summary {{ list-style: none; }}
    details > summary::-webkit-details-marker {{ display: none; }}
    details[open] summary svg {{ transform: rotate(180deg); }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col selection:bg-indigo-500 selection:text-white">

  <!-- Ambient Glow Background -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none -z-10" aria-hidden="true">
    <div class="absolute -top-32 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-600/20 via-purple-600/20 to-pink-500/15 blur-[120px] rounded-full"></div>
  </div>

  <!-- Main Header & Navigation -->
  <header class="border-b border-slate-800/80 backdrop-blur-md bg-slate-950/85 sticky top-0 z-50">
    <div class="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
      <a href="/" class="flex items-center space-x-2.5 group" aria-label="GI LINK Home">
        <img src="/icon-192.png" alt="GI LINK Logo" class="w-8 h-8 rounded-lg shadow-md shadow-indigo-500/30 object-cover group-hover:scale-105 transition" width="32" height="32" />
        <span class="text-lg font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">GI LINK</span>
      </a>

      <!-- Desktop Nav Links -->
      <nav class="hidden md:flex items-center space-x-5 text-xs font-medium text-slate-300" aria-label="Main Navigation">
        <a href="/" class="hover:text-indigo-400 transition">Downloader</a>
        <a href="/#how-it-works" class="hover:text-indigo-400 transition">How It Works</a>
        <a href="/#faq" class="hover:text-indigo-400 transition">FAQ</a>
        <a href="/about" class="hover:text-indigo-400 transition">About</a>
        <a href="/contact" class="hover:text-indigo-400 transition">Contact</a>
      </nav>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2">
        <button id="installBtn" class="hidden items-center space-x-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1.5 rounded-lg transition font-medium shadow-sm" aria-label="Install App">
          <i data-lucide="download-cloud" class="w-3.5 h-3.5" aria-hidden="true"></i>
          <span>Install</span>
        </button>
        <button id="historyBtn" class="flex items-center space-x-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1.5 rounded-lg transition border border-slate-700" aria-label="View Download History">
          <i data-lucide="history" class="w-3.5 h-3.5" aria-hidden="true"></i>
          <span class="hidden sm:inline">History</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Content Container -->
  {content_html}

  <!-- Global Footer -->
  <footer class="border-t border-slate-800/70 py-8 bg-slate-950/90 text-slate-400 text-xs mt-auto">
    <div class="max-w-4xl mx-auto px-4 flex flex-col items-center space-y-4">
      <div class="flex flex-wrap justify-center gap-x-6 gap-y-2 text-slate-400 text-[13px]">
        <a href="/" class="hover:text-indigo-400 transition">Home</a>
        <a href="/#how-it-works" class="hover:text-indigo-400 transition">How It Works</a>
        <a href="/#faq" class="hover:text-indigo-400 transition">FAQ</a>
        <a href="/about" class="hover:text-indigo-400 transition">About Us</a>
        <a href="/privacy" class="hover:text-indigo-400 transition">Privacy Policy</a>
        <a href="/terms" class="hover:text-indigo-400 transition">Terms of Service</a>
        <a href="/dmca" class="hover:text-indigo-400 transition">DMCA / Disclaimer</a>
        <a href="/contact" class="hover:text-indigo-400 transition">Contact</a>
      </div>

      <div class="text-center text-[11px] text-slate-500 max-w-2xl leading-relaxed">
        <p class="mb-1">&copy; 2026 GI LINK. Fast, Private &amp; Universal Media Downloader.</p>
        <p class="mb-1.5">Created by <a href="/about" class="text-indigo-400 hover:underline font-medium">Ghalib Kamal</a></p>
        <p class="text-[10px] text-slate-600">
          Disclaimer: GI LINK is an educational tool designed for personal, fair-use downloading of user-owned or public content. We do not host or archive media files on our servers. All rights belong to their respective copyright owners.
        </p>
      </div>
    </div>
  </footer>

  {extra_scripts}
</body>
</html>"""


# ==============================================================================
# HOMEPAGE CONTENT WITH TOOL & RICH SEO SECTIONS
# ==============================================================================

def get_home_html() -> str:
    return """
  <!-- Main Downloader Container -->
  <main class="flex-1 max-w-3xl mx-auto px-3.5 py-6 sm:py-9 w-full">
    
    <!-- Hero Title -->
    <div class="text-center space-y-2 mb-6">
      <h1 class="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
        Download <span class="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Video &amp; Audio</span> Online
      </h1>
      <p class="text-xs sm:text-sm text-slate-400 max-w-lg mx-auto">
        Fast, high-quality media extractor for Instagram Reels, YouTube, TikTok, Facebook, Twitter/X, and 1000+ platforms.
      </p>
    </div>

    <!-- URL Input Card -->
    <div class="bg-slate-900/95 border border-slate-800 rounded-xl p-2.5 sm:p-3 shadow-xl backdrop-blur-md">
      <form id="urlForm" class="flex flex-col sm:flex-row items-stretch gap-2">
        <div class="relative flex-1">
          <label for="urlInput" class="sr-only">Paste video or media link</label>
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <i data-lucide="link-2" class="w-4 h-4" aria-hidden="true"></i>
          </div>
          <input 
            type="url" 
            id="urlInput"
            name="url"
            placeholder="Paste video or reel link here..." 
            required
            aria-label="Paste video or reel URL"
            class="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-20 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-sm"
          />
          <div class="absolute inset-y-0 right-1 flex items-center space-x-1">
            <button 
              type="button" 
              id="pasteBtn"
              title="Paste from clipboard"
              aria-label="Paste URL from clipboard"
              class="px-2 py-1 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:text-white transition flex items-center space-x-1 border border-slate-700"
            >
              <i data-lucide="clipboard" class="w-3 h-3" aria-hidden="true"></i>
              <span>Paste</span>
            </button>
            <button 
              type="button" 
              id="clearBtn"
              title="Clear input"
              aria-label="Clear input field"
              class="hidden p-1 text-slate-400 hover:text-white rounded"
            >
              <i data-lucide="x" class="w-3.5 h-3.5" aria-hidden="true"></i>
            </button>
          </div>
        </div>

        <button 
          type="submit" 
          id="fetchBtn"
          aria-label="Fetch Media Details"
          class="px-5 py-2.5 rounded-lg font-bold text-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-md transition active:scale-95 flex items-center justify-center space-x-1.5 shrink-0"
        >
          <i data-lucide="search" class="w-4 h-4" id="fetchIcon" aria-hidden="true"></i>
          <span id="fetchText">Fetch</span>
          <div id="fetchSpinner" class="hidden w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></div>
        </button>
      </form>
    </div>

    <!-- Supported Platforms Pills -->
    <div class="mt-3.5 flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-400" aria-label="Supported Platforms">
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="instagram" class="w-3 h-3 text-pink-500" aria-hidden="true"></i>
        <span>Instagram Reels</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="youtube" class="w-3 h-3 text-red-500" aria-hidden="true"></i>
        <span>YouTube</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="video" class="w-3 h-3 text-cyan-400" aria-hidden="true"></i>
        <span>TikTok</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="facebook" class="w-3 h-3 text-blue-500" aria-hidden="true"></i>
        <span>Facebook</span>
      </span>
      <span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 flex items-center space-x-1">
        <i data-lucide="twitter" class="w-3 h-3 text-slate-300" aria-hidden="true"></i>
        <span>X / Twitter</span>
      </span>
    </div>

    <!-- Media Details Card -->
    <section id="mediaCard" class="hidden mt-4 bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-xl animate-fadeIn" aria-live="polite">
      <div class="flex flex-col sm:flex-row gap-3.5">
        <!-- Thumbnail -->
        <div class="relative w-full sm:w-44 aspect-video sm:aspect-square max-h-48 bg-slate-950 rounded-lg overflow-hidden shrink-0 border border-slate-800 flex items-center justify-center">
          <img id="mediaThumb" src="" alt="Media thumbnail preview" class="w-full h-full object-cover" />
          <span id="mediaDuration" class="absolute bottom-1.5 right-1.5 bg-black/80 text-[10px] font-mono px-1.5 py-0.5 rounded text-white font-medium"></span>
          <span id="mediaPlatform" class="absolute top-1.5 left-1.5 bg-indigo-600/90 text-[10px] font-semibold px-2 py-0.5 rounded text-white shadow"></span>
        </div>

        <!-- Info & Formats -->
        <div class="flex-1 flex flex-col justify-between">
          <div>
            <h3 id="mediaTitle" class="text-sm sm:text-base font-bold text-white line-clamp-2 leading-snug"></h3>
            <p id="mediaAuthor" class="text-xs text-slate-400 mt-1 flex items-center space-x-1">
              <i data-lucide="user" class="w-3.5 h-3.5 text-slate-500" aria-hidden="true"></i>
              <span id="authorText">Creator</span>
            </p>
          </div>

          <!-- Format Selection -->
          <div class="mt-3">
            <span class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Choose Download Option:</span>
            <div id="formatPresets" class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-1.5">
              <!-- Preset buttons inserted dynamically -->
            </div>
          </div>

          <!-- Action Status / Progress Bar -->
          <div id="downloadStatus" class="hidden mt-2.5 p-2 rounded-lg bg-slate-950 border border-slate-800" role="status">
            <div class="flex items-center justify-between text-xs text-slate-300 mb-1">
              <span id="statusText" class="font-medium flex items-center space-x-1.5 text-indigo-300">
                <i data-lucide="loader-2" class="w-3 h-3 animate-spin" aria-hidden="true"></i>
                <span>Preparing download...</span>
              </span>
            </div>
            <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div id="statusBar" class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full w-2/3 animate-pulse"></div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Error Alert Card -->
    <div id="errorCard" class="hidden mt-3.5 p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-start space-x-2" role="alert">
      <i data-lucide="alert-circle" class="w-4 h-4 text-red-400 shrink-0 mt-0.5" aria-hidden="true"></i>
      <div>
        <p class="font-semibold text-red-300" id="errorTitle">Fetch Error</p>
        <p class="text-red-200/80 mt-0.5" id="errorMessage">Could not fetch video. Please check link.</p>
      </div>
    </div>

    <!-- Informational SEO Section 1: How It Works -->
    <section id="how-it-works" class="mt-12 pt-8 border-t border-slate-800/60">
      <div class="text-center mb-6">
        <h2 class="text-lg sm:text-2xl font-bold text-white tracking-tight">How to Download Videos &amp; Reels with GI LINK</h2>
        <p class="text-xs sm:text-sm text-slate-400 mt-1">Extract high-resolution media in three effortless steps</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-lg mb-3 border border-indigo-500/30">1</div>
          <h3 class="font-semibold text-white text-sm mb-1">Copy the Video URL</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Open your favorite social app (Instagram, YouTube, TikTok) and copy the shareable video or reel link.</p>
        </div>

        <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center font-bold text-lg mb-3 border border-purple-500/30">2</div>
          <h3 class="font-semibold text-white text-sm mb-1">Paste into GI LINK</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Paste the link into the search box above and tap <strong>Fetch</strong>. Our engine instantly analyzes stream qualities.</p>
        </div>

        <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-lg bg-pink-600/20 text-pink-400 flex items-center justify-center font-bold text-lg mb-3 border border-pink-500/30">3</div>
          <h3 class="font-semibold text-white text-sm mb-1">Save HD MP4 or MP3</h3>
          <p class="text-xs text-slate-400 leading-relaxed">Select your preferred resolution (1080p, 720p, or Audio) to save the media file directly to your device.</p>
        </div>
      </div>
    </section>

    <!-- Informational SEO Section 2: Core Features -->
    <section class="mt-10 pt-8 border-t border-slate-800/60">
      <div class="text-center mb-6">
        <h2 class="text-lg sm:text-2xl font-bold text-white tracking-tight">Why Choose GI LINK?</h2>
        <p class="text-xs sm:text-sm text-slate-400 mt-1">Built for speed, user privacy, and zero complications</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
        <div class="p-3.5 bg-slate-900/50 border border-slate-800/70 rounded-lg">
          <div class="flex items-center space-x-2.5 mb-1.5">
            <i data-lucide="zap" class="w-4 h-4 text-amber-400" aria-hidden="true"></i>
            <h3 class="font-bold text-white text-sm">Ultra Fast Extraction</h3>
          </div>
          <p class="text-slate-400 leading-relaxed">Powered by modern high-throughput serverless pipelines, parsing media streams in seconds.</p>
        </div>

        <div class="p-3.5 bg-slate-900/50 border border-slate-800/70 rounded-lg">
          <div class="flex items-center space-x-2.5 mb-1.5">
            <i data-lucide="shield-check" class="w-4 h-4 text-emerald-400" aria-hidden="true"></i>
            <h3 class="font-bold text-white text-sm">Privacy-First Architecture</h3>
          </div>
          <p class="text-slate-400 leading-relaxed">No tracking, no registration required, and downloaded temp files are purged automatically from memory.</p>
        </div>

        <div class="p-3.5 bg-slate-900/50 border border-slate-800/70 rounded-lg">
          <div class="flex items-center space-x-2.5 mb-1.5">
            <i data-lucide="music" class="w-4 h-4 text-pink-400" aria-hidden="true"></i>
            <h3 class="font-bold text-white text-sm">MP3 Audio Extraction</h3>
          </div>
          <p class="text-slate-400 leading-relaxed">Extract crisp audio tracks and background music directly from public video streams.</p>
        </div>

        <div class="p-3.5 bg-slate-900/50 border border-slate-800/70 rounded-lg">
          <div class="flex items-center space-x-2.5 mb-1.5">
            <i data-lucide="smartphone" class="w-4 h-4 text-indigo-400" aria-hidden="true"></i>
            <h3 class="font-bold text-white text-sm">Installable PWA</h3>
          </div>
          <p class="text-slate-400 leading-relaxed">Install GI LINK as a lightweight Progressive Web App on iOS, Android, macOS, and Windows.</p>
        </div>
      </div>
    </section>

    <!-- Informational SEO Section 3: Frequently Asked Questions (Accordion) -->
    <section id="faq" class="mt-10 pt-8 border-t border-slate-800/60">
      <div class="text-center mb-6">
        <h2 class="text-lg sm:text-2xl font-bold text-white tracking-tight">Frequently Asked Questions</h2>
        <p class="text-xs sm:text-sm text-slate-400 mt-1">Everything you need to know about using GI LINK</p>
      </div>

      <div class="space-y-2.5 max-w-2xl mx-auto text-xs">
        <details class="bg-slate-900/70 border border-slate-800 rounded-lg p-3 group">
          <summary class="flex items-center justify-between font-semibold text-white cursor-pointer select-none">
            <span>Is GI LINK completely free to use?</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition group-open:rotate-180" aria-hidden="true"></i>
          </summary>
          <p class="text-slate-400 mt-2.5 leading-relaxed">
            Yes, GI LINK is 100% free with no registration, subscriptions, or hidden charges. You can download personal copies of public media whenever needed.
          </p>
        </details>

        <details class="bg-slate-900/70 border border-slate-800 rounded-lg p-3 group">
          <summary class="flex items-center justify-between font-semibold text-white cursor-pointer select-none">
            <span>Which websites and social networks are supported?</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition group-open:rotate-180" aria-hidden="true"></i>
          </summary>
          <p class="text-slate-400 mt-2.5 leading-relaxed">
            GI LINK supports Instagram Reels, YouTube videos/Shorts, TikTok, Facebook videos, Twitter/X clips, Reddit, Vimeo, SoundCloud, and hundreds of public video hosting sites.
          </p>
        </details>

        <details class="bg-slate-900/70 border border-slate-800 rounded-lg p-3 group">
          <summary class="flex items-center justify-between font-semibold text-white cursor-pointer select-none">
            <span>Where are downloaded files saved on my device?</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition group-open:rotate-180" aria-hidden="true"></i>
          </summary>
          <p class="text-slate-400 mt-2.5 leading-relaxed">
            On Android and PC/Mac, files are saved in your default <code>Downloads</code> folder. On iPhone/iPad, Safari prompts you to save the file into the <strong>Files</strong> app or photo gallery.
          </p>
        </details>

        <details class="bg-slate-900/70 border border-slate-800 rounded-lg p-3 group">
          <summary class="flex items-center justify-between font-semibold text-white cursor-pointer select-none">
            <span>Does GI LINK store copies of downloaded videos?</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition group-open:rotate-180" aria-hidden="true"></i>
          </summary>
          <p class="text-slate-400 mt-2.5 leading-relaxed">
            No. GI LINK operates as a transient bridge. We do not maintain any permanent database of files or user links. Media files temporarily created during streaming are immediately deleted once transmitted to your browser.
          </p>
        </details>

        <details class="bg-slate-900/70 border border-slate-800 rounded-lg p-3 group">
          <summary class="flex items-center justify-between font-semibold text-white cursor-pointer select-none">
            <span>Can I download private Instagram or Facebook videos?</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition group-open:rotate-180" aria-hidden="true"></i>
          </summary>
          <p class="text-slate-400 mt-2.5 leading-relaxed">
            No. To protect user privacy, GI LINK only supports publicly accessible media links. Content from private accounts cannot be accessed or downloaded.
          </p>
        </details>
      </div>
    </section>

  </main>

  <!-- History Drawer Modal -->
  <div id="historyModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex justify-end" aria-modal="true" role="dialog" aria-labelledby="historyTitle">
    <div class="w-full max-w-sm bg-slate-900 border-l border-slate-800 h-full p-4 overflow-y-auto flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <i data-lucide="history" class="w-4 h-4 text-indigo-400" aria-hidden="true"></i>
            <h2 id="historyTitle" class="font-bold text-white text-base">Download History</h2>
          </div>
          <button id="closeHistoryBtn" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white" aria-label="Close history modal">
            <i data-lucide="x" class="w-4 h-4" aria-hidden="true"></i>
          </button>
        </div>
        <div id="historyList" class="mt-3 space-y-2 text-xs">
          <!-- History items dynamically inserted -->
        </div>
      </div>
      <div class="pt-3 border-t border-slate-800">
        <button id="clearHistoryBtn" class="w-full py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded transition border border-red-500/20" aria-label="Clear all download history">
          Clear History
        </button>
      </div>
    </div>
  </div>
"""


# ==============================================================================
# SUBPAGE CONTENTS: ABOUT, PRIVACY, TERMS, DMCA, CONTACT
# ==============================================================================

def get_about_html() -> str:
    return """
  <main class="flex-1 max-w-3xl mx-auto px-4 py-8 w-full">
    <div class="mb-6">
      <a href="/" class="text-xs text-indigo-400 hover:underline inline-flex items-center space-x-1 mb-2">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Downloader</span>
      </a>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-white">About GI LINK</h1>
      <p class="text-xs sm:text-sm text-slate-400 mt-1">High-performance universal media extraction built for the modern web.</p>
    </div>

    <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
      <div>
        <h2 class="text-base font-bold text-white mb-1.5 flex items-center space-x-2">
          <i data-lucide="sparkles" class="w-4 h-4 text-indigo-400"></i>
          <span>Our Mission</span>
        </h2>
        <p>
          GI LINK was created to provide a clean, distraction-free, and reliable media downloader for content creators, researchers, and everyday web users. In a web cluttered with pop-up advertisements, malicious redirects, and broken tools, GI LINK stands out with an ultra-fast, privacy-first interface.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1.5 flex items-center space-x-2">
          <i data-lucide="code-2" class="w-4 h-4 text-purple-400"></i>
          <span>Technology &amp; Architecture</span>
        </h2>
        <p class="mb-2">
          GI LINK is engineered using industry-proven open-source technologies:
        </p>
        <ul class="list-disc list-inside space-y-1 text-slate-400 pl-1">
          <li><strong>Backend:</strong> Python 3 with FastAPI for high-concurrency async request processing.</li>
          <li><strong>Extraction Engine:</strong> Powered by the robust yt-dlp suite with cloud resilience.</li>
          <li><strong>Deployment:</strong> Global serverless edge infrastructure via Vercel.</li>
          <li><strong>Client Experience:</strong> Pure vanilla JavaScript with Tailwind CSS and Progressive Web App (PWA) offline capabilities.</li>
        </ul>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1.5 flex items-center space-x-2">
          <i data-lucide="user-check" class="w-4 h-4 text-emerald-400"></i>
          <span>The Creator</span>
        </h2>
        <p>
          GI LINK is designed, developed, and maintained by <strong>Ghalib Kamal</strong>. Continuous enhancements are made to support changing social media API endpoints, optimize delivery speeds, and ensure mobile responsiveness.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1.5 flex items-center space-x-2">
          <i data-lucide="shield-alert" class="w-4 h-4 text-amber-400"></i>
          <span>Commitment to Fair Use</span>
        </h2>
        <p>
          GI LINK is an educational tool. We believe in fair use, archiving personal creations, and facilitating offline viewing for personal study. We strictly respect intellectual property rights and encourage all users to download content only when authorized by copyright holders.
        </p>
      </div>
    </div>
  </main>
"""

def get_privacy_html() -> str:
    return """
  <main class="flex-1 max-w-3xl mx-auto px-4 py-8 w-full">
    <div class="mb-6">
      <a href="/" class="text-xs text-indigo-400 hover:underline inline-flex items-center space-x-1 mb-2">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Downloader</span>
      </a>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-white">Privacy Policy</h1>
      <p class="text-xs sm:text-sm text-slate-400 mt-1">Last Updated: October 2026 &bull; Strict Zero-Logging Standards</p>
    </div>

    <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
      <div>
        <h2 class="text-base font-bold text-white mb-1">1. Overview</h2>
        <p>
          At <strong>GI LINK</strong>, accessible from <code>https://gilinkdl.vercel.app</code>, the privacy of our visitors is of paramount importance. This Privacy Policy document details the types of information handled by GI LINK and our zero-retention principles.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">2. Information We Do NOT Collect</h2>
        <p>Unlike many online services, GI LINK does NOT:</p>
        <ul class="list-disc list-inside space-y-1 text-slate-400 pl-1 mt-1">
          <li>Require user registration, email, or telephone numbers.</li>
          <li>Store, archive, or catalogue URLs submitted for download.</li>
          <li>Retain permanent copies of media files processed through the engine.</li>
          <li>Sell, lease, or distribute visitor browsing patterns to data brokers.</li>
        </ul>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">3. Ephemeral Processing &amp; File Deletion</h2>
        <p>
          When you request a download, our serverless backend temporarily streams the requested data from the source platform to format the file for your browser. Once the download stream concludes, the temporary server file is immediately purged from system memory (using automated background removal tasks).
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">4. Client-Side Browser Storage (History)</h2>
        <p>
          The download history displayed inside the GI LINK app is maintained exclusively in your device's browser memory (HTML5 Local/DOM storage). It is never synchronized to any remote database and can be cleared instantly via the "Clear History" button.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">5. Log Files and Web Hosting</h2>
        <p>
          GI LINK utilizes standard hosting telemetry provided by Vercel for infrastructure health monitoring. These standard logs (IP addresses, browser type, referring pages, date/time stamps) are not linked to personally identifiable information.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">6. Advertising &amp; Third-Party Cookies</h2>
        <p>
          Third-party advertising partners (such as Google AdSense) may deploy cookies and web beacons on our site to serve relevant ads based on prior visits to this or other websites. Visitors can choose to disable cookies through their individual browser options or via <a href="https://adssettings.google.com" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:underline">Google Ads Settings</a>.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">7. Contact Information</h2>
        <p>
          For privacy inquiries or clarifications regarding our handling practices, please contact us at our <a href="/contact" class="text-indigo-400 hover:underline">Contact Page</a>.
        </p>
      </div>
    </div>
  </main>
"""

def get_terms_html() -> str:
    return """
  <main class="flex-1 max-w-3xl mx-auto px-4 py-8 w-full">
    <div class="mb-6">
      <a href="/" class="text-xs text-indigo-400 hover:underline inline-flex items-center space-x-1 mb-2">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Downloader</span>
      </a>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-white">Terms of Service</h1>
      <p class="text-xs sm:text-sm text-slate-400 mt-1">Effective Date: October 2026 &bull; User Agreement</p>
    </div>

    <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
      <div>
        <h2 class="text-base font-bold text-white mb-1">1. Acceptance of Terms</h2>
        <p>
          By accessing and using GI LINK, you acknowledge and agree to comply with these Terms of Service. If you do not agree with any portion of these terms, you must discontinue use immediately.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">2. Permitted &amp; Lawful Use</h2>
        <p>
          GI LINK is provided solely for personal, non-commercial, educational, and fair-use archiving purposes. Users are strictly responsible for:
        </p>
        <ul class="list-disc list-inside space-y-1 text-slate-400 pl-1 mt-1">
          <li>Ensuring you own the media or possess written authorization from the copyright holder.</li>
          <li>Complying with copyright legislation applicable in your jurisdiction.</li>
          <li>Refraining from downloading commercial copyrighted movies, broadcast music, or protected works without explicit licenses.</li>
        </ul>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">3. Non-Hosting &amp; Technical Intermediary Disclosure</h2>
        <p>
          GI LINK functions strictly as a client-side proxy tool utilizing open-source format extraction libraries. We do not host, broadcast, archive, or duplicate media files on our infrastructure. All video content resides on third-party servers outside of our control.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">4. Disclaimer of Warranties</h2>
        <p>
          The service is provided on an "AS IS" and "AS AVAILABLE" basis without warranties of any kind. GI LINK does not guarantee continuous uptime, error-free operation, or uninterrupted compatibility with third-party social media platforms.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">5. Limitation of Liability</h2>
        <p>
          In no event shall GI LINK, its developer Ghalib Kamal, or its hosting providers be liable for damages resulting from user misuse, unauthorized media duplication, or violation of third-party platform terms.
        </p>
      </div>
    </div>
  </main>
"""

def get_dmca_html() -> str:
    return """
  <main class="flex-1 max-w-3xl mx-auto px-4 py-8 w-full">
    <div class="mb-6">
      <a href="/" class="text-xs text-indigo-400 hover:underline inline-flex items-center space-x-1 mb-2">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Downloader</span>
      </a>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-white">DMCA &amp; Copyright Policy</h1>
      <p class="text-xs sm:text-sm text-slate-400 mt-1">Digital Millennium Copyright Act Notice &amp; Takedown Procedure</p>
    </div>

    <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
      <div>
        <h2 class="text-base font-bold text-white mb-1">1. Respect for Intellectual Property</h2>
        <p>
          GI LINK respects the intellectual property rights of content creators, artists, and rights holders. We comply fully with the Digital Millennium Copyright Act (17 U.S.C. &sect; 512) and international copyright directives.
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">2. Non-Hosting Safe Harbor Statement</h2>
        <p>
          <strong>GI LINK DOES NOT HOST ANY FILES OR VIDEOS.</strong><br/>
          All media processed through GI LINK is retrieved directly from the public third-party URL supplied by the user. Our servers never keep, catalog, or index downloaded media. Because no files are stored on our servers, removing content from GI LINK does not remove it from the hosting platform (e.g., YouTube, Instagram, or TikTok).
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">3. Domain / Link Blocking Requests</h2>
        <p>
          If you are a copyright owner or authorized representative and wish to request the blocking of specific domains or URL patterns from being processed through the GI LINK extractor, please submit a notice containing:
        </p>
        <ul class="list-disc list-inside space-y-1 text-slate-400 pl-1 mt-1">
          <li>Identification of the copyrighted work claimed to have been infringed.</li>
          <li>Exact URLs of the material you wish to block from our proxy pipeline.</li>
          <li>Your contact information including name, organization, email, and phone number.</li>
          <li>A statement made under penalty of perjury that you are authorized to act on behalf of the owner.</li>
        </ul>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <h2 class="text-base font-bold text-white mb-1">4. Designated Contact</h2>
        <p>
          Copyright notices and takedown inquiries should be directed to our designated administrator via our <a href="/contact" class="text-indigo-400 hover:underline">Contact Page</a>. We review and process verified requests promptly.
        </p>
      </div>
    </div>
  </main>
"""

def get_contact_html() -> str:
    return """
  <main class="flex-1 max-w-3xl mx-auto px-4 py-8 w-full">
    <div class="mb-6">
      <a href="/" class="text-xs text-indigo-400 hover:underline inline-flex items-center space-x-1 mb-2">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Downloader</span>
      </a>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-white">Contact GI LINK</h1>
      <p class="text-xs sm:text-sm text-slate-400 mt-1">Feedback, bug reports, feature requests, and partnership inquiries</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3 text-xs sm:text-sm text-slate-300">
        <h2 class="text-base font-bold text-white mb-1 flex items-center space-x-2">
          <i data-lucide="mail" class="w-4 h-4 text-indigo-400"></i>
          <span>Direct Inquiries</span>
        </h2>
        <p class="text-slate-400 leading-relaxed">
          Have questions, technical suggestions, or identified an extractor issue with a specific platform? Reach out directly to the maintainer.
        </p>
        <div class="pt-2 space-y-2 text-xs">
          <div class="flex items-center space-x-2">
            <span class="text-slate-500 font-medium w-16">Developer:</span>
            <span class="text-white font-semibold">Ghalib Kamal</span>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-slate-500 font-medium w-16">GitHub:</span>
            <a href="https://github.com/ghalibkamal7/gilink" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:underline">ghalibkamal7/gilink</a>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-slate-500 font-medium w-16">Project:</span>
            <span class="text-slate-300">GI LINK Media Downloader</span>
          </div>
        </div>
      </div>

      <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3 text-xs sm:text-sm text-slate-300">
        <h2 class="text-base font-bold text-white mb-1 flex items-center space-x-2">
          <i data-lucide="message-square" class="w-4 h-4 text-purple-400"></i>
          <span>Send Feedback</span>
        </h2>
        <form class="space-y-2.5" onsubmit="event.preventDefault(); alert('Thank you for reaching out! We will review your message.'); this.reset();">
          <div>
            <label class="block text-[11px] font-semibold text-slate-400 mb-1" for="contactName">Your Name</label>
            <input id="contactName" type="text" required placeholder="Ghalib..." class="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-slate-100 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-400 mb-1" for="contactEmail">Your Email</label>
            <input id="contactEmail" type="email" required placeholder="name@example.com" class="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-slate-100 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-400 mb-1" for="contactMessage">Message / Report</label>
            <textarea id="contactMessage" rows="3" required placeholder="Describe your issue or suggestion..." class="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-slate-100 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"></textarea>
          </div>
          <button type="submit" class="w-full py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs rounded-lg shadow transition">
            Submit Message
          </button>
        </form>
      </div>
    </div>
  </main>
"""


# ==============================================================================
# JAVASCRIPT LOGIC FOR HOMEPAGE
# ==============================================================================

HOME_SCRIPTS = """
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
        if (!data.success) throw new Error(data.error || 'Failed to retrieve media details.');
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

        let filename = 'media_download.mp4';
        const disposition = res.headers.get('content-disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
          const matches = /filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/.exec(disposition);
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

    if (urlForm) urlForm.addEventListener('submit', (e) => { e.preventDefault(); fetchMedia(); });

    if (pasteBtn) {
      pasteBtn.addEventListener('click', async () => {
        try {
          const text = await navigator.clipboard.readText();
          if (text) {
            urlInput.value = text;
            if (clearBtn) clearBtn.style.display = 'block';
          }
        } catch (_) {}
      });
    }

    if (urlInput) {
      urlInput.addEventListener('input', () => {
        if (clearBtn) clearBtn.style.display = urlInput.value ? 'block' : 'none';
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        urlInput.value = '';
        clearBtn.style.display = 'none';
      });
    }

    if (historyBtn && historyModal) historyBtn.addEventListener('click', () => historyModal.classList.remove('hidden'));
    if (closeHistoryBtn && historyModal) closeHistoryBtn.addEventListener('click', () => historyModal.classList.add('hidden'));
    if (clearHistoryBtn && historyList) clearHistoryBtn.addEventListener('click', () => { historyList.innerHTML = ''; });

    if (typeof lucide !== 'undefined') lucide.createIcons();
  });

  // --- PWA Service Worker & Install Prompt ---
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }

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
"""

SUBPAGE_SCRIPTS = """
  <script>
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
  </script>
"""
