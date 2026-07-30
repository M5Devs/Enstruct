import logging
import os
from typing import Optional
from tqdm import tqdm
from enstruct.core.transcriber import EnstructTranscriber
from enstruct.tools.subtitle import SubtitleGenerator

logger = logging.getLogger("enstruct.tools.batch")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class BatchProcessor:
    """A processor class to process folders of audio/video files in batch using EnstructTranscriber."""

    SUPPORTED_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".mkv", ".webm"}

    def __init__(self, transcriber: Optional[EnstructTranscriber] = None) -> None:
        """Initializes the BatchProcessor.

        Args:
            transcriber: An optional custom EnstructTranscriber instance. If None,
                        a default transcriber is initialized.
        """
        self.transcriber = transcriber or EnstructTranscriber()
        self.subtitle_generator = SubtitleGenerator()

    def process_folder(
        self,
        folder_path: str,
        output_folder: str,
        language: Optional[str] = None,
        format: str = "srt"
    ) -> None:
        """Processes all supported audio and video files in the specified folder.

        Args:
            folder_path: Path to the input folder containing audio/video files.
            output_folder: Path where transcription outputs will be saved.
            language: ISO 639-1 language code. If None, language is auto-detected per file.
            format: Output format for the transcription ("srt", "vtt", or "txt").

        Raises:
            FileNotFoundError: If the folder_path does not exist.
        """
        if not os.path.exists(folder_path):
            logger.error("Input folder not found: %s", folder_path)
            raise FileNotFoundError(f"Input folder not found: {folder_path}")

        os.makedirs(output_folder, exist_ok=True)

        # Get all supported files in the folder (non-recursive for simplicity/cleanliness)
        try:
            all_files = os.listdir(folder_path)
        except Exception as e:
            logger.error("Failed to read folder contents of '%s': %s", folder_path, str(e))
            raise RuntimeError(f"Error reading directory: {e}") from e

        supported_files = [
            f for f in all_files
            if os.path.splitext(f.lower())[1] in self.SUPPORTED_EXTENSIONS
        ]

        if not supported_files:
            logger.warning("No supported files found in '%s'", folder_path)
            return

        logger.info(
            "Found %d files to process in '%s'. Output directory: '%s'. Format: '%s'",
            len(supported_files),
            folder_path,
            output_folder,
            format
        )

        for filename in tqdm(supported_files, desc="Batch Processing", unit="file"):
            input_file_path = os.path.join(folder_path, filename)
            logger.info("Processing file: %s", input_file_path)

            try:
                # Run transcription
                result = self.transcriber.transcribe(input_file_path, language=language)

                # Generate output path
                base_name, _ = os.path.splitext(filename)
                output_file_name = f"{base_name}.{format.lower()}"
                output_file_path = os.path.join(output_folder, output_file_name)

                # Write output
                self.subtitle_generator.generate(
                    segments=result["segments"],
                    output_path=output_file_path,
                    format=format
                )
                logger.info("Successfully processed '%s' -> '%s'", filename, output_file_path)

            except Exception as e:
                logger.error("Failed to process file '%s': %s", filename, str(e))
                # Continue processing other files even if one fails
