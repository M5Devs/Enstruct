import logging
import os
import tempfile
from typing import Tuple, Optional, Any, Dict
import gradio as gr

from enstruct.core.transcriber import EnstructTranscriber
from enstruct.core.translator import EnstructTranslator
from enstruct.tools.subtitle import SubtitleGenerator
from enstruct.tools.drive import DriveManager

# Try importing YouTubeDownloader; handle missing yt-dlp gracefully
try:
    from enstruct.tools.youtube import YouTubeDownloader
except Exception as e:
    YouTubeDownloader = None  # type: ignore

# Configure logging
logger = logging.getLogger("enstruct.web.app")
logger.setLevel(logging.INFO)


def process_audio_source(
    source_type: str,
    upload_file: Optional[str],
    drive_file_path: str,
    youtube_url: str,
    task: str,
    model_size: str,
    output_format: str,
    language: Optional[str] = None
) -> Tuple[str, str, str]:
    """Processes audio based on source selection (Upload, Google Drive, or YouTube URL).

    Args:
        source_type: "Upload / Microphone", "Google Drive", or "YouTube URL".
        upload_file: Audio file path from Upload/Microphone input.
        drive_file_path: Path to the target file in Google Drive.
        youtube_url: URL to the YouTube video.
        task: "Transcribe" or "Translate to English".
        model_size: Size of Whisper model to load.
        output_format: "srt", "vtt", or "txt".
        language: Optional language code.

    Returns:
        A tuple of (Text Preview, Local Output File Path, Status Message).
    """
    input_file_path = ""
    status_msg = ""
    drive_manager = DriveManager()

    try:
        # Determine and resolve input file path based on source selection
        if source_type == "Upload / Microphone":
            if not upload_file:
                return "No upload audio file provided.", "", "Error: Missing audio file."
            input_file_path = upload_file
            status_msg = "Successfully processed uploaded audio file."

        elif source_type == "Google Drive":
            if not drive_file_path or not drive_file_path.strip():
                return "No Google Drive path provided.", "", "Error: Missing Drive path."

            # Normalize drive path or resolve under typical mount point
            target_path = drive_file_path.strip()
            # If path doesn't start with /content/drive, let's see if it's relative to MyDrive
            if not target_path.startswith("/") and drive_manager.is_colab:
                target_path = os.path.join(drive_manager.MOUNT_POINT, "MyDrive", target_path)

            if not os.path.exists(target_path):
                # Drive might not be mounted, try to mount
                if drive_manager.is_colab:
                    logger.info("Attempting to auto-mount Google Drive...")
                    drive_manager.mount_drive()
                if not os.path.exists(target_path):
                    return (
                        f"Google Drive file not found at: {target_path}",
                        "",
                        "Error: File not found. Please ensure Google Drive is mounted and the path is correct."
                    )

            input_file_path = target_path
            status_msg = f"Successfully loaded file from Google Drive: {target_path}"

        elif source_type == "YouTube URL":
            if not youtube_url or not youtube_url.strip():
                return "No YouTube URL provided.", "", "Error: Missing YouTube URL."

            if YouTubeDownloader is None:
                return (
                    "YouTube Downloader is unavailable because 'yt-dlp' is not installed.",
                    "",
                    "Error: Missing dependency 'yt-dlp'. Install it with: pip install yt-dlp"
                )

            try:
                downloader = YouTubeDownloader()
                temp_dir = tempfile.gettempdir()
                # Download YouTube audio
                input_file_path = downloader.download_audio(youtube_url, output_dir=temp_dir)
                status_msg = "Successfully downloaded and extracted audio from YouTube."
            except Exception as e:
                logger.error("Failed downloading YouTube audio: %s", str(e))
                return f"Failed downloading YouTube video: {e}", "", "Error: YouTube download failed."

        else:
            return "Invalid source type selection.", "", "Error: Invalid source."

        # Initialize appropriate core wrapper and transcribe
        logger.info("Initializing model '%s' for task '%s'", model_size, task)
        if task == "Translate to English":
            translator = EnstructTranslator(model_size=model_size)
            result = translator.translate(input_file_path)
        else:
            lang_param = language.strip() if language and language.strip() else None
            transcriber = EnstructTranscriber(model_size=model_size)
            result = transcriber.transcribe(input_file_path, language=lang_param)

        # Write result to a temporary file of requested format
        temp_dir = tempfile.gettempdir()
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        out_filename = f"{base_name}_{task.lower().replace(' ', '_')}.{output_format}"
        local_out_path = os.path.join(temp_dir, out_filename)

        generator = SubtitleGenerator()
        generator.generate(result["segments"], local_out_path, format=output_format)

        # Try to save the output directly to Google Drive if possible/mounted
        drive_save_msg = ""
        if drive_manager.is_colab:
            with open(local_out_path, "r", encoding="utf-8") as f:
                content = f.read()
            drive_path = drive_manager.save_file(out_filename, content)
            if drive_path:
                drive_save_msg = f" Also saved directly to Google Drive: {drive_path}"
            else:
                drive_save_msg = " [Warning: Could not save output to Google Drive. Check drive mount.]"

        preview = result["text"][:2000]
        if len(result["text"]) > 2000:
            preview += "\n\n...[Preview truncated, download output file for full content]..."

        final_status = f"{status_msg} Processing completed successfully.{drive_save_msg}"
        return preview, local_out_path, final_status

    except Exception as e:
        logger.error("Web processing error: %s", str(e))
        return f"An error occurred: {e}", "", f"Error: {e}"


def on_source_change(source: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Toggles visibility of inputs based on selected Source radio option."""
    if source == "Upload / Microphone":
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    elif source == "Google Drive":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    elif source == "YouTube URL":
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)


def create_demo() -> gr.Blocks:
    """Builds and returns the Gradio interface Blocks object."""
    with gr.Blocks(title="Enstruct - Transcribe. Structure. Free.") as demo:
        gr.Markdown(
            """
            # 🎙️ Enstruct
            ### Transcribe. Structure. Free.
            An open-source toolkit wrapping OpenAI's Whisper model (via `faster-whisper`)
            to provide fast, free, and robust transcription and translation.
            """
        )

        with gr.Row():
            with gr.Column():
                source_input = gr.Radio(
                    choices=["Upload / Microphone", "Google Drive", "YouTube URL"],
                    value="Upload / Microphone",
                    label="Audio Source"
                )

                # Visibility-controlled inputs
                audio_upload = gr.Audio(
                    sources=["upload", "microphone"],
                    type="filepath",
                    label="Input Audio File",
                    visible=True
                )
                drive_path_input = gr.Textbox(
                    placeholder="e.g. MyDrive/Recordings/meeting.mp3 or absolute path",
                    label="Google Drive Path",
                    visible=False
                )
                youtube_url_input = gr.Textbox(
                    placeholder="e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    label="YouTube Video/Audio URL",
                    visible=False
                )

                task_input = gr.Radio(
                    choices=["Transcribe", "Translate to English"],
                    value="Transcribe",
                    label="Task"
                )
                model_input = gr.Dropdown(
                    choices=["tiny", "base", "small", "medium", "large-v3"],
                    value="base",
                    label="Whisper Model Size"
                )
                format_input = gr.Radio(
                    choices=["srt", "vtt", "txt"],
                    value="srt",
                    label="Output Format"
                )
                lang_input = gr.Textbox(
                    placeholder="Auto-detect (or enter code like 'es', 'fr', 'en')",
                    label="Language Code (Optional)"
                )
                submit_btn = gr.Button("Process Audio", variant="primary")

            with gr.Column():
                status_output = gr.Textbox(label="Status Message", interactive=False)
                text_preview = gr.Textbox(label="Text Preview (Truncated at 2000 chars)", interactive=False, lines=10)
                file_output = gr.File(label="Download Subtitle / Text File")

        # Source visibility logic handler
        source_input.change(
            fn=on_source_change,
            inputs=[source_input],
            outputs=[audio_upload, drive_path_input, youtube_url_input]
        )

        submit_btn.click(
            fn=process_audio_source,
            inputs=[
                source_input,
                audio_upload,
                drive_path_input,
                youtube_url_input,
                task_input,
                model_input,
                format_input,
                lang_input
            ],
            outputs=[text_preview, file_output, status_output]
        )

        gr.Markdown(
            """
            ---
            *Enstruct is part of the professional open-source toolkit portfolio. Licensed under the MIT License.*
            """
        )

    return demo


def main() -> None:
    """Starts the Gradio web server."""
    demo = create_demo()
    # Share set to False by default inside the sandbox
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
