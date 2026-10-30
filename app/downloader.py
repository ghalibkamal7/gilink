import os
import re
import uuid
import tempfile
import shutil
import urllib.parse
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
            err_msg = str(e)
            platform = detect_platform(url)
            # Instagram authentication required error handling – try without cookies first
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                # Remove cookiefile if it was set and retry with a generic best format
                ydl_opts.pop('cookiefile', None)
                ydl_opts['format'] = 'best'
                # Remove any postprocessors that could cause failures for video download
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception as retry_err:
                    # If still fails, raise a clear error prompting the user to add cookies
                    raise ValueError(
                        "Instagram download still failed after retry without cookies. "
                        "Please provide valid INSTAGRAM_COOKIES environment variable."
                    ) from retry_err
                # If retry succeeded, continue processing as normal
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            err_msg = str(e)
            platform = detect_platform(url)
            # Instagram authentication required error handling
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                raise ValueError(
                    "Instagram download failed: missing or invalid cookies. "
                    "Set the INSTAGRAM_COOKIES environment variable with a valid session cookie and redeploy."
                )
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any existing postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                # Reset format to best available and retry download without metadata processing
                ydl_opts['format'] = 'best'
                # Remove postprocessors to avoid ffmpeg errors if not needed
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            print(f"Error writing cookies file: {e}")
            return None

    # Fallback to local cookies.txt file if present in repo
    local_cookie = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
    if os.path.exists(local_cookie):
        return local_cookie

    return None

def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filenames and Latin-1 HTTP response headers."""
    clean = re.sub(r'[^\w\s.-]', '_', name)
    clean = clean.encode('ascii', 'ignore').decode('ascii')
    clean = re.sub(r'\s+', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:60] or "media_download"

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
                    {"id": "best", "name": "Best Quality (Video + Audio)", "ext": "mp4", "badge": "Full"},
                    {"id": "18", "name": "Standard (360p + Audio)", "ext": "mp4", "badge": "Fast"},
                    {"id": "bestaudio/best", "name": "Audio Only (MP3)", "ext": "mp3", "badge": "Audio"}
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
                        {"id": "best", "quality": "HD (Video + Audio)", "height": 720, "ext": "mp4", "size": "Auto", "type": "video"}
                    ],
                    "audio_formats": [
                        {"id": "bestaudio", "quality": "128 kbps", "ext": "mp3", "size": "Auto", "type": "audio"}
                    ]
                }
        except Exception:
            continue

    # Second fallback: Official YouTube oEmbed API (100% reliable, zero bot-detection)
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        oe_resp = requests.get(oembed_url, timeout=4)
        if oe_resp.status_code == 200:
            oe_data = oe_resp.json()
            title = oe_data.get("title") or "YouTube Video"
            uploader = oe_data.get("author_name") or "YouTube Creator"
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            presets = [
                {"id": "best", "name": "Best Quality (Video + Audio)", "ext": "mp4", "badge": "Full"},
                {"id": "18", "name": "Standard (360p + Audio)", "ext": "mp4", "badge": "Fast"},
                {"id": "bestaudio/best", "name": "Audio Only (MP3)", "ext": "mp3", "badge": "Audio"}
            ]
            return {
                "title": title,
                "thumbnail": thumbnail,
                "duration": "",
                "uploader": uploader,
                "platform": "YouTube",
                "url": url,
                "presets": presets,
                "formats": [
                    {"id": "best", "quality": "HD (Video + Audio)", "height": 720, "ext": "mp4", "size": "Auto", "type": "video"}
                ],
                "audio_formats": [
                    {"id": "bestaudio", "quality": "128 kbps", "ext": "mp3", "size": "Auto", "type": "audio"}
                ]
            }
    except Exception:
        pass

    return None

def _extract_height(stream_dict: Dict[str, Any]) -> int:
    """Helper to extract vertical resolution integer from stream metadata."""
    lbl = str(stream_dict.get('qualityLabel') or stream_dict.get('resolution') or '')
    m = re.search(r'(\d+)', lbl)
    if m:
        return int(m.group(1))
    size = str(stream_dict.get('size') or '')
    m = re.search(r'x(\d+)', size)
    if m:
        return int(m.group(1))
    return 0

def _is_url_expired(url_str: str) -> bool:
    """Check if a YouTube videoplayback URL has expired by examining its 'expire' parameter."""
    import time
    try:
        parsed = urllib.parse.urlparse(url_str)
        params = urllib.parse.parse_qs(parsed.query)
        expire_vals = params.get('expire', [])
        if expire_vals:
            expire_ts = int(expire_vals[0])
            # Consider expired if less than 30 seconds remaining
            return expire_ts < (time.time() + 30)
    except Exception:
        pass
    return False


def get_youtube_direct_stream(url: str, is_audio: bool = False, format_spec: str = "best") -> Optional[Dict[str, Any]]:
    """Return an instant streaming proxy URL for YouTube with optimal quality selection.
    
    Priority order:
    1. yt-dlp with android/ios/tv mobile clients (most reliable on cloud, fresh URLs for this IP)
    2. Invidious proxy (only if yt-dlp fails, uses instance's /videoplayback proxy endpoint)
    """
    vid_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if not vid_match:
        return None
    video_id = vid_match.group(1)

    target_height = 9999
    if '1080' in format_spec:
        target_height = 1080
    elif '720' in format_spec:
        target_height = 720
    elif '480' in format_spec:
        target_height = 480
    elif '360' in format_spec:
        target_height = 360

    # --- PRIMARY: yt-dlp mobile client extraction (URLs are fresh & bound to this server's IP) ---
    try:
        y_opts = {
            'quiet': True,
            'skip_download': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'tv']
                }
            }
        }
        cookie_file = get_cookies_filepath()
        if cookie_file:
            y_opts['cookiefile'] = cookie_file
        with yt_dlp.YoutubeDL(y_opts) as ydl:
            yt_info = ydl.extract_info(url, download=False)
            if yt_info:
                title = sanitize_filename(yt_info.get('title') or "YouTube_Media")
                formats = [f for f in yt_info.get('formats', []) if f.get('url') and not _is_url_expired(f['url'])]
                if is_audio:
                    audio_fs = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                    if not audio_fs:
                        audio_fs = formats
                    audio_fs.sort(key=lambda f: f.get('abr') or f.get('tbr') or 0, reverse=True)
                    if audio_fs:
                        chosen = audio_fs[0]
                        return {
                            "stream_url": chosen['url'],
                            "filename": f"{title}.mp3",
                            "media_type": "audio/mpeg",
                            "content_length": chosen.get('filesize') or chosen.get('filesize_approx')
                        }
                else:
                    video_fs = [f for f in formats if f.get('vcodec') != 'none']
                    if video_fs:
                        # STRICT REQUIREMENT: Video MUST contain audio (progressive stream)
                        prog_fs = [f for f in video_fs if f.get('acodec') and f.get('acodec') != 'none']
                        if prog_fs:
                            prog_fs.sort(key=lambda f: f.get('height') or 0, reverse=True)
                            matching = [f for f in prog_fs if (f.get('height') or 0) <= target_height]
                            chosen = matching[0] if matching else prog_fs[0]
                            return {
                                "stream_url": chosen['url'],
                                "filename": f"{title}.mp4",
                                "media_type": "video/mp4",
                                "content_length": chosen.get('filesize') or chosen.get('filesize_approx')
                            }
    except Exception as e:
        print(f"yt-dlp direct stream extraction error: {e}")

    # --- FALLBACK: Invidious proxy (progressive streams ONLY, never silent adaptive formats) ---
    instances = [
        'https://yt.chocolatemoo53.com',
        'https://invidious.nerdvpn.de',
        'https://inv.nadeko.net'
    ]
    for inst in instances:
        try:
            r = requests.get(f'{inst}/api/v1/videos/{video_id}', timeout=5)
            if r.status_code == 200:
                data = r.json()
                title = sanitize_filename(data.get('title') or "YouTube_Media")
                streams = data.get('formatStreams') or []
                adaptive = data.get('adaptiveFormats') or []

                if is_audio:
                    audio_candidates = [a for a in adaptive if 'audio/' in a.get('type', '') and a.get('url')]
                    if audio_candidates:
                        audio_candidates.sort(
                            key=lambda a: int(a.get('bitrate') or 0) + (1000000 if 'audio/mp4' in a.get('type', '') else 0),
                            reverse=True
                        )
                        chosen_audio = audio_candidates[0]
                        parsed = urllib.parse.urlparse(chosen_audio['url'])
                        proxy_url = f"{inst}/videoplayback?{parsed.query}"
                        try:
                            check = requests.head(proxy_url, timeout=5, allow_redirects=True)
                            if check.status_code >= 400:
                                continue
                        except Exception:
                            continue
                        clen = chosen_audio.get('clen')
                        return {
                            "stream_url": proxy_url,
                            "filename": f"{title}.mp3",
                            "media_type": "audio/mpeg",
                            "content_length": int(clen) if clen else None
                        }
                else:
                    # ONLY progressive streams (pre-muxed audio & video). NEVER return silent adaptive streams!
                    if streams:
                        streams.sort(key=_extract_height, reverse=True)
                        matching = [s for s in streams if _extract_height(s) <= target_height]
                        chosen_stream = matching[0] if matching else streams[0]
                        s_url = chosen_stream.get('url')
                        if s_url:
                            parsed = urllib.parse.urlparse(s_url)
                            proxy_url = f"{inst}/videoplayback?{parsed.query}"
                            try:
                                check = requests.head(proxy_url, timeout=5, allow_redirects=True)
                                if check.status_code >= 400:
                                    continue
                            except Exception:
                                continue
                            clen = chosen_stream.get('clen')
                            return {
                                "stream_url": proxy_url,
                                "filename": f"{title}.mp4",
                                "media_type": "video/mp4",
                                "content_length": int(clen) if clen else None
                            }
        except Exception:
            continue

    return None

def download_youtube_fallback(url: str, req_id: str, is_audio: bool = False) -> Optional[Dict[str, Any]]:
    """Fallback YouTube stream downloader with progressive stream support & audio/video muxing."""
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
            r = requests.get(f'{inst}/api/v1/videos/{video_id}', timeout=5)
            if r.status_code == 200:
                data = r.json()
                title = sanitize_filename(data.get('title') or "YouTube_Media")
                streams = data.get('formatStreams') or []
                adaptive = data.get('adaptiveFormats') or []

                # 1. Audio-only download
                if is_audio:
                    a_url = next((a.get('url') for a in adaptive if 'audio/mp4' in a.get('type', '') and a.get('url')), None)
                    if not a_url:
                        a_url = next((a.get('url') for a in adaptive if 'audio/' in a.get('type', '') and a.get('url')), None)
                    if a_url:
                        target = os.path.join(DOWNLOAD_DIR, f'{req_id}_{title}.mp3')
                        with requests.get(a_url, stream=True, timeout=25) as resp:
                            if resp.status_code == 200:
                                with open(target, 'wb') as f:
                                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                                        if chunk:
                                            f.write(chunk)
                                if os.path.exists(target) and os.path.getsize(target) > 0:
                                    return {'filepath': target, 'filename': f'{title}.mp3', 'filesize': os.path.getsize(target)}
                                else:
                                    try: os.remove(target)
                                    except Exception: pass

                # 2. Progressive stream (single file with video + audio)
                if streams and not is_audio:
                    dl_url = streams[0].get('url')
                    if dl_url:
                        target = os.path.join(DOWNLOAD_DIR, f"{req_id}_{title}.mp4")
                        with requests.get(dl_url, stream=True, timeout=25) as resp:
                            if resp.status_code == 200:
                                with open(target, 'wb') as f:
                                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                                        if chunk:
                                            f.write(chunk)
                                if os.path.exists(target) and os.path.getsize(target) > 0:
                                    return {
                                        "filepath": target,
                                        "filename": f"{title}.mp4",
                                        "filesize": os.path.getsize(target)
                                    }
                                else:
                                    try: os.remove(target)
                                    except Exception: pass

                # 3. Adaptive streams (separate video + audio muxed via ffmpeg)
                if adaptive and not is_audio:
                    v_url = next((a.get('url') for a in adaptive if 'video/mp4' in a.get('type', '') and a.get('url')), None)
                    a_url = next((a.get('url') for a in adaptive if 'audio/mp4' in a.get('type', '') and a.get('url')), None)
                    if v_url:
                        target = os.path.join(DOWNLOAD_DIR, f"{req_id}_{title}.mp4")
                        v_temp = os.path.join(DOWNLOAD_DIR, f"{req_id}_v.mp4")
                        with requests.get(v_url, stream=True, timeout=25) as resp:
                            if resp.status_code == 200:
                                with open(v_temp, 'wb') as f:
                                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                                        if chunk:
                                            f.write(chunk)
                        if a_url and has_ffmpeg():
                            a_temp = os.path.join(DOWNLOAD_DIR, f"{req_id}_a.m4a")
                            with requests.get(a_url, stream=True, timeout=25) as resp:
                                if resp.status_code == 200:
                                    with open(a_temp, 'wb') as f:
                                        for chunk in resp.iter_content(chunk_size=64 * 1024):
                                            if chunk:
                                                f.write(chunk)
                            try:
                                import subprocess
                                subprocess.run(['ffmpeg', '-y', '-i', v_temp, '-i', a_temp, '-c', 'copy', target], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                if os.path.exists(v_temp): os.remove(v_temp)
                                if os.path.exists(a_temp): os.remove(a_temp)
                            except Exception:
                                if os.path.exists(v_temp):
                                    try: os.remove(v_temp)
                                    except Exception: pass
                                if os.path.exists(a_temp):
                                    try: os.remove(a_temp)
                                    except Exception: pass
                                continue
                        else:
                            # Without ffmpeg, we cannot mux video and audio. Never return silent video!
                            if os.path.exists(v_temp):
                                try: os.remove(v_temp)
                                except Exception: pass
                            continue
                        if os.path.exists(target) and os.path.getsize(target) > 0:
                            return {
                                "filepath": target,
                                "filename": f"{title}.mp4",
                                "filesize": os.path.getsize(target)
                            }
                        else:
                            if os.path.exists(target):
                                try: os.remove(target)
                                except Exception: pass
                            if os.path.exists(v_temp):
                                try: os.remove(v_temp)
                                except Exception: pass
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
                'player_client': ['android', 'ios', 'tv']
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
            platform = detect_platform(url)
            # Instagram authentication required error handling – try without cookies first
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                # Remove cookiefile if it was set and retry with a generic best format
                ydl_opts.pop('cookiefile', None)
                ydl_opts['format'] = 'best'
                # Remove any postprocessors that could cause failures for video download
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception as retry_err:
                    # If still fails, raise a clear error prompting the user to add cookies
                    raise ValueError(
                        "Instagram download still failed after retry without cookies. "
                        "Please provide valid INSTAGRAM_COOKIES environment variable."
                    ) from retry_err
                # If retry succeeded, continue processing as normal
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            err_msg = str(e)
            platform = detect_platform(url)
            # Instagram authentication required error handling
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                raise ValueError(
                    "Instagram download failed: missing or invalid cookies. "
                    "Set the INSTAGRAM_COOKIES environment variable with a valid session cookie and redeploy."
                )
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any existing postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                # Reset format to best available and retry download without metadata processing
                ydl_opts['format'] = 'best'
                # Remove postprocessors to avoid ffmpeg errors if not needed
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            err_msg = str(e)
            # Automatic fallback for YouTube if cloud IP is challenged
            if detect_platform(url) == "YouTube":
                if 'cookiefile' in ydl_opts:
                    try:
                        safe_opts = dict(ydl_opts)
                        safe_opts.pop('cookiefile', None)
                        safe_opts['extractor_args'] = {'youtube': {'player_client': ['android', 'ios', 'tv']}}
                        with yt_dlp.YoutubeDL(safe_opts) as retry_ydl:
                            info = retry_ydl.extract_info(url, download=False)
                    except Exception:
                        pass
                if not info:
                    fallback = extract_youtube_fallback(url)
                    if fallback:
                        return fallback
            if "Instagram sent an empty media response" in err_msg and not cookie_file:
                raise ValueError("Instagram requires cookies on cloud server. Please configure INSTAGRAM_COOKIES in Vercel environment variables.")
            if ("Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm" in err_msg):
                fallback = extract_youtube_fallback(url)
                if fallback:
                    return fallback
                raise ValueError("YouTube Bot Protection triggered on cloud server. Please export cookies from YouTube, set YOUTUBE_COOKIES in Vercel Environment Variables, and Redeploy in Vercel.")
            if not info:
                fallback = extract_youtube_fallback(url)
                if fallback:
                    return fallback
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
        # Determine platform for special handling
    platform = detect_platform(url)
    if platform == "Instagram":
        # Instagram usually provides a combined video+audio stream; use the generic 'best' format.
        # This works for both video and audio (ffmpeg will extract audio when needed).
        if is_audio:
            if ffmpeg_available:
                ydl_opts['format'] = 'best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = 'best'
        else:
            if ffmpeg_available:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                ydl_opts['format'] = 'best'
        # Skip the generic YouTube/ffmpeg format logic below for Instagram
    else:
        # Existing logic for non‑Instagram platforms
        if is_audio:
            if ffmpeg_available:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = 'bestaudio/best'
        else:
            # If ffmpeg is present, allow bestvideo+bestaudio merging, else use pre‑merged progressive stream
            if ffmpeg_available and ("+" in format_spec):
                ydl_opts['format'] = format_spec
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                # Fallback to single progressive stream with audio (format 22 or 18)
                # STRICT: Always require [acodec!=none] so video always has audio!
                clean_format = format_spec.replace("bestvideo+bestaudio/", "").replace("/best", "").replace("/b", "")
                if "height<=720" in clean_format:
                    ydl_opts['format'] = '22/best[height<=720][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
                elif "height<=480" in clean_format:
                    ydl_opts['format'] = 'best[height<=480][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
                elif clean_format and clean_format != "best":
                    ydl_opts['format'] = f"{clean_format}[acodec!=none]/22/18/best[vcodec!=none][acodec!=none]"
                else:
                    ydl_opts['format'] = '22/18/best[vcodec!=none][acodec!=none]'


        seen_resolutions = set()
        
        # Sort formats by resolution / quality
        for f in raw_formats:
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            height = f.get('height')
            ext = f.get('ext', 'mp4')
            filesize = f.get('filesize') or f.get('filesize_approx')

            # Video streams (if no ffmpeg, only show formats that include audio)
            if vcodec != 'none' and height:
                if not ffmpeg_available and (not acodec or acodec == 'none'):
                    continue
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

        # Safe presets that always include sound (progressive audio+video)
        presets = [
            {"id": "best", "name": "Best Quality (Video + Audio)", "ext": "mp4", "badge": "Full"},
            {"id": "18", "name": "Standard (360p + Audio)", "ext": "mp4", "badge": "Fast"},
            {"id": "bestaudio/best", "name": "Audio Only (MP3)", "ext": "mp3", "badge": "Audio"}
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
                'player_client': ['android', 'ios', 'tv']
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

    # Determine platform for special handling
    platform = detect_platform(url)
    if platform == "Instagram":
        # Instagram usually provides a combined video+audio stream; use the generic 'best' format.
        # This works for both video and audio (ffmpeg will extract audio when needed).
        if is_audio:
            if ffmpeg_available:
                ydl_opts['format'] = 'best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = 'best'
        else:
            if ffmpeg_available:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                ydl_opts['format'] = 'best'
        # Skip the generic YouTube/ffmpeg format logic below for Instagram
    else:
        # Existing logic for non‑Instagram platforms
        if is_audio:
            if ffmpeg_available:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['format'] = 'bestaudio/best'
        else:
            # If ffmpeg is present, allow bestvideo+bestaudio merging, else use pre‑merged progressive stream
            if ffmpeg_available and ("+" in format_spec):
                ydl_opts['format'] = format_spec
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                # Fallback to single progressive stream with audio (format 22 or 18)
                # STRICT: Always require [acodec!=none] so video always has audio!
                clean_format = format_spec.replace("bestvideo+bestaudio/", "").replace("/best", "").replace("/b", "")
                if "height<=720" in clean_format:
                    ydl_opts['format'] = '22/best[height<=720][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
                elif "height<=480" in clean_format:
                    ydl_opts['format'] = 'best[height<=480][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
                elif clean_format and clean_format != "best":
                    ydl_opts['format'] = f"{clean_format}[acodec!=none]/22/18/best[vcodec!=none][acodec!=none]"
                else:
                    ydl_opts['format'] = '22/18/best[vcodec!=none][acodec!=none]'


    # Determine platform for special handling
    platform = detect_platform(url)
    if is_audio:
        if platform == "Instagram":
            # Instagram often provides combined video+audio; use best format and let ffmpeg extract audio
            if ffmpeg_available:
                ydl_opts['format'] = 'best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                # Without ffmpeg, download best and rely on client to handle MP4 (fallback)
                ydl_opts['format'] = 'best'
        else:
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
            # Fallback to single progressive stream with audio (format 22 or 18)
            # STRICT: Always require [acodec!=none] so video always has audio!
            clean_format = format_spec.replace("bestvideo+bestaudio/", "").replace("/best", "").replace("/b", "")
            if "height<=720" in clean_format:
                ydl_opts['format'] = '22/best[height<=720][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
            elif "height<=480" in clean_format:
                ydl_opts['format'] = 'best[height<=480][acodec!=none]/18/best[vcodec!=none][acodec!=none]'
            elif clean_format and clean_format != "best":
                ydl_opts['format'] = f"{clean_format}[acodec!=none]/22/18/best[vcodec!=none][acodec!=none]"
            else:
                ydl_opts['format'] = '22/18/best[vcodec!=none][acodec!=none]'

    info = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            err_msg = str(e)
            platform = detect_platform(url)
            # Instagram authentication required error handling – try without cookies first
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                # Remove cookiefile if it was set and retry with a generic best format
                ydl_opts.pop('cookiefile', None)
                ydl_opts['format'] = 'best'
                # Remove any postprocessors that could cause failures for video download
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception as retry_err:
                    # If still fails, raise a clear error prompting the user to add cookies
                    raise ValueError(
                        "Instagram download still failed after retry without cookies. "
                        "Please provide valid INSTAGRAM_COOKIES environment variable."
                    ) from retry_err
                # If retry succeeded, continue processing as normal
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            err_msg = str(e)
            platform = detect_platform(url)
            # Instagram authentication required error handling
            if platform == "Instagram" and "Instagram sent an empty media response" in err_msg:
                raise ValueError(
                    "Instagram download failed: missing or invalid cookies. "
                    "Set the INSTAGRAM_COOKIES environment variable with a valid session cookie and redeploy."
                )
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                if is_audio:
                    # For audio, use best and let ffmpeg extract if available
                    if ffmpeg_available:
                        ydl_opts['format'] = 'best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        ydl_opts['format'] = 'best'
                else:
                    # For video, prefer combined video+audio
                    if ffmpeg_available:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                        ydl_opts['merge_output_format'] = 'mp4'
                    else:
                        ydl_opts['format'] = 'best'
                # Remove any existing postprocessors that may cause errors for video
                if not is_audio:
                    ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            platform = detect_platform(url)
            # Handle Instagram extraction failures gracefully by retrying with a generic best format
            if platform == "Instagram":
                # Reset format to best available and retry download without metadata processing
                ydl_opts['format'] = 'best'
                # Remove postprocessors to avoid ffmpeg errors if not needed
                ydl_opts.pop('postprocessors', None)
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception:
                    info = None
            # Existing YouTube fallback logic remains unchanged
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                # If still no info, attempt generic fallback for YouTube again (existing logic)
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                    if yt_fallback:
                        return yt_fallback
                raise e
            # If specified format failed (e.g. ffmpeg missing error), retry with safest progressive format
            if "ffmpeg" in str(e).lower() or "merge" in str(e).lower() or "requested format" in str(e).lower():
                ydl_opts.pop('merge_output_format', None)
                ydl_opts.pop('postprocessors', None)
                if is_audio:
                    ydl_opts['format'] = 'bestaudio/best'
                else:
                    ydl_opts['format'] = '22/18/best[vcodec!=none][acodec!=none]'
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as retry_ydl:
                        info = retry_ydl.extract_info(url, download=True)
                except Exception:
                    pass

            # If yt-dlp failed completely on YouTube, attempt direct Invidious stream download
            if not info and detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback:
                    return yt_fallback

            if not info:
                if detect_platform(url) == "YouTube":
                    yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
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

        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            # Scan directory for matching valid file with req_id
            for f in os.listdir(DOWNLOAD_DIR):
                cand = os.path.join(DOWNLOAD_DIR, f)
                if f.startswith(req_id) and os.path.exists(cand) and os.path.getsize(cand) > 0 and not f.endswith(".part"):
                    filename = cand
                    break

        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            if detect_platform(url) == "YouTube":
                yt_fallback = download_youtube_fallback(url, req_id, is_audio=is_audio)
                if yt_fallback and os.path.exists(yt_fallback["filepath"]) and os.path.getsize(yt_fallback["filepath"]) > 0:
                    return yt_fallback
            raise FileNotFoundError("Downloaded media file could not be located or is empty.")

        clean_name = os.path.basename(filename)
        # Strip req_id prefix from downloaded filename for user-friendly name
        display_name = clean_name.replace(f"{req_id}_", "")

        return {
            "filepath": filename,
            "filename": display_name,
            "filesize": os.path.getsize(filename)
        }
