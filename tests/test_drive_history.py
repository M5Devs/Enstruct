import os
import shutil
import tempfile
import pytest
from enstruct.tools.drive import DriveManager


def test_drive_manager_history():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = DriveManager()
        # Override save dir to temp folder
        manager.get_save_directory = lambda: temp_dir

        assert manager.get_history() == []

        entry1 = {
            "id": "123",
            "date": "2026-10-23 10:00:00",
            "source": "Upload / Microphone",
            "language": "en",
            "duration": 5.0,
            "model": "large-v3-turbo",
            "format": "srt",
            "output_path": "/tmp/out.srt",
            "status": "Success",
            "error_message": ""
        }

        manager.log_session(entry1)
        history = manager.get_history()
        assert len(history) == 1
        assert history[0]["id"] == "123"

        entry2 = {
            "id": "456",
            "date": "2026-10-23 10:05:00",
            "source": "YouTube URL",
            "language": "es",
            "duration": 12.0,
            "model": "large-v3-turbo",
            "format": "vtt",
            "output_path": "/tmp/out2.vtt",
            "status": "Success",
            "error_message": ""
        }

        manager.log_session(entry2)
        history = manager.get_history()
        assert len(history) == 2
        assert history[1]["id"] == "456"

        manager.clear_history()
        assert manager.get_history() == []
    finally:
        shutil.rmtree(temp_dir)
