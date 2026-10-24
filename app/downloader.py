import os
import re
import uuid
import tempfile
import shutil
from typing import Dict, Any, List, Optional
import yt_dlp

# Use /tmp for downloads (works on Vercel's read-only filesystem)
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "omnidrop_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def has_ffmpeg() -> bool:
    """Check if ffmpeg is available in system PATH."""
    return shutil.which("ffmpeg") is not None

def get_cookies_filepath() -> Optional[str]:
    """
    Checks for Instagram/Social cookies from Environment Variable or local file.
    Writes env var content to /tmp/cookies.txt if present.
    """
    env_cookies = os.environ.get("INSTAGRAM_COOKIES") or os.environ.get("COOKIES_TXT")
    if env_cookies and env_cookies.strip():
        cookie_path = os.path.join(tempfile.gettempdir(), "omnidrop_cookies.txt")
        try:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(env_cookies.strip())
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

def get_media_info(url: str) -> Dict[str, Any]:
    """Extract metadata and available qualities for a given URL."""
    ydl_opts: Dict[str, Any] = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
    }

    # Pass cookies if available (required for Instagram on cloud datacenters)
    cookie_file = get_cookies_filepath()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            err_msg = str(e)
            if "Instagram sent an empty media response" in err_msg and not cookie_file:
                raise ValueError("Instagram requires cookies on cloud server. Please configure INSTAGRAM_COOKIES in Vercel environment variables.")
            raise ValueError(f"Media fetch failed: {err_msg}")

        if not info:
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
    }

    # Pass cookies if available
    cookie_file = get_cookies_filepath()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

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
            # Fallback to standalone single stream format (does not require ffmpeg merge)
            clean_format = format_spec.replace("bestvideo+bestaudio/", "")
            if "+" in clean_format:
                clean_format = "best"
            ydl_opts['format'] = clean_format or 'best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            # If specified format failed (e.g. ffmpeg missing error), retry with safest 'best'
            if "ffmpeg" in str(e).lower() or "merge" in str(e).lower() or "requested format" in str(e).lower():
                ydl_opts.pop('merge_output_format', None)
                ydl_opts.pop('postprocessors', None)
                ydl_opts['format'] = 'best'
                with yt_dlp.YoutubeDL(ydl_opts) as retry_ydl:
                    info = retry_ydl.extract_info(url, download=True)
            else:
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
            raise FileNotFoundError("Downloaded file could not be located.")

        clean_name = os.path.basename(filename)
        # Strip req_id prefix from downloaded filename for user-friendly name
        display_name = clean_name.replace(f"{req_id}_", "")

        return {
            "filepath": filename,
            "filename": display_name,
            "filesize": os.path.getsize(filename)
        }
