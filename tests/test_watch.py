import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from enstruct.tools.watch import FolderWatcher


@patch("enstruct.core.transcriber.EnstructTranscriber")
def test_folder_watcher_run_once(mock_transcriber_cls):
    temp_in = tempfile.mkdtemp()
    temp_out = tempfile.mkdtemp()
    temp_arch = tempfile.mkdtemp()

    try:
        # Create a dummy mp3 file in input directory
        dummy_file = os.path.join(temp_in, "test_audio.mp3")
        with open(dummy_file, "wb") as f:
            f.write(b"dummy audio data")

        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = {
            "text": "Folder watch test",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Folder watch test"}],
            "language": "en",
            "duration": 2.0
        }
        mock_transcriber_cls.return_value = mock_instance

        watcher = FolderWatcher(
            input_dir=temp_in,
            output_dir=temp_out,
            format="srt",
            archive_dir=temp_arch,
            model_size="large-v3-turbo"
        )

        processed = watcher.run_once()
        assert processed == ["test_audio.mp3"]

        # Input file should be moved to archive
        assert not os.path.exists(dummy_file)
        assert os.path.exists(os.path.join(temp_arch, "test_audio.mp3"))

        # Output SRT should exist in output_dir
        expected_output = os.path.join(temp_out, "test_audio.srt")
        assert os.path.exists(expected_output)
        with open(expected_output, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Folder watch test" in content
    finally:
        shutil.rmtree(temp_in)
        shutil.rmtree(temp_out)
        shutil.rmtree(temp_arch)
