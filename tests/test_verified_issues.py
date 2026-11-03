import asyncio
import os
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
    extension_from_mime_type,
    media_type_for_file,
)
from app.pages import HOME_SCRIPTS, get_home_html
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
        for format_spec, expected_format in (
            ("best", "bestvideo+bestaudio/best"),
            ("18", "18/best[acodec!=none][vcodec!=none]/bestvideo+bestaudio/best"),
        ):
            with self.subTest(format_spec=format_spec):
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
                         patch("app.downloader.has_ffmpeg", return_value=True), \
                         patch("app.downloader.get_cookies_filepath", return_value=None):
                        result = download_media("https://example.com/video", format_spec)

                    self.assertEqual(FakeYoutubeDL.options[0]["format"], expected_format)
                    self.assertEqual(FakeYoutubeDL.options[0]["merge_output_format"], "mp4")
                    self.assertTrue(FakeYoutubeDL.downloads[0])
                    self.assertTrue(os.path.exists(result["filepath"]))
                finally:
                    main.remove_temp_file(filepath)

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
        click_offset = app_script.index("anchor.click();")
        revoke_offset = app_script.index("URL.revokeObjectURL(blobUrl)")
        self.assertGreater(revoke_offset, click_offset)
        self.assertIn("setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000)", app_script)

    def test_history_dialog_is_hidden_until_opened(self):
        home_html = get_home_html()
        stylesheet = Path("app/static/style.css").read_text(encoding="utf-8")
        self.assertIn('<dialog class="history-dialog" id="historyModal"', home_html)
        self.assertIn(".history-dialog:not([open]) { display: none; }", stylesheet)


if __name__ == "__main__":
    unittest.main()
