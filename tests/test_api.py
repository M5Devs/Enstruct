import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from interfaces.api.server import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("interfaces.api.server.get_transcriber")
def test_transcriptions_endpoint_json(mock_get_transcriber, tmp_path):
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = {
        "text": "Hello this is a test transcription.",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Hello this is a test transcription."}
        ],
        "language": "en",
        "duration": 2.0
    }
    mock_get_transcriber.return_value = mock_transcriber

    dummy_audio = tmp_path / "audio.wav"
    dummy_audio.write_bytes(b"RIFF....WAVEfmt ....data....")

    with open(dummy_audio, "rb") as f:
        response = client.post(
            "/v1/audio/transcriptions",
            files={"file": ("audio.wav", f, "audio/wav")},
            data={"model": "large-v3-turbo", "response_format": "json"}
        )

    assert response.status_code == 200
    assert response.json() == {"text": "Hello this is a test transcription."}


@patch("interfaces.api.server.get_transcriber")
def test_transcriptions_endpoint_srt(mock_get_transcriber, tmp_path):
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = {
        "text": "Subtitle test.",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Subtitle test."}
        ],
        "language": "en",
        "duration": 1.5
    }
    mock_get_transcriber.return_value = mock_transcriber

    dummy_audio = tmp_path / "audio.wav"
    dummy_audio.write_bytes(b"RIFF....WAVEfmt ....data....")

    with open(dummy_audio, "rb") as f:
        response = client.post(
            "/v1/audio/transcriptions",
            files={"file": ("audio.wav", f, "audio/wav")},
            data={"model": "large-v3-turbo", "response_format": "srt"}
        )

    assert response.status_code == 200
    assert "00:00:00,000 --> 00:00:01,500" in response.text
    assert "Subtitle test." in response.text
