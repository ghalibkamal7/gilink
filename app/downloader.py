import os
import re
import uuid
import tempfile
import shutil
from typing import Dict, Any, List, Optional
import requests
import yt_dlp

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

# Use /tmp for downloads (works on Vercel's read-only filesystem)
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "omnidrop_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def has_ffmpeg() -> bool:
    """Check if ffmpeg is available in system PATH."""
    return shutil.which("ffmpeg") is not None

def parse_cookie_data(raw: str, default_domain: str = ".youtube.com") -> List[str]:
    """Parse cookie string (either full Netscape format or key=value header format) into Netscape lines."""
    lines: List[str] = []
    raw_lines = raw.strip().splitlines()
    has_netscape_header = any("Netscape HTTP Cookie File" in l for l in raw_lines)
    has_tabs = any("\t" in l for l in raw_lines if not l.strip().startswith("#"))

    if has_netscape_header or has_tabs:
        for line in raw_lines:
            l = line.strip()
            if l and not l.startswith("#"):
                lines.append(l)
    else:
        # Header string: name=value; name2=value2
        tokens = []
        for line in raw_lines:
            for part in line.split(";"):
                p = part.strip()
                if "=" in p:
                    lower = p.lower()
                    if not lower.startswith("path=") and not lower.startswith("domain=") and not lower.startswith("expires="):
                        tokens.append(p)
        for token in tokens:
            if "=" in token:
                name, val = token.split("=", 1)
                name, val = name.strip(), val.strip()
                if name and val:
                    lines.append(f"{default_domain}\tTRUE\t/\tFALSE\t2147483647\t{name}\t{val}")
    return lines

def get_cookies_filepath() -> Optional[str]:
    """Retrieve cookies for platforms that require them (Instagram, YouTube, etc.).
    Combines cookies from YOUTUBE_COOKIES, INSTAGRAM_COOKIES, and COOKIES_TXT.
    """
    all_cookie_lines: List[str] = []

    # 1. YouTube cookies
    yt_c = os.environ.get("YOUTUBE_COOKIES")
    if yt_c and yt_c.strip():
        all_cookie_lines.extend(parse_cookie_data(yt_c.strip(), default_domain=".youtube.com"))

    # 2. Instagram cookies
    ig_c = os.environ.get("INSTAGRAM_COOKIES")
    if ig_c and ig_c.strip():
        all_cookie_lines.extend(parse_cookie_data(ig_c.strip(), default_domain=".instagram.com"))

    # 3. Generic cookies
    gen_c = os.environ.get("COOKIES_TXT")
    if gen_c and gen_c.strip():
        all_cookie_lines.extend(parse_cookie_data(gen_c.strip(), default_domain=".youtube.com"))

    if all_cookie_lines:
        cookie_path = os.path.join(tempfile.gettempdir(), "omnidrop_cookies.txt")
        try:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("\n".join(all_cookie_lines) + "\n")
            return cookie_path
        except Exception as e:
            print(f"Error writing cookies file: {e}")
            return None

    # Fallback to local cookies.txt file if present in repo
    local_cookie = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
    if os.path.exists(local_cookie):
        return local_cookie

    return None

def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filenames."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean[:80].strip() or "media_download"

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    elif "instagram.com" in url_lower:
        return "Instagram"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "Facebook"
    elif "tiktok.com" in url_lower:
        return "TikTok"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "X (Twitter)"
    elif "reddit.com" in url_lower or "redd.it" in url_lower:
        return "Reddit"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "Pinterest"
    elif "soundcloud.com" in url_lower:
        return "SoundCloud"
    elif "vimeo.com" in url_lower:
        return "Vimeo"
    return "Universal Media"

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_filesize(bytes_val: Optional[int]) -> str:
    if not bytes_val:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def extract_youtube_fallback(url: str) -> Optional[Dict[str, Any]]:
    """Fallback YouTube extractor via reliable Invidious nodes if yt-dlp encounters cloud bot protection."""
    vid_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if not vid_match:
        return None
    video_id = vid_match.group(1)
    instances = [
        'https://yt.chocolatemoo53.com',
        'https://invidious.nerdvpn.de',
        'https://inv.nadeko.net'
    ]
    for inst in instances:
        try:
            r = requests.get(f'{inst}/api/v1/videos/{video_id}', timeout=4)
            if r.status_code == 200:
                data = r.json()
                title = data.get('title') or "YouTube Video"
                duration = format_duration(data.get('lengthSeconds'))
                uploader = data.get('author') or "YouTube Creator"
                thumbs = data.get('videoThumbnails') or []
                thumbnail = thumbs[-1].get('url') if thumbs else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                if thumbnail.startswith("/"):
                    thumbnail = f"https://i.ytimg.com{thumbnail}"
                
                presets = [
                    {"id": "best", "name": "Best Quality (HD)", "ext": "mp4", "badge": "Fast"},
                    {"id": "best[height<=720]/best", "name": "720p HD", "ext": "mp4", "badge": "720p"},
                    {"id": "best[height<=480]/best", "name": "480p SD", "ext": "mp4", "badge": "480p"},
                    {"id": "bestaudio/best", "name": "Audio Only", "ext": "mp3", "badge": "Audio"}
                ]
                return {
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration,
                    "uploader": uploader,
                    "platform": "YouTube",
                    "url": url,
                    "presets": presets,
                    "formats": [
                        {"id": "best", "quality": "HD (720p/360p)", "height": 720, "ext": "mp4", "size": "Auto", "type": "video"}
                    ],
                    "audio_formats": [
                        {"id": "bestaudio", "quality": "128 kbps", "ext": "mp3", "size": "Auto", "type": "audio"}
                    ]
                }
        except Exception:
            continue
    return None

def download_youtube_fallback(url: str, req_id: str) -> Optional[Dict[str, Any]]:
    """Fallback YouTube stream downloader if cloud datacenter IPs are blocked."""
    vid_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if not vid_match:
        return None
    video_id = vid_match.group(1)
    instances = [
        'https://yt.chocolatemoo53.com',
        'https://invidious.nerdvpn.de',
        'https://inv.nadeko.net'
    ]
    for inst in instances:
        try:
            r = requests.get(f'{inst}/api/v1/videos/{video_id}', timeout=4)
            if r.status_code == 200:
                data = r.json()
                title = data.get('title') or "YouTube_Media"
                streams = data.get('formatStreams') or []
                if streams:
                    dl_url = streams[0].get('url')
                    if dl_url:
                        safe_title = sanitize_filename(title)
                        target_file = os.path.join(DOWNLOAD_DIR, f"{req_id}_{safe_title}.mp4")
                        with requests.get(dl_url, stream=True, timeout=20) as resp:
                            if resp.status_code == 200:
                                with open(target_file, 'wb') as f:
                                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                                        if chunk:
                                            f.write(chunk)
                                return {
                                    "filepath": target_file,
                                    "filename": f"{safe_title}.mp4",
                                    "filesize": os.path.getsize(target_file)
                                }
        except Exception:
            continue
    return None

def get_media_info(url: str) -> Dict[str, Any]:
    """Extract metadata and available qualities for a given URL."""
    ydl_opts: Dict[str, Any] = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }

    # Pass cookies if available (required for Instagram/YouTube on cloud datacenters)
    cookie_file = get_cookies_filepath()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    proxy = os.environ.get("YOUTUBE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy and proxy.strip():
        ydl_opts['proxy'] = proxy.strip()

    info = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            err_msg = str(e)
            # Automatic fallback for YouTube if cloud IP is challenged
            if detect_platform(url) == "YouTube":
                fallback = extract_youtube_fallback(url)
                if fallback:
                    return fallback
            if "Instagram sent an empty media response" in err_msg and not cookie_file:
                raise ValueError("Instagram requires cookies on cloud server. Please configure INSTAGRAM_COOKIES in Vercel environment variables.")
            if ("Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm" in err_msg):
                raise ValueError("YouTube Bot Protection triggered on cloud server. Please export cookies from YouTube, set YOUTUBE_COOKIES in Vercel Environment Variables, and Redeploy in Vercel.")
            raise ValueError(f"Media fetch failed: {err_msg}")

        if not info:
            if detect_platform(url) == "YouTube":
                fallback = extract_youtube_fallback(url)
                if fallback:
                    return fallback
            raise ValueError("Could not retrieve media details.")

        # If it's a playlist or multiple entries, pick the first
        if 'entries' in info and info['entries']:
            entry = info['entries'][0]
            if entry:
                info = entry

        title = info.get('title') or "Untitled Media"
        thumbnail = info.get('thumbnail') or ""
        duration = format_duration(info.get('duration'))
        uploader = info.get('uploader') or info.get('channel') or info.get('creator') or "Unknown Creator"
        platform = detect_platform(url)

        # Parse formats
        raw_formats = info.get('formats', [])
        video_options: List[Dict[str, Any]] = []
        audio_options: List[Dict[str, Any]] = []

        seen_resolutions = set()
        
        # Sort formats by resolution / quality
        for f in raw_formats:
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            height = f.get('height')
            ext = f.get('ext', 'mp4')
            filesize = f.get('filesize') or f.get('filesize_approx')

            # Video streams
            if vcodec != 'none' and height:
                res_key = f"{height}p"
                if res_key not in seen_resolutions:
                    seen_resolutions.add(res_key)
                    video_options.append({
                        "id": f.get('format_id'),
                        "quality": res_key,
                        "height": height,
                        "ext": ext if ext in ['mp4', 'webm'] else 'mp4',
                        "size": format_filesize(filesize),
                        "type": "video"
                    })

            # Audio-only streams
            elif vcodec == 'none' and acodec != 'none':
                abr = f.get('abr') or f.get('tbr')
                abr_str = f"{int(abr)} kbps" if abr else "Audio"
                audio_options.append({
                    "id": f.get('format_id'),
                    "quality": abr_str,
                    "ext": "mp3",
                    "size": format_filesize(filesize),
                    "type": "audio"
                })

        # Sort video options descending by height
        video_options.sort(key=lambda x: x['height'], reverse=True)

        # If no explicit format was extracted (like direct video or simple sites)
        if not video_options and not audio_options:
            video_options.append({
                "id": "best",
                "quality": "Best Quality",
                "height": 1080,
                "ext": "mp4",
                "size": "Auto",
                "type": "video"
            })

        # Safe presets that always work (with or without ffmpeg)
        presets = [
            {"id": "best", "name": "Best Quality (HD)", "ext": "mp4", "badge": "Fast"},
            {"id": "best[height<=720]/best", "name": "720p HD", "ext": "mp4", "badge": "720p"},
            {"id": "best[height<=480]/best", "name": "480p SD", "ext": "mp4", "badge": "480p"},
            {"id": "bestaudio/best", "name": "Audio Only", "ext": "mp3", "badge": "Audio"}
        ]

        return {
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "uploader": uploader,
            "platform": platform,
            "url": url,
            "presets": presets,
            "formats": video_options[:4],
            "audio_formats": audio_options[:2]
        }

def download_media(url: str, format_spec: str, is_audio: bool = False) -> Dict[str, Any]:
    """Download the media file to the downloads directory and return filepath."""
    req_id = uuid.uuid4().hex[:8]
    out_template = os.path.join(DOWNLOAD_DIR, f"{req_id}_%(title).50s.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        'outtmpl': out_template,
        'quiet': False,
        'no_warnings': True,
        'restrictfilenames': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }

    # Pass cookies if available
    cookie_file = get_cookies_filepath()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    proxy = os.environ.get("YOUTUBE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy and proxy.strip():
        ydl_opts['proxy'] = proxy.strip()

    ffmpeg_available = has_ffmpeg()

    if is_audio:
        if ffmpeg_available:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Fallback when ffmpeg is not available: extract direct bestaudio without transcoding
            ydl_opts['format'] = 'bestaudio/best'
    else:
        # If ffmpeg is present, allow bestvideo+bestaudio merging, else use pre-merged progressive stream
        if ffmpeg_available and ("+" in format_spec):
            ydl_opts['format'] = format_spec
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            # Fallback to single stream with progressive audio+video fallback
            clean_format = format_spec.replace("bestvideo+bestaudio/", "")
            if "+" in clean_format or clean_format == "best":
                # Prefer progressive streams containing both audio and video (format 18 is YouTube's reliable standard)
                ydl_opts['format'] = '18/best[vcodec!=none][acodec!=none]/best/b'
            elif "height<=720" in clean_format:
                ydl_opts['format'] = 'best[height<=720][acodec!=none]/18/best[acodec!=none]/best'
            elif "height<=480" in clean_format:
                ydl_opts['format'] = 'best[height<=480][acodec!=none]/18/best[acodec!=none]/best'
            else:
                ydl_opts['format'] = f"{clean_format}/best[acodec!=none]/18/best/b"

    info = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            # If specified format failed (e.g. ffmpeg missing error), retry with safest progressive format
            if "ffmpeg" in str(e).lower() or "merge" in str(e).lower() or "requested format" in str(e).lower():
                ydl_opts.pop('merge_output_format', None)
                ydl_opts.pop('postprocessors', None)
                if is_audio:
                    ydl_opts['format'] = 'bestaudio/best'
                else:
                    ydl_opts['format'] = '18/best[acodec!=none]/best/b'
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as retry_ydl:
                        info = retry_ydl.extract_info(url, download=True)
                except Exception:
                    pass

            # If yt-dlp failed completely on YouTube, attempt direct Invidious stream download
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id)
                if yt_fallback:
                    return yt_fallback

            if not info:
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id)
                    if yt_fallback:
                        return yt_fallback
                raise e

        filename = ydl.prepare_filename(info)
        
        # If audio conversion changed ext to mp3
        if is_audio:
            base, _ = os.path.splitext(filename)
            mp3_candidate = f"{base}.mp3"
            if os.path.exists(mp3_candidate):
                filename = mp3_candidate

        # In case merge output changed ext to mp4
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            mp4_candidate = f"{base}.mp4"
            if os.path.exists(mp4_candidate):
                filename = mp4_candidate

        if not os.path.exists(filename):
            # Scan directory for matching file with req_id
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(req_id):
                    filename = os.path.join(DOWNLOAD_DIR, f)
                    break

        if not os.path.exists(filename):
            if detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id)
                if yt_fallback:
                    return yt_fallback
            raise FileNotFoundError("Downloaded file could not be located.")

        clean_name = os.path.basename(filename)
        # Strip req_id prefix from downloaded filename for user-friendly name
        display_name = clean_name.replace(f"{req_id}_", "")

        return {
            "filepath": filename,
            "filename": display_name,
            "filesize": os.path.getsize(filename)
        }
