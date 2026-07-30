import click
import logging
import os
import sys
from typing import Optional

from enstruct.core.transcriber import EnstructTranscriber
from enstruct.core.translator import EnstructTranslator
from enstruct.tools.batch import BatchProcessor
from enstruct.tools.subtitle import SubtitleGenerator

# Configure console logging for CLI
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)  # Default CLI logging level


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output for debugging.')
def cli(verbose: bool) -> None:
    """Enstruct CLI - Transcribe. Structure. Free.

    An open-source audio transcription & translation toolkit.
    """
    if verbose:
        logger.setLevel(logging.INFO)
        # Also ensure package level loggers show info logs
        logging.getLogger("enstruct").setLevel(logging.INFO)


@cli.command()
@click.argument('audio', type=click.Path(exists=True, dir_okay=False))
@click.option('--language', '-l', default=None, help='ISO 639-1 language code of the input audio (e.g. "en", "es").')
@click.option('--output', '-o', default=None, help='Path to save the transcription file.')
@click.option('--format', '-f', default='srt', type=click.Choice(['srt', 'vtt', 'txt'], case_sensitive=False),
              help='Output format (srt, vtt, txt). Defaults to srt.')
def transcribe(audio: str, language: Optional[str], output: Optional[str], format: str) -> None:
    """Transcribe a single audio file to text or subtitles."""
    click.echo(f"Initializing transcription for {audio}...")
    try:
        transcriber = EnstructTranscriber()
        result = transcriber.transcribe(audio, language=language)

        if output:
            dest_path = output
        else:
            # Generate default output path in the current directory with the requested format
            base_name = os.path.splitext(os.path.basename(audio))[0]
            dest_path = f"{base_name}.{format.lower()}"

        generator = SubtitleGenerator()
        generator.generate(result["segments"], dest_path, format=format)
        click.echo(f"Successfully transcribed. Output saved to: {dest_path}")
    except Exception as e:
        click.echo(f"Error during transcription: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('audio', type=click.Path(exists=True, dir_okay=False))
@click.option('--output', '-o', default=None, help='Path to save the English translation.')
@click.option('--format', '-f', default='srt', type=click.Choice(['srt', 'vtt', 'txt'], case_sensitive=False),
              help='Output format (srt, vtt, txt). Defaults to srt.')
def translate(audio: str, output: Optional[str], format: str) -> None:
    """Translate non-English audio file into English text or subtitles."""
    click.echo(f"Initializing English translation for {audio}...")
    try:
        translator = EnstructTranslator()
        result = translator.translate(audio)

        if output:
            dest_path = output
        else:
            base_name = os.path.splitext(os.path.basename(audio))[0]
            dest_path = f"{base_name}_translated.{format.lower()}"

        generator = SubtitleGenerator()
        generator.generate(result["segments"], dest_path, format=format)
        click.echo(f"Successfully translated. Output saved to: {dest_path}")
    except Exception as e:
        click.echo(f"Error during translation: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('folder', type=click.Path(exists=True, file_okay=False))
@click.option('--output', '-o', required=True, help='Output folder to save all transcriptions.')
@click.option('--language', '-l', default=None, help='ISO 639-1 language code.')
@click.option('--format', '-f', default='srt', type=click.Choice(['srt', 'vtt', 'txt'], case_sensitive=False),
              help='Output format (srt, vtt, txt). Defaults to srt.')
def batch(folder: str, output: str, language: Optional[str], format: str) -> None:
    """Batch process an entire folder containing audio or video files."""
    click.echo(f"Batch processing folder {folder}...")
    try:
        processor = BatchProcessor()
        processor.process_folder(
            folder_path=folder,
            output_folder=output,
            language=language,
            format=format
        )
        click.echo("Batch processing finished.")
    except Exception as e:
        click.echo(f"Error during batch processing: {e}", err=True)
        sys.exit(1)


@cli.command('detect-language')
@click.argument('audio', type=click.Path(exists=True, dir_okay=False))
def detect_language(audio: str) -> None:
    """Detect the language of an audio file."""
    click.echo(f"Analyzing language of {audio}...")
    try:
        transcriber = EnstructTranscriber()
        lang_code = transcriber.detect_language(audio)
        click.echo(f"Detected Language Code: {lang_code}")
    except Exception as e:
        click.echo(f"Error during language detection: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
