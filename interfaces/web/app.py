import logging
import os
import tempfile
from typing import Tuple, Optional
import gradio as gr

from enstruct.core.transcriber import EnstructTranscriber
from enstruct.core.translator import EnstructTranslator
from enstruct.tools.subtitle import SubtitleGenerator

# Configure logging
logger = logging.getLogger("enstruct.web.app")
logger.setLevel(logging.INFO)


def process_audio(
    audio_file: str,
    task: str,
    model_size: str,
    output_format: str,
    language: Optional[str] = None
) -> Tuple[str, str]:
    """Processes audio and generates specified format transcription or translation.

    Args:
        audio_file: Path to the audio file uploaded by user.
        task: Either "Transcribe" or "Translate to English".
        model_size: The model size selection (e.g. "tiny", "base", "large-v3").
        output_format: "srt", "vtt", or "txt".
        language: Optional language ISO code.

    Returns:
        A tuple of (Text Preview, Path to generated file).
    """
    if not audio_file:
        return "No audio file provided.", ""

    try:
        # Initialize appropriate core wrapper
        if task == "Translate to English":
            translator = EnstructTranslator(model_size=model_size)
            result = translator.translate(audio_file)
        else:
            lang_param = language.strip() if language and language.strip() else None
            transcriber = EnstructTranscriber(model_size=model_size)
            result = transcriber.transcribe(audio_file, language=lang_param)

        # Write result to a temporary file of requested format
        temp_dir = tempfile.gettempdir()
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        out_filename = f"{base_name}_{task.lower().replace(' ', '_')}.{output_format}"
        out_path = os.path.join(temp_dir, out_filename)

        generator = SubtitleGenerator()
        generator.generate(result["segments"], out_path, format=output_format)

        preview = result["text"][:2000]
        if len(result["text"]) > 2000:
            preview += "\n\n...[Preview truncated, download output file for full content]..."

        return preview, out_path

    except Exception as e:
        logger.error("Web processing error: %s", str(e))
        return f"An error occurred: {e}", ""


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
                audio_input = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Input Audio")
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
                text_preview = gr.Textbox(label="Text Preview (Truncated at 2000 chars)", interactive=False, lines=10)
                file_output = gr.File(label="Download Subtitle / Text File")

        submit_btn.click(
            fn=process_audio,
            inputs=[audio_input, task_input, model_input, format_input, lang_input],
            outputs=[text_preview, file_output]
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
