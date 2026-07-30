import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Tuple, Optional, Any, Dict, List
import gradio as gr

from enstruct.core.transcriber import EnstructTranscriber
from enstruct.core.translator import EnstructTranslator
from enstruct.tools.subtitle import SubtitleGenerator
from enstruct.integrations.drive import DriveManager

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
    """Processes audio based on source selection (Upload, Google Drive, or YouTube URL)

    and logs the session details (success or error) into the History system.

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

    # Log session variables
    session_id = str(uuid.uuid4())[:8]
    lang_logged = language if language and language.strip() else "Auto-detect"
    duration_logged = 0.0
    output_path_logged = "N/A"
    status_logged = "Error"
    error_logged = ""

    try:
        # Determine and resolve input file path based on source selection
        if source_type == "Upload / Microphone":
            if not upload_file:
                raise ValueError("No upload audio file provided.")
            input_file_path = upload_file
            status_msg = "Successfully processed uploaded audio file."

        elif source_type == "Google Drive":
            if not drive_file_path or not drive_file_path.strip():
                raise ValueError("No Google Drive path provided.")

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
                    raise FileNotFoundError(f"Google Drive file not found at: {target_path}")

            input_file_path = target_path
            status_msg = f"Successfully loaded file from Google Drive: {target_path}"

        elif source_type == "YouTube URL":
            if not youtube_url or not youtube_url.strip():
                raise ValueError("No YouTube URL provided.")

            if YouTubeDownloader is None:
                raise RuntimeError("YouTube Downloader is unavailable because 'yt-dlp' is not installed.")

            downloader = YouTubeDownloader()
            temp_dir = tempfile.gettempdir()
            # Download YouTube audio
            input_file_path = downloader.download_audio(youtube_url, output_dir=temp_dir)
            status_msg = "Successfully downloaded and extracted audio from YouTube."

        else:
            raise ValueError("Invalid source type selection.")

        # Initialize appropriate core wrapper and transcribe
        logger.info("Initializing model '%s' for task '%s'", model_size, task)
        if task == "Translate to English":
            translator = EnstructTranslator(model_size=model_size)
            result = translator.translate(input_file_path)
        else:
            lang_param = language.strip() if language and language.strip() else None
            transcriber = EnstructTranscriber(model_size=model_size)
            result = transcriber.transcribe(input_file_path, language=lang_param)

        duration_logged = float(result.get("duration", 0.0))
        lang_logged = result.get("language", lang_logged)

        # Write result to a temporary file of requested format
        temp_dir = tempfile.gettempdir()
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        out_filename = f"{base_name}_{task.lower().replace(' ', '_')}.{output_format}"
        local_out_path = os.path.join(temp_dir, out_filename)

        generator = SubtitleGenerator()
        generator.generate(result["segments"], local_out_path, format=output_format)
        output_path_logged = local_out_path

        # Try to save the output directly to Google Drive if possible/mounted
        drive_save_msg = ""
        if drive_manager.is_colab:
            with open(local_out_path, "r", encoding="utf-8") as f:
                content = f.read()
            drive_path = drive_manager.save_file(out_filename, content)
            if drive_path:
                drive_save_msg = f" Also saved directly to Google Drive: {drive_path}"
                output_path_logged = drive_path
            else:
                drive_save_msg = " [Warning: Could not save output to Google Drive. Check drive mount.]"

        preview = result["text"][:2000]
        if len(result["text"]) > 2000:
            preview += "\n\n...[Preview truncated, download output file for full content]..."

        final_status = f"{status_msg} Processing completed successfully.{drive_save_msg}"
        status_logged = "Success"

        # Log success session
        entry = {
            "id": session_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_type,
            "language": lang_logged,
            "duration": duration_logged,
            "model": model_size,
            "format": output_format,
            "output_path": output_path_logged,
            "status": status_logged,
            "error_message": error_logged
        }
        drive_manager.log_session(entry)

        return preview, local_out_path, final_status

    except Exception as e:
        logger.error("Web processing error: %s", str(e))
        error_logged = str(e)

        # Log failed session
        entry = {
            "id": session_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_type,
            "language": lang_logged,
            "duration": duration_logged,
            "model": model_size,
            "format": output_format,
            "output_path": output_path_logged,
            "status": status_logged,
            "error_message": error_logged
        }
        drive_manager.log_session(entry)

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


def refresh_history_table() -> List[List[str]]:
    """Retrieves session history entries and formats them for the gr.Dataframe.

    Returns:
        A list of lists with values matching the dataframe columns.
    """
    manager = DriveManager()
    history = manager.get_history()
    rows = []
    for item in history:
        duration_val = item.get("duration", 0.0)
        duration_str = f"{duration_val:.2f}s" if isinstance(duration_val, (int, float)) else str(duration_val)
        rows.append([
            item.get("date", ""),
            item.get("source", ""),
            item.get("language", ""),
            duration_str,
            item.get("model", ""),
            item.get("format", ""),
            item.get("status", "")
        ])
    return rows


def clear_history_and_refresh() -> List[List[str]]:
    """Clears all session logs and returns an empty list to clear the table."""
    manager = DriveManager()
    manager.clear_history()
    return []


def create_demo() -> gr.Blocks:
    """Builds and returns the Gradio interface Blocks object with three tabs."""
    with gr.Blocks(title="Enstruct - Transcribe. Structure. Free.") as demo:
        gr.Markdown(
            """
            # 🎙️ Enstruct
            ### Transcribe. Structure. Free.
            An open-source toolkit wrapping OpenAI's Whisper model (via `faster-whisper`)
            to provide fast, free, and robust transcription and translation.
            """
        )

        with gr.Tabs():
            # Tab 1: Transcribe / Translate
            with gr.Tab("🎙️ Transcribe / Translate"):
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
                            value="large-v3",
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

            # Tab 2: History
            with gr.Tab("📋 History"):
                gr.Markdown("### 📜 Session History logs and activity details.")
                refresh_btn = gr.Button("🔄 Refresh History", variant="primary")
                
                history_table = gr.Dataframe(
                    headers=["Date", "Source", "Language", "Duration", "Model", "Format", "Status"],
                    datatype=["str", "str", "str", "str", "str", "str", "str"],
                    col_count=(7, "fixed"),
                    label="Logged Sessions Table",
                    interactive=False
                )
                
                clear_btn = gr.Button("🗑️ Clear History", variant="stop")

                refresh_btn.click(
                    fn=refresh_history_table,
                    inputs=[],
                    outputs=[history_table]
                )

                clear_btn.click(
                    fn=clear_history_and_refresh,
                    inputs=[],
                    outputs=[history_table]
                )

            # Tab 3: About
            with gr.Tab("⚙️ About"):
                gr.Markdown(
                    """
                    ### 🎙️ Enstruct Project Information
                    
                    **Enstruct** is an elite, open-source audio transcription & translation utility. 
                    It wraps OpenAI's Whisper architectures via the lightning-fast `faster-whisper` package 
                    utilizing CTranslate2 to achieve real-time and robust subtitle generation completely for free.
                    
                    * **GitHub Repository:** [github.com/M5Devs/Enstruct](https://github.com/M5Devs/Enstruct)
                    * **License:** Licensed under the **AGPL v3 License**
                    * **Commercial Use:** *Commercial licenses are available for enterprise deployments, custom model fine-tuning, and premium API scaling.*
                    """
                )

        gr.Markdown(
            """
            ---
            *Enstruct is part of the professional open-source toolkit portfolio. Licensed under the AGPL v3 License.*
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
