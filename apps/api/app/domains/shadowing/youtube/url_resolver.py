import re
from urllib.parse import parse_qs, urlparse

from app.shared.errors.exceptions import ValidationException


class YoutubeUrlResolver:
    """Deterministic, robust YouTube URL parser and canonicalizer."""

    _VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")

    @classmethod
    def extract_video_id(cls, url: str) -> str:
        """
        Extracts 11-character YouTube video ID from various standard YouTube URL formats.
        Supports:
          - youtube.com/watch?v=...
          - youtu.be/...
          - youtube.com/shorts/...
          - youtube.com/embed/...
          - youtube.com/live/...
        Raises ValidationException for invalid URLs.
        """
        if not url or not isinstance(url, str):
            raise ValidationException("YouTube URL cannot be empty.")

        clean_url = url.strip()

        # If user directly pasted an 11-character video ID
        if cls._VIDEO_ID_REGEX.match(clean_url):
            return clean_url

        try:
            parsed = urlparse(clean_url)
        except Exception as e:
            raise ValidationException(f"Invalid URL structure: {e}")

        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain.startswith("m."):
            domain = domain[2:]

        video_id: str | None = None

        if domain in ("youtube.com", "youtube-nocookie.com"):
            path = parsed.path
            if path == "/watch":
                qs = parse_qs(parsed.query)
                v_list = qs.get("v")
                if v_list and len(v_list) > 0:
                    video_id = v_list[0]
            elif path.startswith("/shorts/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    video_id = parts[1]
            elif path.startswith("/embed/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    video_id = parts[1]
            elif path.startswith("/live/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    video_id = parts[1]
            elif path.startswith("/v/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    video_id = parts[1]
        elif domain == "youtu.be":
            parts = [p for p in parsed.path.split("/") if p]
            if parts:
                video_id = parts[0]

        if not video_id or not cls._VIDEO_ID_REGEX.match(video_id):
            raise ValidationException(
                f"Invalid YouTube URL: '{url}'. Please provide a valid YouTube video, shorts, or youtu.be link."
            )

        return video_id

    @classmethod
    def get_canonical_url(cls, video_id: str) -> str:
        """Returns normalized standard watch URL."""
        if not cls._VIDEO_ID_REGEX.match(video_id):
            raise ValidationException(f"Invalid video ID format: '{video_id}'")
        return f"https://www.youtube.com/watch?v={video_id}"
