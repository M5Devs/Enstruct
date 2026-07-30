from typing import List, Dict, Any


class TXTWriter:
    """A writer class to export transcription segments in plain text (TXT) format."""

    @staticmethod
    def write(segments: List[Dict[str, Any]], output_path: str) -> None:
        """Writes transcription text to a TXT file.

        Args:
            segments: A list of segment dictionaries, each having 'text'.
            output_path: Path to the output file.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment["text"].strip()
                if text:
                    f.write(f"{text}\n")
