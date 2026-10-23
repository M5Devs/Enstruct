import logging
import os
import tempfile
from typing import Optional, Union, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from enstruct.core.transcriber import EnstructTranscriber
from enstruct.tools.subtitle import SubtitleGenerator

logger = logging.getLogger("enstruct.api.server")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

app = FastAPI(
    title="Enstruct REST API",
    description="OpenAI-Compatible Audio Transcription REST API powered by Enstruct and faster-whisper.",
    version="0.1.0"
)

# Global transcriber cache per model_size
_transcribers: Dict[str, EnstructTranscriber] = {}


def get_transcriber(model_size: str) -> EnstructTranscriber:
    """Returns or initializes a cached EnstructTranscriber instance for a given model size."""
    if model_size not in _transcribers:
        logger.info("Initializing EnstructTranscriber for model '%s'", model_size)
        _transcribers[model_size] = EnstructTranscriber(model_size=model_size)
    return _transcribers[model_size]


@app.post("/v1/audio/transcriptions", response_model=None)
async def create_transcription(
    file: UploadFile = File(...),
    model: Optional[str] = Form("large-v3-turbo"),
    language: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    temperature: Optional[float] = Form(0.0)
) -> Union[JSONResponse, PlainTextResponse]:
    """OpenAI-compatible transcription endpoint.

    Accepts multipart/form-data audio uploads and transcribes them.
    Supported response formats: json, text, srt, vtt.
    """
    model_name = model or "large-v3-turbo"
    resp_fmt = (response_format or "json").lower()

    if resp_fmt not in ["json", "text", "srt", "vtt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported response_format '{resp_fmt}'. Must be one of: json, text, srt, vtt."
        )

    # Save uploaded file to temporary path
    temp_dir = tempfile.gettempdir()
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
    temp_file_path = os.path.join(temp_dir, f"upload_{os.urandom(8).hex()}{file_ext}")

    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)

        transcriber = get_transcriber(model_name)
        lang_param = language.strip() if language and language.strip() else None
        result = transcriber.transcribe(temp_file_path, language=lang_param)

        if resp_fmt == "json":
            return JSONResponse(content={"text": result["text"]})
        elif resp_fmt == "text":
            return PlainTextResponse(content=result["text"])
        else: # srt or vtt
            subtitle_gen = SubtitleGenerator()
            output_sub_path = os.path.join(temp_dir, f"output_{os.urandom(8).hex()}.{resp_fmt}")
            subtitle_gen.generate(result["segments"], output_sub_path, format=resp_fmt)
            with open(output_sub_path, "r", encoding="utf-8") as sf:
                sub_content = sf.read()
            if os.path.exists(output_sub_path):
                os.remove(output_sub_path)
            return PlainTextResponse(content=sub_content)

    except Exception as e:
        logger.error("API Error during transcription: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
