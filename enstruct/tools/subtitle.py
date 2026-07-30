import logging
from typing import List, Dict, Any
from enstruct.outputs.srt_writer import SRTWriter
from enstruct.outputs.vtt_writer import VTTWriter
from enstruct.outputs.txt_writer import TXTWriter

logger = logging.getLogger("enstruct.tools.subtitle")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class SubtitleGenerator:
    """A tool class to manage generating various subtitle and text outputs from segments."""

    def generate(self, segments: List[Dict[str, Any]], output_path: str, format: str = "srt") -> None:
        """Generates a subtitle or text file from transcription segments.

        Args:
            segments: A list of segment dictionaries with 'start', 'end', and 'text' keys.
            output_path: Path where the output file should be saved.
            format: Output format, supporting "srt", "vtt", and "txt" (case-insensitive).

        Raises:
            ValueError: If an unsupported format is specified.
            Exception: If file writing fails.
        """
        fmt = format.lower()
        logger.info("Generating subtitle file with format '%s' at '%s'", fmt, output_path)

        if fmt == "srt":
            SRTWriter.write(segments, output_path)
        elif fmt == "vtt":
            VTTWriter.write(segments, output_path)
        elif fmt == "txt":
            TXTWriter.write(segments, output_path)
        else:
            logger.error("Unsupported subtitle format: %s", format)
            raise ValueError(f"Unsupported format '{format}'. Supported formats are: srt, vtt, txt")

        logger.info("Successfully generated subtitle file at '%s'", output_path)
