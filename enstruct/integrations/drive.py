import json
import logging
import os
import sys
from typing import Optional, Dict, Any, List

logger = logging.getLogger("enstruct.integrations.drive")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class DriveManager:
    """Manages Google Drive mounting, folder initialization, file storage,

    and transcription session history for Google Colab environments,
    with graceful fallbacks for local execution.
    """

    MOUNT_POINT: str = "/content/drive"
    SAVE_SUBDIR: str = "MyDrive/Enstruct_Transcriptions"

    # Enstruct constants required for Colab workflows
    ENSTRUCT_ROOT: str = "/content/drive/MyDrive/Enstruct"
    OUTPUTS_DIR: str = "/content/drive/MyDrive/Enstruct/outputs"
    HISTORY_FILE: str = "/content/drive/MyDrive/Enstruct/history.json"

    # Local fallback constants
    LOCAL_ROOT: str = "./Enstruct_local"
    LOCAL_OUTPUTS_DIR: str = "./Enstruct_local/outputs"
    LOCAL_HISTORY_FILE: str = "./Enstruct_local/history.json"

    def __init__(self) -> None:
        """Initializes the DriveManager."""
        self.is_colab: bool = self._detect_colab()
        self.is_mounted: bool = False

    def _detect_colab(self) -> bool:
        """Detects whether the code is currently running inside Google Colab.

        Returns:
            True if running in Google Colab, False otherwise.
        """
        return "google.colab" in sys.modules

    def mount_drive(self) -> bool:
        """Mounts Google Drive under the configured mount point if in Google Colab.

        Returns:
            True if successfully mounted, False otherwise.
        """
        if not self.is_colab:
            logger.info("Not running in Google Colab. Google Drive mount skipped.")
            return False

        try:
            from google.colab import drive  # type: ignore
            logger.info("Attempting to mount Google Drive at '%s'...", self.MOUNT_POINT)
            drive.mount(self.MOUNT_POINT, force_remount=True)
            self.is_mounted = True
            logger.info("Google Drive successfully mounted.")
            return True
        except Exception as e:
            logger.error("Failed to mount Google Drive: %s", str(e))
            self.is_mounted = False
            return False

    def ensure_folders(self) -> None:
        """Ensures the required Enstruct folders exist in Google Drive (or local fallback)."""
        root_dir = self.ENSTRUCT_ROOT if (self.is_colab and self.is_mounted) else self.LOCAL_ROOT
        outputs_dir = self.OUTPUTS_DIR if (self.is_colab and self.is_mounted) else self.LOCAL_OUTPUTS_DIR

        try:
            os.makedirs(root_dir, exist_ok=True)
            os.makedirs(outputs_dir, exist_ok=True)
            logger.info("Successfully ensured Enstruct folder directories exist at: %s", root_dir)
        except Exception as e:
            logger.error("Failed to create Enstruct folder directories: %s", str(e))

    def get_save_directory(self) -> str:
        """Returns the full target path where files should be saved.

        Returns:
            The complete destination folder path string.
        """
        if self.is_colab and self.is_mounted:
            return self.OUTPUTS_DIR
        return self.LOCAL_OUTPUTS_DIR

    def _get_history_file_path(self) -> str:
        """Returns the active history file path depending on Colab mount status.

        Returns:
            The path to the history JSON file.
        """
        if self.is_colab and self.is_mounted:
            return self.HISTORY_FILE
        return self.LOCAL_HISTORY_FILE

    def save_file(self, filename: str, content: str) -> Optional[str]:
        """Saves text content (like subtitle or transcription) to the Google Drive directory.

        Args:
            filename: The name of the file (e.g. 'interview.srt').
            content: The text content to write.

        Returns:
            The full path of the saved file if successful, or None if skipped/failed.
        """
        # If in Colab but not mounted, try to mount first
        if self.is_colab and not self.is_mounted:
            if not os.path.exists(self.MOUNT_POINT):
                logger.warning("Drive mount point '%s' does not exist. Attempting to mount...", self.MOUNT_POINT)
                mounted = self.mount_drive()
                if not mounted:
                    logger.error("Cannot save file to Google Drive: Drive is not mounted.")
                    # Fallback to local save instead of failing
            else:
                self.is_mounted = True

        save_dir = self.get_save_directory()
        try:
            os.makedirs(save_dir, exist_ok=True)
            dest_path = os.path.join(save_dir, filename)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Successfully saved file: %s", dest_path)
            return dest_path
        except Exception as e:
            logger.error("Failed to save file: %s", str(e))
            return None

    def log_session(self, entry: dict) -> None:
        """Logs a session entry into the history JSON file.

        Args:
            entry: A dictionary containing details about the transcription session.
                   Expected keys: id, date, source, language, duration, model,
                                  format, output_path, status, error_message.
        """
        history_path = self._get_history_file_path()
        history_dir = os.path.dirname(history_path)

        try:
            os.makedirs(history_dir, exist_ok=True)
        except Exception as e:
            logger.error("Could not ensure directory for history file: %s", str(e))
            return

        data: Dict[str, Any] = {"sessions": []}

        # Attempt to read existing history
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "sessions" not in data or not isinstance(data["sessions"], list):
                    data["sessions"] = []
            except Exception as e:
                logger.warning("Failed to read existing history JSON, initializing fresh sessions list. Error: %s", str(e))
                data = {"sessions": []}

        # Append new session entry
        data["sessions"].append(entry)

        # Write back updated history
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Successfully logged session entry to: %s", history_path)
        except Exception as e:
            logger.error("Failed to write to history file at %s: %s", history_path, str(e))

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieves all logged session entries from the history JSON file.

        Returns:
            A list of dictionary session entries, or [] if missing or error.
        """
        history_path = self._get_history_file_path()
        if not os.path.exists(history_path):
            return []

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "sessions" in data and isinstance(data["sessions"], list):
                return data["sessions"]
            return []
        except Exception as e:
            logger.error("Failed to read history from %s: %s", history_path, str(e))
            return []

    def clear_history(self) -> None:
        """Clears all session logs by writing a fresh empty history structure."""
        history_path = self._get_history_file_path()
        history_dir = os.path.dirname(history_path)

        try:
            os.makedirs(history_dir, exist_ok=True)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump({"sessions": []}, f, indent=2)
            logger.info("Successfully cleared history logs.")
        except Exception as e:
            logger.error("Failed to clear history: %s", str(e))
