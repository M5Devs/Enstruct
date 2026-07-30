import pytest
import os
from unittest.mock import MagicMock, patch
from enstruct.core.transcriber import EnstructTranscriber, detect_optimal_device
from enstruct.core.translator import EnstructTranslator


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
