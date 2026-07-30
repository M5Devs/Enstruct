import logging
from typing import Dict, Any
from enstruct.core.transcriber import EnstructTranscriber

logger = logging.getLogger("enstruct.core.translator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class EnstructTranslator:
    """A translator class that wraps the EnstructTranscriber using task='translate'

    to translate any spoken language in the audio directly into English text.
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto"
    ) -> None:
        """Initializes the translator and its underlying EnstructTranscriber.

        Args:
            model_size: Size of the model to load (e.g., "tiny", "base", "large-v3").
            device: Computing device ("cuda", "cpu", or "auto").
            compute_type: Computation precision ("float16", "int8", "auto", etc.).
        """
        logger.info("Initializing EnstructTranslator")
        self.transcriber = EnstructTranscriber(
            model_size=model_size,
            device=device,
            compute_type=compute_type
        )

    def translate(self, audio_path: str) -> Dict[str, Any]:
        """Translates the audio file to English text.

        Args:
            audio_path: Path to the audio file.

        Returns:
            A dictionary containing:
                - "text": Translated English text combined.
                - "segments": A list of dict segment info (start, end, text).
                - "language": Detected language code.
                - "duration": Duration of the audio file in seconds.

        Raises:
            FileNotFoundError: If audio_path does not exist.
            RuntimeError: If translation/transcription fails.
        """
        logger.info("Translating audio file to English: %s", audio_path)
        # Using task="translate" is the standard Whisper approach for audio -> English translation
        return self.transcriber.transcribe(audio_path, task="translate")
