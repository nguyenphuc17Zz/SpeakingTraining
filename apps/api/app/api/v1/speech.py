import base64
from typing import Any

from fastapi import APIRouter, File, Form, Response, UploadFile
from pydantic import BaseModel

from app.domains.speech.contracts import STTOptions, STTResult, TTSOptions, TTSVoice
from app.domains.speech.stt_router import stt_router
from app.domains.speech.tts_router import tts_router
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/speech", tags=["Speech"])


class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str = "1"
    speaker_id: int = 1
    speed: float = 1.0
    pitch: float = 0.0
    provider: str | None = "voicevox"
    return_base64: bool = False


class SynthesizeResponse(BaseModel):
    audio_base64: str
    format: str = "wav"
    duration_ms: int | None = None
    processing_time_ms: int | None = None
    voice: str


@router.post("/transcribe", response_model=STTResult)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    model: str = Form("base"),
    language: str = Form("ja"),
    provider: str = Form("faster_whisper"),
):
    """Standalone audio transcription with Faster-Whisper."""
    if not audio_file:
        raise ValidationException("Audio file is required.")

    audio_bytes = await audio_file.read()
    if len(audio_bytes) == 0:
        raise ValidationException("Audio file cannot be empty.")

    options = STTOptions(model=model, language=language)
    return await stt_router.transcribe(
        audio_bytes=audio_bytes,
        provider_id=provider,
        options=options,
    )


@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
):
    """Standalone Japanese speech synthesis with VOICEVOX."""
    if not request.text.strip():
        raise ValidationException("Text to synthesize cannot be empty.")

    options = TTSOptions(
        voice_id=request.voice_id,
        speaker_id=request.speaker_id,
        speed=request.speed,
        pitch=request.pitch,
    )

    output = await tts_router.synthesize(
        text=request.text,
        provider_id=request.provider,
        options=options,
    )

    if request.return_base64:
        return SynthesizeResponse(
            audio_base64=base64.b64encode(output.audio_bytes).decode("utf-8"),
            format=output.format,
            duration_ms=output.duration_ms,
            processing_time_ms=output.processing_time_ms,
            voice=output.voice,
        )

    return Response(
        content=output.audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="speech.wav"'},
    )


@router.get("/voices", response_model=list[TTSVoice])
async def list_available_voices(provider: str | None = "voicevox"):
    """List available speaker voices for speech synthesis."""
    return await tts_router.get_available_voices(provider)


@router.get("/stt-models", response_model=list[dict[str, Any]])
async def list_stt_models(active_model: str = "base"):
    """List available Speech-to-Text models, download statuses, and hardware recommendations."""
    return stt_router.get_available_models(active_model=active_model)


class STTModelActionRequest(BaseModel):
    model_id: str


@router.post("/stt-models/download")
async def download_stt_model(request: STTModelActionRequest):
    """Downloads Faster-Whisper model in background."""
    import asyncio
    from fastapi import HTTPException
    from app.domains.speech.model_manager import whisper_model_manager

    model_id = request.model_id.lower().strip()
    try:
        path = await asyncio.to_thread(whisper_model_manager.download_model_sync, model_id)
        return {
            "success": True,
            "model_id": model_id,
            "path": path,
            "message": f"Đã tải thành công model {model_id}!",
            "models": whisper_model_manager.get_available_models_info(active_model=model_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể tải model {model_id}: {str(e)}")


@router.post("/stt-models/select")
async def select_stt_model(request: STTModelActionRequest):
    """Sets active default STT model and pre-warms it."""
    import asyncio
    from app.domains.speech.model_manager import whisper_model_manager

    model_id = request.model_id.lower().strip()
    whisper_model_manager.set_active_model(model_id)
    # Pre-warm model in background
    asyncio.create_task(asyncio.to_thread(whisper_model_manager.get_or_load_model, model_id))

    return {
        "success": True,
        "active_model": model_id,
        "message": f"Đã kích hoạt model Whisper {model_id} cho toàn hệ thống.",
        "models": whisper_model_manager.get_available_models_info(active_model=model_id),
    }


# ── Universal Furigana Resolver Endpoints ──

class RubyChunkDTO(BaseModel):
    text: str
    reading: str | None = None

class FuriganaRequest(BaseModel):
    text: str

class FuriganaResponse(BaseModel):
    text: str
    hiragana: str
    ruby: list[RubyChunkDTO]

class BatchFuriganaRequest(BaseModel):
    texts: list[str]

class BatchFuriganaResponse(BaseModel):
    results: list[FuriganaResponse]

@router.post("/furigana", response_model=FuriganaResponse)
async def resolve_furigana(
    request: FuriganaRequest,
):
    """Resolves Japanese text into structured Ruby tokens with Hiragana readings."""
    from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
    text = request.text or ""
    hiragana = JapaneseReadingResolver.to_hiragana(text)
    ruby_raw = JapaneseReadingResolver.to_ruby_chunks(text)
    ruby_dtos = [RubyChunkDTO(text=c.get("text", ""), reading=c.get("reading")) for c in ruby_raw]
    return FuriganaResponse(text=text, hiragana=hiragana, ruby=ruby_dtos)

@router.post("/furigana/batch", response_model=BatchFuriganaResponse)
async def resolve_batch_furigana(
    request: BatchFuriganaRequest,
):
    """Resolves multiple Japanese sentences into structured Ruby tokens."""
    from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
    results = []
    for text in request.texts:
        hiragana = JapaneseReadingResolver.to_hiragana(text)
        ruby_raw = JapaneseReadingResolver.to_ruby_chunks(text)
        ruby_dtos = [RubyChunkDTO(text=c.get("text", ""), reading=c.get("reading")) for c in ruby_raw]
        results.append(FuriganaResponse(text=text, hiragana=hiragana, ruby=ruby_dtos))
    return BatchFuriganaResponse(results=results)

