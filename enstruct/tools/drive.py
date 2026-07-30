import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("enstruct.tools.drive")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class DriveManager:
    """Manages Google Drive mounting and file storage for Google Colab environments,

    with graceful fallbacks for local execution.
    """

    MOUNT_POINT: str = "/content/drive"
    SAVE_SUBDIR: str = "MyDrive/Enstruct_Transcriptions"

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

    def get_save_directory(self) -> str:
        """Returns the full target path where files should be saved.

        Returns:
            The complete destination folder path string.
        """
        return os.path.join(self.MOUNT_POINT, self.SAVE_SUBDIR)

    def save_file(self, filename: str, content: str) -> Optional[str]:
        """Saves text content (like subtitle or transcription) to the Google Drive directory.

        Args:
            filename: The name of the file (e.g. 'interview.srt').
            content: The text content to write.

        Returns:
            The full path of the saved file if successful, or None if skipped/failed.
        """
        if not self.is_colab:
            logger.warning("Not in Google Colab. File saving to Drive was skipped.")
            return None

        # Verify mount status or try to mount if in Colab
        if not self.is_mounted:
            if not os.path.exists(self.MOUNT_POINT):
                logger.warning("Drive mount point '%s' does not exist. Attempting to mount...", self.MOUNT_POINT)
                mounted = self.mount_drive()
                if not mounted:
                    logger.error("Cannot save file: Google Drive is not mounted.")
                    return None

        save_dir = self.get_save_directory()
        try:
            os.makedirs(save_dir, exist_ok=True)
            dest_path = os.path.join(save_dir, filename)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Successfully saved file to Google Drive: %s", dest_path)
            return dest_path
        except Exception as e:
            logger.error("Failed to save file to Google Drive folder: %s", str(e))
            return None
