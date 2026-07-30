import logging
import os
from typing import Dict, Any, Optional

try:
    import torch
except ImportError:
    torch = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    # Fallback/mock support for testing or environments without CTranslate2 compiled
    WhisperModel = None

# Configure logging
logger = logging.getLogger("enstruct.core.transcriber")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def detect_optimal_device() -> str:
    """Detects the optimal device for faster-whisper.

    Returns "cuda" if CUDA is available and torch is installed, else "cpu".
    """
    if torch is not None and torch.cuda.is_available():
        logger.info("CUDA device detected. Optimal device set to 'cuda'.")
        return "cuda"
    logger.info("CUDA device not detected. Optimal device set to 'cpu'.")
    return "cpu"


class EnstructTranscriber:
    """A wrapper class for faster-whisper providing robust audio transcription."""

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto"
    ) -> None:
        """Initializes the EnstructTranscriber with desired settings.

        Args:
            model_size: Size of the model to load (e.g., "tiny", "base", "large-v3").
            device: Computing device ("cuda", "cpu", or "auto").
            compute_type: Computation precision ("float16", "int8", "auto", etc.).
        """
        self.model_size = model_size
        self.compute_type = compute_type

        # Handle auto-device detection
        if device == "auto":
            self.device = detect_optimal_device()
        else:
            self.device = device

        logger.info(
            "Initializing WhisperModel with size='%s', device='%s', compute_type='%s'",
            self.model_size,
            self.device,
            self.compute_type
        )

        if WhisperModel is not None:
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception as e:
                logger.error("Failed to load WhisperModel: %s", str(e))
                raise RuntimeError(f"Could not load faster-whisper model: {e}") from e
        else:
            logger.warning(
                "faster-whisper is not installed or available in this context. "
                "WhisperModel operations will fail."
            )
            self.model = None

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """Transcribes the given audio file using faster-whisper.

        Args:
            audio_path: Path to the target audio file.
            language: ISO 639-1 language code (e.g. "en", "es"). If None, language is auto-detected.
            task: Task to perform, either "transcribe" or "translate".

        Returns:
            A dictionary containing:
                - "text": Whole transcribed text combined.
                - "segments": A list of dict segment info (start, end, text).
                - "language": Detected or specified language code.
                - "duration": Duration of the audio file in seconds.

        Raises:
            FileNotFoundError: If audio_path does not exist.
            RuntimeError: If WhisperModel isn't loaded or transcription fails.
        """
        if not os.path.exists(audio_path):
            logger.error("Audio path not found: %s", audio_path)
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self.model is None:
            logger.error("WhisperModel is not initialized.")
            raise RuntimeError("WhisperModel is not initialized or failed to load.")

        logger.info("Starting transcription for '%s' (task='%s')", audio_path, task)

        try:
            segments_generator, info = self.model.transcribe(
                audio_path,
                language=language,
                task=task
            )

            # Consume generator and build simple segment dictionary representation
            segments_list = []
            text_segments = []
            for segment in segments_generator:
                text_segments.append(segment.text)
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })

            full_text = "".join(text_segments).strip()

            result = {
                "text": full_text,
                "segments": segments_list,
                "language": info.language,
                "duration": info.duration
            }

            logger.info("Completed transcription for '%s'. Duration: %.2f seconds.", audio_path, info.duration)
            return result

        except Exception as e:
            logger.error("Error during transcription of '%s': %s", audio_path, str(e))
            raise RuntimeError(f"Transcription failed: {e}") from e

    def detect_language(self, audio_path: str) -> str:
        """Detects the language of the audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Detected language code.

        Raises:
            FileNotFoundError: If audio_path does not exist.
            RuntimeError: If language detection fails.
        """
        if not os.path.exists(audio_path):
            logger.error("Audio path not found: %s", audio_path)
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self.model is None:
            logger.error("WhisperModel is not initialized.")
            raise RuntimeError("WhisperModel is not initialized or failed to load.")

        logger.info("Detecting language for '%s'", audio_path)

        try:
            # We can use the transcribe method with a small segment or transcribe's built-in info
            # Or use WhisperModel.model.detect_language internally if exposed.
            # To be standard and safe, let's call transcribe with short duration/just enough to fetch info.
            # However, faster-whisper's transcribe method returns generator & info immediately without consuming.
            _, info = self.model.transcribe(audio_path)
            detected_lang = info.language
            logger.info("Detected language for '%s' is '%s' with probability %.2f", audio_path, detected_lang, info.language_probability)
            return detected_lang
        except Exception as e:
            logger.error("Error during language detection for '%s': %s", audio_path, str(e))
            raise RuntimeError(f"Language detection failed: {e}") from e
