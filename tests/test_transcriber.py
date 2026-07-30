import sys
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from enstruct.core.transcriber import EnstructTranscriber, detect_optimal_device
from enstruct.core.translator import EnstructTranslator
from enstruct.integrations.drive import DriveManager


def test_detect_optimal_device():
    # Test optimal device detection logic
    device = detect_optimal_device()
    assert device in ["cuda", "cpu"]


@patch("enstruct.core.transcriber.WhisperModel")
def test_transcriber_initialization(mock_whisper):
    # Test initialization with custom parameters
    transcriber = EnstructTranscriber(model_size="tiny", device="cpu", compute_type="float32")
    assert transcriber.model_size == "tiny"
    assert transcriber.device == "cpu"
    assert transcriber.compute_type == "float32"
    mock_whisper.assert_called_once_with("tiny", device="cpu", compute_type="float32")


@patch("enstruct.core.transcriber.WhisperModel")
def test_transcriber_transcribe_file_not_found(mock_whisper):
    # Test that transcribing a non-existent file raises FileNotFoundError
    transcriber = EnstructTranscriber(model_size="tiny", device="cpu")
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe("non_existent_audio.mp3")


@patch("enstruct.core.transcriber.WhisperModel")
@patch("os.path.exists", return_value=True)
def test_transcriber_transcribe_success(mock_exists, mock_whisper):
    # Create mock transcription segment generators
    mock_segment_1 = MagicMock()
    mock_segment_1.start = 0.0
    mock_segment_1.end = 2.0
    mock_segment_1.text = "Hello world."

    mock_segment_2 = MagicMock()
    mock_segment_2.start = 2.0
    mock_segment_2.end = 4.0
    mock_segment_2.text = " Testing Enstruct."

    mock_segments = [mock_segment_1, mock_segment_2]

    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.duration = 4.0

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
    mock_whisper.return_value = mock_model_instance

    transcriber = EnstructTranscriber(model_size="tiny", device="cpu")
    result = transcriber.transcribe("dummy_audio.wav")

    assert result["text"] == "Hello world. Testing Enstruct."
    assert len(result["segments"]) == 2
    assert result["segments"][0]["start"] == 0.0
    assert result["segments"][0]["text"] == "Hello world."
    assert result["language"] == "en"
    assert result["duration"] == 4.0


@patch("enstruct.core.transcriber.WhisperModel")
@patch("os.path.exists", return_value=True)
def test_transcriber_detect_language(mock_exists, mock_whisper):
    mock_info = MagicMock()
    mock_info.language = "es"
    mock_info.language_probability = 0.99

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.return_value = ([], mock_info)
    mock_whisper.return_value = mock_model_instance

    transcriber = EnstructTranscriber(model_size="tiny", device="cpu")
    detected = transcriber.detect_language("dummy_audio.wav")
    assert detected == "es"


@patch("enstruct.core.transcriber.WhisperModel")
@patch("os.path.exists", return_value=True)
def test_translator_success(mock_exists, mock_whisper):
    # Setup mock for EnstructTranslator which uses task='translate'
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 3.0
    mock_segment.text = "This is a translation."

    mock_info = MagicMock()
    mock_info.language = "fr"
    mock_info.duration = 3.0

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.return_value = ([mock_segment], mock_info)
    mock_whisper.return_value = mock_model_instance

    translator = EnstructTranslator(model_size="tiny", device="cpu")
    result = translator.translate("dummy_audio.wav")

    assert result["text"] == "This is a translation."
    # Ensure WhisperModel's transcribe was called with task="translate"
    mock_model_instance.transcribe.assert_called_once_with("dummy_audio.wav", language=None, task="translate")


def test_drive_manager_local_execution():
    # DriveManager should not mount or crash when executing locally
    with patch.dict(sys.modules):
        if "google.colab" in sys.modules:
            del sys.modules["google.colab"]
        manager = DriveManager()
        assert not manager.is_colab
        assert not manager.mount_drive()
        assert manager.save_file("test.srt", "test") is not None  # Local fallback active


def test_drive_manager_colab_execution():
    # Mock google.colab and google.colab.drive to test colab execution paths
    mock_drive = MagicMock()
    mock_colab = MagicMock()
    mock_colab.drive = mock_drive

    with patch.dict(sys.modules, {
        "google": MagicMock(),
        "google.colab": mock_colab,
        "google.colab.drive": mock_drive
    }):
        manager = DriveManager()
        assert manager.is_colab
        assert manager.mount_drive()
        assert manager.is_mounted

        # Test save file
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", create=True) as mock_open:
            path = manager.save_file("sub.srt", "subtitle content")
            assert path == os.path.join(manager.OUTPUTS_DIR, "sub.srt")


def test_drive_manager_history_and_folders():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = DriveManager()
        manager.LOCAL_ROOT = tmpdir
        manager.LOCAL_OUTPUTS_DIR = os.path.join(tmpdir, "outputs")
        manager.LOCAL_HISTORY_FILE = os.path.join(tmpdir, "history.json")

        manager.ensure_folders()
        assert os.path.exists(manager.LOCAL_ROOT)
        assert os.path.exists(manager.LOCAL_OUTPUTS_DIR)

        # Retrieve empty history
        assert manager.get_history() == []

        # Log session
        entry = {
            "id": "123",
            "date": "2026-07-30 12:00:00",
            "source": "YouTube URL",
            "language": "en",
            "duration": 5.5,
            "model": "base",
            "format": "srt",
            "output_path": "/tmp/test.srt",
            "status": "Success",
            "error_message": ""
        }
        manager.log_session(entry)

        history = manager.get_history()
        assert len(history) == 1
        assert history[0]["id"] == "123"

        # Clear history
        manager.clear_history()
        assert manager.get_history() == []


def test_youtube_downloader_not_installed():
    with patch("enstruct.tools.youtube.yt_dlp", None):
        # Importing or instantiating should raise RuntimeError when yt-dlp is not available
        from enstruct.tools.youtube import YouTubeDownloader
        with pytest.raises(RuntimeError) as excinfo:
            YouTubeDownloader()
        assert "yt-dlp" in str(excinfo.value)


def test_youtube_downloader_empty_url():
    from enstruct.tools.youtube import YouTubeDownloader
    downloader = YouTubeDownloader()
    with pytest.raises(ValueError):
        downloader.download_audio("")


@patch("enstruct.tools.youtube.yt_dlp")
def test_youtube_downloader_success(mock_yt_dlp):
    from enstruct.tools.youtube import YouTubeDownloader

    mock_ydl_instance = MagicMock()
    mock_info = {
        "title": "Sample Video Title",
        "requested_downloads": [{"filepath": "/tmp/Sample Video Title.mp3"}]
    }
    mock_ydl_instance.extract_info.return_value = mock_info
    mock_yt_dlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl_instance

    downloader = YouTubeDownloader()
    with patch("os.path.exists", return_value=True):
        path = downloader.download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ", output_dir="/tmp")
        assert "Sample Video Title.mp3" in path
