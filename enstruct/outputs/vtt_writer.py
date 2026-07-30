import math
from typing import List, Dict, Any


def format_vtt_timestamp(seconds: float) -> str:
    """Formats seconds into VTT timestamp format: HH:MM:SS.mmm.

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted timestamp string.
    """
    milliseconds = int(math.modf(seconds)[0] * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


class VTTWriter:
    """A writer class to export transcription segments in Web Video Text Tracks (VTT) format."""

    @staticmethod
    def write(segments: List[Dict[str, Any]], output_path: str) -> None:
        """Writes transcription segments to a VTT file.

        Args:
            segments: A list of segment dictionaries, each having 'start', 'end', and 'text'.
            output_path: Path to the output file.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for i, segment in enumerate(segments, 1):
                start_str = format_vtt_timestamp(segment["start"])
                end_str = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{text}\n\n")
