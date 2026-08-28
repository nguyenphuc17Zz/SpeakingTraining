import asyncio
from typing import Any

from app.core.logging import logger
from app.domains.shadowing.contracts import TranscriptSource, VideoTranscriptProvider

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
    _YOUTUBE_TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    _YOUTUBE_TRANSCRIPT_API_AVAILABLE = False


class YouTubeTranscriptAdapter:
    """Fetches official Japanese captions (manual or auto-generated) using youtube-transcript-api."""

    def __init__(self):
        self.languages = ["ja", "ja-JP", "ja-Latn"]

    async def get_transcript(self, video_id: str) -> list[dict[str, Any]]:
        """
        Fetches transcript entries: list of dict with keys: 'text', 'start', 'duration'.
        Returns empty list if captions are unavailable or if language is not Japanese.
        """
        if not _YOUTUBE_TRANSCRIPT_API_AVAILABLE:
            logger.warning("[YouTubeTranscriptAdapter] youtube-transcript-api is not installed.")
            return []

        # Run synchronous YouTubeTranscriptApi in executor thread
        loop = asyncio.get_running_loop()
        try:
            entries = await loop.run_in_executor(None, self._fetch_sync, video_id)
            return entries
        except Exception as e:
            logger.info(f"[YouTubeTranscriptAdapter] No YouTube transcript found for {video_id}: {e}")
            return []

    def _fetch_sync(self, video_id: str) -> list[dict[str, Any]]:
        """Synchronous fetch logic with Japanese priority and language validation."""
        # 1. Try finding available transcript list (support both 1.x and legacy APIs)
        transcript_list = None
        try:
            if hasattr(YouTubeTranscriptApi, "list"):
                try:
                    transcript_list = YouTubeTranscriptApi().list(video_id)
                except Exception:
                    transcript_list = YouTubeTranscriptApi.list(video_id)
            elif hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            else:
                transcript_list = YouTubeTranscriptApi().list(video_id)
        except Exception as e:
            logger.info(f"[YouTubeTranscriptAdapter] Failed to list transcripts for {video_id}: {e}")
            return []

        if not transcript_list:
            return []

        # 2. Look for manual Japanese first, then generated Japanese, then any JA variant
        target_transcript = None
        for lang_code in ["ja", "ja-JP"]:
            try:
                target_transcript = transcript_list.find_manually_created_transcript([lang_code])
                break
            except Exception:
                pass

        if not target_transcript:
            for lang_code in ["ja", "ja-JP"]:
                try:
                    target_transcript = transcript_list.find_generated_transcript([lang_code])
                    break
                except Exception:
                    pass

        if not target_transcript:
            try:
                target_transcript = transcript_list.find_transcript(["ja", "ja-JP", "ja-Latn"])
            except Exception:
                pass

        if not target_transcript:
            logger.info(f"[YouTubeTranscriptAdapter] Video {video_id} has no Japanese transcript available.")
            return []

        data = target_transcript.fetch()
        formatted: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                raw_text = item.get("text", "").strip()
                start = float(item.get("start", 0.0))
                duration = float(item.get("duration", 0.0))
            else:
                raw_text = getattr(item, "text", "").strip()
                start = float(getattr(item, "start", 0.0))
                duration = float(getattr(item, "duration", 0.0))

            if not raw_text:
                continue
            formatted.append({
                "text": raw_text,
                "start": start,
                "duration": duration,
                "end": round(start + duration, 3),
            })

        return formatted
