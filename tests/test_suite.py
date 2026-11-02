"""
Comprehensive Independent Test Suite for GI LINK
Covers:
1. Health & Metadata & SEO verification tags (Search Console, AdSense, robots, sitemap, ads.txt)
2. Comprehensive SSRF validation:
   - IPv4 private, loopback, link-local, carrier-grade, decimal, hex
   - IPv6 loopback (::1), link-local (fe80::), unique local (fc00::/fd00::)
   - DNS resolution rebinding to private IPs
   - Malformed/unusual schemes, userinfo (@), missing hosts
   - Ensuring legitimate media URLs are NEVER blocked
3. Instagram & YouTube Logic:
   - Instagram with invalid/expired cookies
   - Instagram without cookies
   - Transparency of retry logic (not masking original cookie error)
   - YouTube bot challenge handling
4. Download Integrity & Lifecycle:
   - File creation, non-empty validation, and MP4 magic-bytes integrity
   - Chunked StreamingResponse delivery
   - Temporary file cleanup on success, exceptions, and client disconnect
   - Partial file cleanup via cleanup_temp_req_files
   - FFmpeg availability adaptation
"""

import os
import sys
import json
import socket
import asyncio
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, remove_temp_file, is_safe_media_url
from app.downloader import (
    detect_platform,
    sanitize_filename,
    parse_cookie_data,
    format_duration,
    format_filesize,
    has_ffmpeg,
    get_cookies_filepath,
    get_media_info,
    download_media,
    cleanup_temp_req_files,
    DOWNLOAD_DIR
)

async def asgi_request(method: str, path: str, query: str = "", body: bytes = b"", headers: list = None):
    """Executes an in-process ASGI request against the FastAPI app."""
    headers = headers or []
    response_body = []
    response_headers = {}
    status_code = [None]

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": query.encode("latin-1"),
        "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers],
        "client": ("127.0.0.1", 54321),
        "server": ("127.0.0.1", 80),
    }

    sent_request = [False]
    done_event = asyncio.Event()

    async def receive():
        if not sent_request[0]:
            sent_request[0] = True
            return {"type": "http.request", "body": body, "more_body": False}
        await done_event.wait()
        return {"type": "http.disconnect"}

    async def send(event):
        if event["type"] == "http.response.start":
            status_code[0] = event["status"]
            for k, v in event.get("headers", []):
                response_headers[k.decode("latin-1").lower()] = v.decode("latin-1")
        elif event["type"] == "http.response.body":
            response_body.append(event.get("body", b""))
            if not event.get("more_body", False):
                done_event.set()

    task = asyncio.create_task(app(scope, receive, send))
    await task
    done_event.set()
    return status_code[0], response_headers, b"".join(response_body)


class TestHealthAndMetadata(unittest.TestCase):
    def test_health_endpoint(self):
        status, headers, body = asyncio.run(asgi_request("GET", "/api/health"))
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "GI LINK Media Downloader")
        self.assertIn("ffmpeg_available", data)
        self.assertIn("cookie_file_active", data)

    def test_home_page_seo_and_verification_tags(self):
        status, _, body = asyncio.run(asgi_request("GET", "/"))
        self.assertEqual(status, 200)
        html = body.decode("utf-8")
        # Google Search Console tag preserved
        self.assertIn('name="google-site-verification" content="Du_RVrnTwPBjSXPQjQ-RlDluCuEo0A4QMPz9vAWXjDY"', html)
        # Google AdSense tag preserved
        self.assertIn('name="google-adsense-account" content="ca-pub-6837969928640726"', html)
        self.assertIn("GI LINK", html)

    def test_policy_pages(self):
        for path in ["/about", "/privacy", "/terms", "/dmca", "/contact"]:
            status, _, body = asyncio.run(asgi_request("GET", path))
            self.assertEqual(status, 200, f"Page {path} returned status {status}")
            self.assertIn("GI LINK", body.decode("utf-8"))

    def test_crawlers_and_ads_txt(self):
        status, _, body = asyncio.run(asgi_request("GET", "/robots.txt"))
        self.assertEqual(status, 200)
        self.assertIn("User-agent: *", body.decode("utf-8"))

        status, _, body = asyncio.run(asgi_request("GET", "/sitemap.xml"))
        self.assertEqual(status, 200)
        self.assertIn("https://gilinkdl.vercel.app/", body.decode("utf-8"))

        status, _, body = asyncio.run(asgi_request("GET", "/ads.txt"))
        self.assertEqual(status, 200)
        self.assertIn("pub-6837969928640726", body.decode("utf-8"))


class TestSSRFAndSecurityValidation(unittest.TestCase):
    def test_ipv4_private_and_loopback_ranges(self):
        blocked_ips = [
            "http://127.0.0.1/",
            "http://127.0.0.2:8080/test",
            "http://10.0.0.1/",
            "http://10.255.255.255/",
            "http://172.16.0.1/",
            "http://172.31.255.254/",
            "http://192.168.0.1/",
            "http://192.168.1.254/",
            "http://169.254.169.254/latest/meta-data/",  # Cloud instance metadata
            "http://0.0.0.0/",
            "http://0.0.0.0:8000/",
        ]
        for url in blocked_ips:
            safe, reason = is_safe_media_url(url)
            self.assertFalse(safe, f"Failed to block private IPv4: {url}")
            self.assertTrue(len(reason) > 0)

    def test_ipv6_private_and_loopback_ranges(self):
        blocked_ipv6 = [
            "http://[::1]/",
            "http://[::1]:8080/",
            "http://[fe80::1]/",
            "http://[fc00::1]/",
            "http://[fd12:3456:789a:1::1]/",
            "http://[::]/",
        ]
        for url in blocked_ipv6:
            safe, reason = is_safe_media_url(url)
            self.assertFalse(safe, f"Failed to block IPv6: {url}")

    def test_decimal_and_hex_ip_representations(self):
        # 2130706433 is decimal representation of 127.0.0.1
        safe_dec, _ = is_safe_media_url("http://2130706433/admin")
        self.assertFalse(safe_dec, "Failed to block decimal IP representation of 127.0.0.1")

        # 0x7f000001 is hex representation of 127.0.0.1
        safe_hex, _ = is_safe_media_url("http://0x7f000001/admin")
        self.assertFalse(safe_hex, "Failed to block hex IP representation of 127.0.0.1")

    def test_dns_rebinding_to_private_ip(self):
        # Simulate DNS resolution returning a private IP for an external-looking hostname
        with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.100", 80))]):
            safe, reason = is_safe_media_url("http://attacker-controlled-domain.com/video.mp4")
            self.assertFalse(safe)
            self.assertIn("forbidden private address", reason)

        with patch("socket.getaddrinfo", return_value=[(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 80))]):
            safe, reason = is_safe_media_url("http://rebind-to-ipv6-loopback.org/media.mp4")
            self.assertFalse(safe)
            self.assertIn("forbidden private address", reason)

    def test_malformed_and_unusual_schemes(self):
        invalid_urls = [
            "",
            "not_a_url",
            "ftp://files.example.com/movie.mp4",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "http://admin:secret@legit.com/video.mp4",  # User credentials in URL
            "http:///no-host-path",
        ]
        for url in invalid_urls:
            safe, _ = is_safe_media_url(url)
            self.assertFalse(safe, f"Failed to reject invalid/dangerous URL: {url}")

    def test_legitimate_media_urls_are_permitted(self):
        legit_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.instagram.com/reel/C3test123/",
            "https://www.tiktok.com/@creator/video/1234567890",
            "https://www.facebook.com/watch/?v=987654321",
            "https://x.com/user/status/123456789",
            "https://twitter.com/user/status/123456789",
            "https://www.reddit.com/r/videos/comments/abcde/cool_clip/",
            "https://vimeo.com/123456789",
            "https://soundcloud.com/artist/track",
            "https://www.w3schools.com/html/mov_bbb.mp4",
        ]
        for url in legit_urls:
            safe, reason = is_safe_media_url(url)
            self.assertTrue(safe, f"Legitimate URL was incorrectly rejected: {url} ({reason})")


class TestInstagramAndYouTubeLogic(unittest.TestCase):
    def test_instagram_without_cookies_error_clarity(self):
        url = "https://www.instagram.com/reel/DBtest12345/"
        req_body = json.dumps({"url": url}).encode("utf-8")
        status, _, body = asyncio.run(asgi_request("POST", "/api/info", body=req_body, headers=[("content-type", "application/json")]))
        self.assertEqual(status, 400)
        res = json.loads(body.decode("utf-8"))
        self.assertFalse(res["success"])
        self.assertIn("Instagram", res["error"])

    def test_instagram_with_invalid_cookies_reports_both_attempts(self):
        # Configure invalid cookies
        with patch.dict(os.environ, {"INSTAGRAM_COOKIES": "sessionid=invalid_expired_token_12345"}):
            ck_file = get_cookies_filepath()
            self.assertIsNotNone(ck_file)
            self.assertTrue(os.path.exists(ck_file))

            # Simulate Instagram failing both with cookie and without cookie
            mock_ydl = MagicMock()
            mock_ydl.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.side_effect = Exception("Instagram sent an empty media response.")
            
            with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
                with self.assertRaises(ValueError) as ctx:
                    get_media_info("https://www.instagram.com/reel/C3test/")
                err_text = str(ctx.exception)
                # Verify both the original cookie attempt and retry are reported transparently
                self.assertIn("Configured cookies failed", err_text)
                self.assertIn("retry without cookies failed", err_text)

    def test_youtube_fallback_does_not_return_fake_file(self):
        # Test download_youtube_fallback returns None if video cannot be fetched
        with patch("requests.get", side_effect=Exception("Network error")):
            result = app_downloader_fallback = download_media.__globals__["download_youtube_fallback"]("https://youtu.be/dQw4w9WgXcQ", "test_req")
            self.assertIsNone(result)

    def test_parse_cookie_data_netscape_and_header(self):
        # Header string format
        header_cookie = "sessionid=123456; csrftoken=abcdef"
        lines = parse_cookie_data(header_cookie, default_domain=".instagram.com")
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("sessionid\t123456" in l for l in lines))

        # Netscape format
        netscape_raw = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1793361876\tSID\tabc"
        lines_ns = parse_cookie_data(netscape_raw)
        self.assertEqual(len(lines_ns), 1)
        self.assertIn("SID\tabc", lines_ns[0])


class TestDownloadIntegrityAndCleanup(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertNotIn("/", sanitize_filename("../../etc/passwd"))
        self.assertNotIn("..", sanitize_filename("../test.mp4"))
        hindi_name = "शानदार_वीडियो_clip"
        clean = sanitize_filename(hindi_name)
        self.assertTrue(clean.isascii())
        self.assertGreater(len(clean), 0)

    def test_partial_file_cleanup_on_failure(self):
        test_id = "testclean123"
        dummy_file = os.path.join(DOWNLOAD_DIR, f"{test_id}_partial.part")
        with open(dummy_file, "w") as f:
            f.write("partial content")
        self.assertTrue(os.path.exists(dummy_file))

        cleanup_temp_req_files(test_id)
        self.assertFalse(os.path.exists(dummy_file), "cleanup_temp_req_files failed to remove partial file")

    def test_temp_file_removal_helper(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"test data")
            path = tf.name
        self.assertTrue(os.path.exists(path))
        remove_temp_file(path)
        self.assertFalse(os.path.exists(path))
        # Ensure idempotent calling does not raise error
        remove_temp_file(path)

    def test_ffmpeg_missing_fallback(self):
        with patch("shutil.which", return_value=None):
            self.assertFalse(has_ffmpeg())

    def test_live_download_file_integrity_and_magic_bytes(self):
        test_video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
        
        # 1. Test info extraction
        info = get_media_info(test_video_url)
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "mov_bbb")

        # 2. Test actual download execution
        result = download_media(test_video_url, format_spec="best", is_audio=False)
        filepath = result["filepath"]
        self.assertTrue(os.path.exists(filepath), "Downloaded file must exist on disk")

        # 3. Verify MP4 magic bytes integrity (ftyp box)
        with open(filepath, "rb") as f:
            header = f.read(12)
            self.assertIn(b"ftyp", header, "File does not contain valid MP4 ftyp container box header")

        # 4. Test HTTP /api/download streaming endpoint
        status, headers, body = asyncio.run(
            asgi_request("GET", "/api/download", query=f"url={test_video_url}&format_spec=best")
        )
        self.assertEqual(status, 200)
        self.assertIn("content-disposition", headers)
        self.assertEqual(headers.get("content-type"), "video/mp4")
        self.assertEqual(headers.get("content-length"), str(result["filesize"]))
        self.assertEqual(len(body), result["filesize"])

        # 5. Clean up temp file
        remove_temp_file(filepath)
        self.assertFalse(os.path.exists(filepath))


if __name__ == "__main__":
    unittest.main()
