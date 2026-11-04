import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app import main
from app.downloader import (
    DOWNLOAD_DIR,
    audio_preset,
    download_media,
    download_youtube_fallback,
    detect_platform,
    extension_from_mime_type,
    get_media_info,
    media_type_for_file,
    _configure_static_ffmpeg,
)
from app.pages import ASSET_VERSION, HOME_SCRIPTS, get_home_html, render_layout
from app.icons import get_favicon_bytes


class TestVerifiedIssues(unittest.TestCase):
    def test_audio_extensions_and_mime_types_match_original_formats(self):
        cases = {
            "audio/aac": ".aac",
            'audio/mp4; codecs="mp4a.40.2"': ".m4a",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "audio/opus": ".opus",
            "audio/webm": ".webm",
        }
        for mime_type, extension in cases.items():
            with self.subTest(mime_type=mime_type):
                self.assertEqual(extension_from_mime_type(mime_type), extension)
                if mime_type in {"audio/aac", "audio/opus"}:
                    self.assertNotEqual(extension, ".mp3")

        self.assertEqual(media_type_for_file("track.m4a", True), "audio/mp4")
        self.assertEqual(media_type_for_file("track.opus", True), "audio/opus")
        self.assertEqual(media_type_for_file("track.webm", True), "audio/webm")

    def test_mp3_preset_reflects_conversion_availability(self):
        with patch("app.downloader.has_ffmpeg", return_value=False):
            preset = audio_preset(".webm")
            self.assertEqual(preset["ext"], "webm")
            self.assertTrue(preset["is_audio"])
            self.assertIn("Original format", preset["name"])

        with patch("app.downloader.has_ffmpeg", return_value=True):
            preset = audio_preset(".webm")
            self.assertEqual(preset["ext"], "mp3")
            self.assertIn("MP3", preset["name"])

    def test_youtube_fallback_keeps_the_original_audio_extension_without_ffmpeg(self):
        api_response = MagicMock(status_code=200)
        api_response.json.return_value = {
            "title": "sample audio",
            "adaptiveFormats": [
                {"type": "audio/webm; codecs=opus", "url": "https://media.example/audio"}
            ],
        }
        audio_response = MagicMock(status_code=200)
        audio_response.__enter__.return_value = audio_response
        audio_response.__exit__.return_value = False
        audio_response.iter_content.return_value = [b"audio data"]

        with patch("app.downloader.requests.get", side_effect=[api_response, audio_response]), \
             patch("app.downloader.has_ffmpeg", return_value=False):
            result = download_youtube_fallback(
                "https://youtu.be/dQw4w9WgXcQ",
                "verifiedissue",
                is_audio=True,
            )

        self.assertIsNotNone(result)
        self.assertTrue(result["filename"].endswith(".webm"))
        self.assertTrue(result["filepath"].endswith(".webm"))
        self.assertTrue(os.path.exists(result["filepath"]))
        os.remove(result["filepath"])

    def test_audio_download_response_uses_the_returned_file_format(self):
        async def make_response(path):
            result = {"filepath": path, "filename": "sample.webm", "filesize": 10}
            with patch.object(main, "is_safe_media_url", return_value=(True, "")), \
                 patch.object(main, "download_media", return_value=result), \
                 patch.object(main, "get_youtube_direct_stream") as direct_stream:
                response = await main.trigger_download(
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "bestaudio/best",
                    True,
                )
                direct_stream.assert_not_called()
                return response

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as media:
            media.write(b"\x1aE\xdf\xa3audio")
            filepath = media.name
        try:
            response = asyncio.run(make_response(filepath))
            self.assertEqual(response.media_type, "audio/webm")
            self.assertIn("sample.webm", response.headers["content-disposition"])
        finally:
            main.remove_temp_file(filepath)

    def test_video_presets_select_audio_video_muxing_with_ffmpeg(self):
        for url, format_spec, ffmpeg_available, expected_format, expected_merge in (
            ("https://example.com/video", "best", True, "bestvideo+bestaudio/best", "mp4"),
            ("https://example.com/video", "18", True, "18/best[acodec!=none][vcodec!=none]/bestvideo+bestaudio/best", "mp4"),
            ("https://www.instagram.com/reel/DfPUcPmtIDs/", "best", True, "bestvideo+bestaudio/best", "mp4"),
            ("https://www.instagram.com/reel/DfPUcPmtIDs/", "best", False, "best[vcodec!=none][acodec!=none]", None),
        ):
            with self.subTest(url=url, format_spec=format_spec, ffmpeg_available=ffmpeg_available):
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as media:
                    media.write(b"video and audio")
                    filepath = media.name

                class FakeYoutubeDL:
                    options = []
                    downloads = []

                    def __init__(self, options):
                        self.options.append(options)

                    def __enter__(self):
                        return self

                    def __exit__(self, *_args):
                        return False

                    def extract_info(self, _url, download):
                        self.downloads.append(download)
                        return {"title": "sample"}

                    def prepare_filename(self, _info):
                        return filepath

                try:
                    FakeYoutubeDL.options = []
                    FakeYoutubeDL.downloads = []
                    with patch("app.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL), \
                         patch("app.downloader.has_ffmpeg", return_value=ffmpeg_available), \
                         patch("app.downloader.get_cookies_filepath", return_value=None):
                        result = download_media(url, format_spec)

                    self.assertEqual(FakeYoutubeDL.options[0]["format"], expected_format)
                    self.assertEqual(FakeYoutubeDL.options[0].get("merge_output_format"), expected_merge)
                    self.assertTrue(FakeYoutubeDL.downloads[0])
                    self.assertTrue(os.path.exists(result["filepath"]))
                finally:
                    main.remove_temp_file(filepath)

    def test_supported_platform_hostnames_are_detected_exactly(self):
        cases = {
            "https://youtu.be/dQw4w9WgXcQ": "YouTube",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ": "YouTube",
            "https://www.instagram.com/reel/abc123/": "Instagram",
            "https://vm.tiktok.com/abc123/": "TikTok",
            "https://fb.watch/abc123/": "Facebook",
            "https://x.com/creator/status/123": "X (Twitter)",
            "https://redd.it/abc123": "Reddit",
            "https://pin.it/abc123": "Pinterest",
            "https://on.soundcloud.com/abc123": "SoundCloud",
            "https://vimeo.com/123456": "Vimeo",
            "https://youtube.com.attacker.example/video": "Universal Media",
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(detect_platform(url), expected)

    def test_other_platform_retries_metadata_without_stale_cookies(self):
        calls = []

        class FakeYoutubeDL:
            def __init__(self, options):
                self.options = options

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def extract_info(self, _url, download):
                calls.append((self.options, download))
                if len(calls) == 1:
                    raise ValueError("Authentication failed")
                return {
                    "title": "TikTok sample",
                    "formats": [{
                        "format_id": "progressive",
                        "vcodec": "h264",
                        "acodec": "aac",
                        "height": 720,
                        "ext": "mp4",
                    }],
                }

        with patch("app.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL), \
             patch("app.downloader.get_cookies_filepath", return_value="/tmp/cookies.txt"), \
             patch("app.downloader.has_ffmpeg", return_value=False):
            result = get_media_info("https://www.tiktok.com/@creator/video/123456")

        self.assertEqual(len(calls), 2)
        self.assertIn("cookiefile", calls[0][0])
        self.assertNotIn("cookiefile", calls[1][0])
        self.assertEqual(result["platform"], "TikTok")
        self.assertEqual(result["formats"][0]["quality"], "720p")

    def test_non_youtube_format_failure_retries_only_with_audio_video_streams(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as media:
            media.write(b"progressive video audio")
            filepath = media.name
        captured_options = []

        class FakeYoutubeDL:
            def __init__(self, options):
                self.options = options
                captured_options.append(options)

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def extract_info(self, _url, download):
                if len(captured_options) == 1:
                    raise ValueError("Requested format is not available")
                return {"title": "sample"}

            def prepare_filename(self, _info):
                return filepath

        try:
            with patch("app.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL), \
                 patch("app.downloader.has_ffmpeg", return_value=True), \
                 patch("app.downloader.get_cookies_filepath", return_value=None):
                result = download_media("https://www.tiktok.com/@creator/video/123456", "best")

            self.assertEqual(
                captured_options[1]["format"],
                "best[vcodec!=none][acodec!=none]",
            )
            self.assertEqual(result["filename"], os.path.basename(filepath))
        finally:
            main.remove_temp_file(filepath)

    def test_static_ffmpeg_uses_tmp_when_the_installed_package_is_read_only(self):
        static_ffmpeg = MagicMock()
        static_ffmpeg_runtime = MagicMock()
        static_ffmpeg.run = static_ffmpeg_runtime
        static_ffmpeg_runtime.get_platform_dir.return_value = (
            "/readonly/site-packages/static_ffmpeg/bin/linux"
        )
        static_ffmpeg_runtime.get_platform_key.return_value = "linux"

        with patch.dict(sys.modules, {
            "static_ffmpeg": static_ffmpeg,
            "static_ffmpeg.run": static_ffmpeg_runtime,
        }), patch("app.downloader.os.makedirs"):
            error = _configure_static_ffmpeg()

        self.assertIsNone(error)
        static_ffmpeg.add_paths.assert_called_once_with(
            download_dir=os.path.join(
                tempfile.gettempdir(), "gilink-static-ffmpeg", "bin", "linux"
            )
        )
        self.assertEqual(
            static_ffmpeg_runtime.LOCK_FILE,
            os.path.join(tempfile.gettempdir(), "gilink-static-ffmpeg", "ffmpeg.lock"),
        )

    def test_metadata_does_not_advertise_unmuxable_video_without_ffmpeg(self):
        info = {
            "title": "adaptive-only video",
            "formats": [
                {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "ext": "mp4"},
                {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "ext": "m4a", "abr": 128},
            ],
        }

        class FakeYoutubeDL:
            downloads = []

            def __init__(self, _options):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def extract_info(self, _url, download):
                self.downloads.append(download)
                return info

        with patch("app.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL), \
             patch("app.downloader.has_ffmpeg", return_value=False), \
             patch("app.downloader.get_cookies_filepath", return_value=None):
            result = get_media_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        self.assertEqual(FakeYoutubeDL.downloads, [False])
        self.assertEqual(result["formats"], [])
        self.assertEqual(result["presets"], [{
            "id": "bestaudio/best",
            "name": "Audio Only (Original format)",
            "ext": "m4a",
            "badge": "M4A",
            "is_audio": True,
        }])

    def test_icon_routes_match_file_signatures_and_content_types(self):
        async def get_response(handler):
            return await handler()

        cases = [
            (main.icon_192_png, "image/png", b"\x89PNG\r\n\x1a\n"),
            (main.icon_192_jpg, "image/jpeg", b"\xff\xd8\xff"),
            (main.icon_512_png, "image/png", b"\x89PNG\r\n\x1a\n"),
            (main.icon_512_jpg, "image/jpeg", b"\xff\xd8\xff"),
            (main.favicon, "image/vnd.microsoft.icon", b"\x00\x00\x01\x00"),
        ]
        for handler, mime_type, signature in cases:
            with self.subTest(mime_type=mime_type):
                response = asyncio.run(get_response(handler))
                self.assertEqual(response.headers["content-type"], mime_type)
                self.assertTrue(response.body.startswith(signature))

        self.assertTrue(get_favicon_bytes())

    def test_untrusted_values_are_not_inserted_with_inner_html(self):
        scripts = [
            HOME_SCRIPTS,
            Path("app/static/app.js").read_text(encoding="utf-8"),
        ]
        for script in scripts:
            self.assertNotIn("innerHTML", script)

        app_script = Path("app/static/app.js").read_text(encoding="utf-8")
        self.assertIn("frame.src = `/api/download?${query}`", app_script)
        self.assertIn("downloadFrame.contentDocument", app_script)
        self.assertNotIn("URL.createObjectURL", app_script)
        self.assertNotIn("new Blob", app_script)

    def test_history_dialog_is_hidden_until_opened(self):
        home_html = get_home_html()
        stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
        self.assertIn('<dialog class="history-dialog" id="historyModal"', home_html)
        self.assertIn(".history-dialog:not([open]) { display: none; }", stylesheet)

    def test_classic_and_modern_ui_toggle_is_available(self):
        home_html = get_home_html()
        app_html = render_layout("GI LINK", "Description", "", home_html)
        app_script = Path("app/static/app.js").read_text(encoding="utf-8")
        stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
        self.assertIn('id="uiModeToggle"', app_html)
        self.assertIn('data-ui-mode="classic"', app_html)
        self.assertIn("localStorage.setItem('gilink-ui-mode', mode)", app_script)
        self.assertIn('body[data-ui-mode="classic"]', stylesheet)
        self.assertIn(".modern-headline", stylesheet)
        self.assertIn(f"/static/style.css?v={ASSET_VERSION}", app_html)
        self.assertIn(f"/static/app.js?v={ASSET_VERSION}", app_html)
        self.assertEqual(app_html.count('class="brand-icon" src="/icon-192.png"'), 2)

    def test_footer_credits_creator_without_github_link(self):
        app_html = render_layout("GI LINK", "Description", "", get_home_html())
        self.assertIn("Created by Ghalib Kamal", app_html)
        self.assertNotIn('href="https://github.com/ghalibkamal7/gilink"', app_html)

    def test_available_download_styles_match_both_themes(self):
        stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
        app_script = Path("app/static/app.js").read_text(encoding="utf-8")
        self.assertIn(".format-button.is-video .format-icon", stylesheet)
        self.assertIn(".format-button.is-audio .format-icon", stylesheet)
        self.assertIn("body[data-ui-mode=\"classic\"] {", stylesheet)
        self.assertIn("--format-hover: #182238", stylesheet)
        self.assertIn("grid-template: \"main arrow\" auto \"info arrow\" auto", stylesheet)
        self.assertIn("format-extension", app_script)
        self.assertIn("format-size", app_script)
        self.assertIn("const accessibleDetails = [extension, sizeLabel].filter(Boolean);", app_script)
        self.assertNotIn("info.length", app_script)


if __name__ == "__main__":
    unittest.main()
