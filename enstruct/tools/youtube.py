import logging
import os
import tempfile
from typing import Optional, Dict, Any

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

logger = logging.getLogger("enstruct.tools.youtube")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class YouTubeDownloader:
    """A wrapper for yt-dlp to download and extract audio from YouTube URLs."""

    def __init__(self) -> None:
        """Initializes the YouTubeDownloader.

        Raises:
            RuntimeError: If yt-dlp package is not installed/available.
        """
        if yt_dlp is None:
            logger.error("yt-dlp is not installed. YouTubeDownloader is unavailable.")
            raise RuntimeError(
                "The 'yt-dlp' package is required for YouTube audio downloading but is not installed. "
                "Please install it using: pip install yt-dlp"
            )

    def download_audio(self, url: str, output_dir: Optional[str] = None) -> str:
        """Downloads the audio from the given YouTube URL and extracts it as an MP3 file.

        Args:
            url: The YouTube video or audio URL.
            output_dir: Folder path where the downloaded audio should be saved.
                         If None, a temporary directory is used.

        Returns:
            The local absolute filepath to the downloaded MP3 audio.

        Raises:
            ValueError: If the URL is empty or invalid.
            RuntimeError: If download or audio extraction fails.
        """
        if not url or not url.strip():
            raise ValueError("YouTube URL cannot be empty.")

        if output_dir is None:
            output_dir = tempfile.gettempdir()

        os.makedirs(output_dir, exist_ok=True)
        logger.info("Initializing download for YouTube URL: %s", url)

        # Output template for yt-dlp
        outtmpl_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        ydl_opts: Dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise RuntimeError("Failed to extract info from YouTube URL.")

                # If it's a playlist or multiple entries, get the first one
                if "entries" in info:
                    video_info = info["entries"][0]
                else:
                    video_info = info

                # Construct expected output file path
                title = video_info.get("title")
                if not title:
                    raise RuntimeError("Could not retrieve video title from YouTube metadata.")

                # Clean title using standard yt-dlp restricted characters filter (or check downloaded files)
                # Let's get the final filename directly from yt-dlp if possible,
                # or prepare path manually.
                # yt-dlp stores output files info under 'requested_downloads'
                req_downloads = video_info.get("requested_downloads", [])
                if req_downloads:
                    final_path = req_downloads[0].get("filepath")
                    if final_path and os.path.exists(final_path):
                        logger.info("YouTube audio successfully downloaded and converted to: %s", final_path)
                        return os.path.abspath(final_path)

                # Fallback path estimation
                sanitized_title = ydl.prepare_filename(video_info)
                # Replace original extension with mp3
                base, _ = os.path.splitext(sanitized_title)
                expected_path = f"{base}.mp3"

                if os.path.exists(expected_path):
                    logger.info("YouTube audio successfully downloaded (fallback check) to: %s", expected_path)
                    return os.path.abspath(expected_path)

                # Search directory for recently downloaded MP3 with the title if all else fails
                for file_in_dir in os.listdir(output_dir):
                    if title in file_in_dir and file_in_dir.endswith(".mp3"):
                        found_path = os.path.join(output_dir, file_in_dir)
                        logger.info("Discovered downloaded MP3 in directory: %s", found_path)
                        return os.path.abspath(found_path)

                raise FileNotFoundError(f"Could not find the extracted MP3 file for video '{title}'.")

        except Exception as e:
            logger.error("Failed to download YouTube audio: %s", str(e))
            raise RuntimeError(f"YouTube download failed: {e}") from e
