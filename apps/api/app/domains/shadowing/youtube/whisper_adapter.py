import asyncio
import os
import shutil
import tempfile
import uuid
from typing import Any

from app.core.logging import logger
from app.domains.shadowing.contracts import VideoTranscriptProvider
from app.domains.shadowing.youtube.url_resolver import YoutubeUrlResolver
from app.domains.speech.contracts import STTOptions
from app.domains.speech.stt_router import stt_router

try:
    import yt_dlp
    _YT_DLP_AVAILABLE = True
except ImportError:
    _YT_DLP_AVAILABLE = False


class WhisperFallbackAdapter(VideoTranscriptProvider):
    """
    Fallback transcript provider that downloads ephemeral temporary audio
    from YouTube and processes it using Faster-Whisper, then immediately purges the media.
    """

    def __init__(self, default_model: str = "base"):
        self.default_model = default_model

    async def get_transcript(
        self,
        video_id: str,
        custom_model: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extracts ephemeral audio for the YouTube video, transcribes with Faster-Whisper,
        and guarantees cleanup of all temporary media files.
        """
        if not _YT_DLP_AVAILABLE:
            logger.warning("[WhisperFallbackAdapter] yt-dlp is not available. Whisper fallback cannot download audio.")
            return []

        canonical_url = YoutubeUrlResolver.get_canonical_url(video_id)
        temp_dir = tempfile.mkdtemp(prefix=f"shadowing_ephemeral_{video_id}_")
        output_template = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex[:8]}.%(ext)s")

        model_name = custom_model or self.default_model

        try:
            # 1. Download temporary audio synchronously in executor thread
            loop = asyncio.get_running_loop()
            audio_path = await loop.run_in_executor(
                None, self._download_audio_sync, canonical_url, output_template
            )

            if not audio_path or not os.path.exists(audio_path):
                logger.warning(f"[WhisperFallbackAdapter] Failed to download temporary audio for {video_id}")
                return []

            # 2. Read audio bytes
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            # 3. Transcribe via Phase 3 STT Router
            options = STTOptions(
                language="ja",
                model=model_name,
                vad_filter=True,
            )
            stt_result = await stt_router.transcribe(audio_bytes=audio_bytes, options=options)

            if not stt_result.text.strip():
                logger.info(f"[WhisperFallbackAdapter] Whisper transcribed empty text for {video_id}")
                return []

            # 4. Convert word/segment timestamps into transcript format
            transcript_entries = self._format_stt_result_to_entries(stt_result)
            logger.info(
                f"[WhisperFallbackAdapter] Successfully generated {len(transcript_entries)} segments via Whisper ({model_name}) for {video_id}"
            )
            return transcript_entries

        except Exception as e:
            logger.error(f"[WhisperFallbackAdapter] Whisper transcription fallback failed for {video_id}: {e}", exc_info=True)
            return []
        finally:
            # 5. Storage Principle: ALWAYS delete temporary audio directory
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug(f"[WhisperFallbackAdapter] Purged temporary directory: {temp_dir}")
            except Exception as ce:
                logger.warning(f"[WhisperFallbackAdapter] Failed to purge temporary directory {temp_dir}: {ce}")

    def _download_audio_sync(self, url: str, output_template: str) -> str | None:
        """Downloads audio stream using yt-dlp."""
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ] if shutil.which("ffmpeg") else [],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find output file in directory
            parent = os.path.dirname(output_template)
            for fname in os.listdir(parent):
                full = os.path.join(parent, fname)
                if os.path.isfile(full):
                    return full
            return None
        except Exception as e:
            logger.warning(f"[WhisperFallbackAdapter] yt-dlp extraction error for {url}: {e}")
            return None

    def _format_stt_result_to_entries(self, stt_result: Any) -> list[dict[str, Any]]:
        """Converts word timestamps and text into formatted sentence/phrase level segments."""
        words = getattr(stt_result, "words", [])
        if not words:
            # Fallback single segment if no word timestamps
            duration_s = (stt_result.duration_ms or 5000) / 1000.0
            return [{
                "text": stt_result.text.strip(),
                "start": 0.0,
                "end": round(duration_s, 2),
                "duration": round(duration_s, 2),
            }]

        # Group words into sentence/clause-like chunks based on punctuation and pauses (>0.8s)
        entries: list[dict[str, Any]] = []
        current_words: list[Any] = []
        current_start: float = words[0].start_ms / 1000.0

        for i, w in enumerate(words):
            current_words.append(w.word)
            w_end_s = w.end_ms / 1000.0

            # Check pause to next word
            is_last = (i == len(words) - 1)
            pause_after = 0.0
            if not is_last:
                next_start_s = words[i + 1].start_ms / 1000.0
                pause_after = next_start_s - w_end_s

            is_punct = any(p in w.word for p in ["。", "！", "？", "!", "?", "、", "\n"])
            has_long_pause = pause_after > 0.85
            is_long_enough = (w_end_s - current_start) > 2.5

            if is_last or (is_punct and is_long_enough) or (has_long_pause and len(current_words) >= 3):
                chunk_text = "".join(current_words).strip()
                if chunk_text:
                    entries.append({
                        "text": chunk_text,
                        "start": round(current_start, 2),
                        "end": round(w_end_s, 2),
                        "duration": round(w_end_s - current_start, 2),
                    })
                current_words = []
                if not is_last:
                    current_start = words[i + 1].start_ms / 1000.0

        # Catch remaining
        if current_words:
            chunk_text = "".join(current_words).strip()
            if chunk_text:
                w_end_s = words[-1].end_ms / 1000.0
                entries.append({
                    "text": chunk_text,
                    "start": round(current_start, 2),
                    "end": round(w_end_s, 2),
                    "duration": round(w_end_s - current_start, 2),
                })

        return entries
