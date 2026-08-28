import asyncio
import os
import tempfile
import time
from typing import Any

from app.core.logging import logger
from app.domains.speech.contracts import (
    STTComputeType,
    STTDevice,
    STTOptions,
    STTProvider,
    STTResult,
    WordTimestamp,
)
from app.domains.speech.errors import STTProviderError, STTUnavailableError


from app.domains.speech.model_manager import whisper_model_manager


class FasterWhisperAdapter(STTProvider):
    """Production Faster-Whisper Speech-to-Text adapter with model caching and async execution."""

    provider_id: str = "faster_whisper"

    def __init__(
        self,
        default_model: str = "base",
        default_device: str = "auto",
        default_compute_type: str = "auto",
    ):
        self.default_model = default_model
        self.default_device = default_device
        self.default_compute_type = default_compute_type

    @classmethod
    def _detect_hardware(cls, preferred_device: str, preferred_compute: str) -> tuple[str, str]:
        return whisper_model_manager.detect_hardware(preferred_device, preferred_compute)

    def _get_or_load_model(self, model_size: str, device: str, compute_type: str) -> Any:
        return whisper_model_manager.get_or_load_model(model_size, device, compute_type)

    def _transcribe_sync(
        self,
        audio_input: Any,
        options: STTOptions,
    ) -> tuple[str, float | None, list[WordTimestamp], float]:
        """Synchronous transcription executed in worker thread."""
        model = self._get_or_load_model(
            model_size=options.model,
            device=options.device.value,
            compute_type=options.compute_type.value,
        )

        try:
            segments, info = model.transcribe(
                audio_input,
                language=options.language,
                beam_size=options.beam_size,
                temperature=options.temperature,
                initial_prompt=options.initial_prompt,
                condition_on_previous_text=False,
                vad_filter=options.vad_filter,
                vad_parameters=dict(min_silence_duration_ms=800, threshold=0.30, speech_pad_ms=300) if options.vad_filter else None,
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4,
                word_timestamps=True,
            )

            full_text_list = []
            words_list: list[WordTimestamp] = []
            avg_logprob_list = []

            for segment in segments:
                full_text_list.append(segment.text.strip())
                if segment.avg_logprob is not None:
                    avg_logprob_list.append(segment.avg_logprob)

                if segment.words:
                    for w in segment.words:
                        words_list.append(
                            WordTimestamp(
                                word=w.word,
                                start_ms=int(w.start * 1000),
                                end_ms=int(w.end * 1000),
                                confidence=float(w.probability) if hasattr(w, "probability") else 1.0,
                            )
                        )

            full_text = " ".join(full_text_list).strip()

            # Calculate confidence from avg_logprob if available
            confidence = None
            if avg_logprob_list:
                import math

                avg_logprob = sum(avg_logprob_list) / len(avg_logprob_list)
                # Convert log probability to approximate confidence [0, 1]
                confidence = round(min(1.0, max(0.0, math.exp(avg_logprob))), 3)

            duration = float(info.duration) if hasattr(info, "duration") else None
            conf_val = confidence if confidence is not None else (info.language_probability if hasattr(info, "language_probability") else 1.0)
            return full_text, duration, words_list, conf_val
        except Exception as e:
            # Automatic CPU fallback if CUDA DLL / device execution encounters an issue
            err_str = str(e).lower()
            if "cublas" in err_str or "cuda" in err_str or "cudnn" in err_str:
                logger.warning(f"[FasterWhisper] CUDA execution failed ({e}). Falling back to CPU int8 model...")
                try:
                    cpu_model = self._get_or_load_model(
                        model_size=options.model,
                        device="cpu",
                        compute_type="int8",
                    )
                    segments, info = cpu_model.transcribe(
                        audio_input,
                        language=options.language,
                        beam_size=options.beam_size,
                        temperature=options.temperature,
                        initial_prompt=options.initial_prompt,
                        condition_on_previous_text=False,
                        vad_filter=options.vad_filter,
                        vad_parameters=dict(min_silence_duration_ms=250, threshold=0.35) if options.vad_filter else None,
                        no_speech_threshold=0.6,
                        compression_ratio_threshold=2.4,
                        word_timestamps=True,
                    )
                    full_text_list = []
                    words_list = []
                    for segment in segments:
                        full_text_list.append(segment.text.strip())
                        if segment.words:
                            for w in segment.words:
                                words_list.append(
                                    WordTimestamp(
                                        word=w.word,
                                        start_ms=int(w.start * 1000),
                                        end_ms=int(w.end * 1000),
                                        confidence=float(w.probability) if hasattr(w, "probability") else 1.0,
                                    )
                                )
                    full_text = " ".join(full_text_list).strip()
                    duration = float(info.duration) if hasattr(info, "duration") else None
                    conf_val = info.language_probability if hasattr(info, "language_probability") else 1.0
                    return full_text, duration, words_list, conf_val
                except Exception as cpu_err:
                    logger.error(f"[FasterWhisper] CPU fallback failed: {cpu_err}", exc_info=True)

            logger.error(f"[FasterWhisper] Transcription execution error: {e}", exc_info=True)
            raise STTProviderError(
                message=f"Faster-Whisper transcription failed: {str(e)}",
                provider_id=self.provider_id,
                raw_error=e,
            )

    async def transcribe(
        self,
        audio_bytes: bytes,
        options: STTOptions | None = None,
    ) -> STTResult:
        """Asynchronously transcribe audio bytes using thread pool."""
        if not audio_bytes or len(audio_bytes) < 64:
            return STTResult(
                text="",
                language=options.language if options else "ja",
                duration_ms=0,
                confidence=0.0,
                processing_time_ms=0,
                model=options.model if options else self.default_model,
                provider=self.provider_id,
                words=[],
                metadata={"status": "empty_audio"},
            )

        stt_opts = options or STTOptions(
            model=self.default_model,
            device=STTDevice(self.default_device) if self.default_device in [d.value for d in STTDevice] else STTDevice.AUTO,
            compute_type=STTComputeType(self.default_compute_type) if self.default_compute_type in [c.value for c in STTComputeType] else STTComputeType.AUTO,
        )

        start_time = time.perf_counter()
        temp_file_path = None

        try:
            # 1. Try high-speed in-memory audio decoding & gain normalization via AudioPreprocessor
            from app.domains.pronunciation.infrastructure.audio_preprocessor import AudioPreprocessor

            samples, sr, dur_sec = AudioPreprocessor.load_and_preprocess(audio_bytes)
            if len(samples) > 0:
                audio_input = samples
            else:
                # Suffix fallback for temporary file
                suffix = ".webm"
                if audio_bytes.startswith(b"RIFF"):
                    suffix = ".wav"
                elif audio_bytes.startswith(b"OggS"):
                    suffix = ".ogg"
                elif audio_bytes.startswith(b"ID3") or audio_bytes.startswith(b"\xff\xfb"):
                    suffix = ".mp3"

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(audio_bytes)
                    temp_file_path = tmp.name
                audio_input = temp_file_path

            # Run in worker threadpool to avoid blocking FastAPI event loop
            text, duration_sec, words, lang_prob = await asyncio.to_thread(
                self._transcribe_sync,
                audio_input,
                stt_opts,
            )

            proc_ms = int((time.perf_counter() - start_time) * 1000)
            duration_ms = int((duration_sec or dur_sec or 0) * 1000)

            logger.info(
                f"[FasterWhisper] Transcribed {len(audio_bytes)} bytes -> '{text}' in {proc_ms}ms (duration: {duration_ms}ms)"
            )

            return STTResult(
                text=text,
                language=stt_opts.language,
                duration_ms=duration_ms,
                confidence=lang_prob,
                processing_time_ms=proc_ms,
                model=stt_opts.model,
                provider=self.provider_id,
                words=words,
                metadata={
                    "beam_size": stt_opts.beam_size,
                    "vad_filter": False,
                },
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp audio file {temp_file_path}: {e}")
