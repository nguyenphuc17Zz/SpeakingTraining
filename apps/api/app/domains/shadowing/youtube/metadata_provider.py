from datetime import datetime, timezone
import httpx

from app.core.logging import logger
from app.domains.shadowing.contracts import ShadowingVideoMetadata
from app.domains.shadowing.youtube.url_resolver import YoutubeUrlResolver
from app.shared.errors.exceptions import NotFoundException, ValidationException


class YoutubeMetadataProvider:
    """Fetches YouTube video metadata via public oEmbed endpoint with fallback parsing."""

    OEMBED_URL = "https://www.youtube.com/oembed"

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    async def get_metadata(self, video_id: str) -> ShadowingVideoMetadata:
        """
        Fetches title, author/channel, thumbnail, and duration for a given YouTube video ID.
        Uses YouTube's official public oEmbed API.
        """
        canonical_url = YoutubeUrlResolver.get_canonical_url(video_id)
        params = {"url": canonical_url, "format": "json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.OEMBED_URL, params=params)

                if resp.status_code == 404:
                    logger.warning(f"[YoutubeMetadataProvider] Video '{video_id}' not found or private (404).")
                    return ShadowingVideoMetadata(
                        video_id=video_id,
                        url=canonical_url,
                        canonical_url=canonical_url,
                        title="Unavailable Video",
                        channel_name="Unknown Channel",
                        source_status="unavailable",
                        metadata_fetched_at=datetime.now(timezone.utc),
                    )

                if resp.status_code == 401 or resp.status_code == 403:
                    logger.warning(f"[YoutubeMetadataProvider] Video '{video_id}' restricted/private ({resp.status_code}).")
                    return ShadowingVideoMetadata(
                        video_id=video_id,
                        url=canonical_url,
                        canonical_url=canonical_url,
                        title="Restricted Video",
                        channel_name="Unknown Channel",
                        source_status="restricted",
                        metadata_fetched_at=datetime.now(timezone.utc),
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", f"YouTube Video ({video_id})")
                    channel_name = data.get("author_name", "YouTube Creator")
                    thumbnail_url = data.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")

                    return ShadowingVideoMetadata(
                        video_id=video_id,
                        url=canonical_url,
                        canonical_url=canonical_url,
                        title=title,
                        channel_name=channel_name,
                        channel_id=None,
                        thumbnail_url=thumbnail_url,
                        duration_seconds=0,  # Updated during transcript resolution if available
                        published_at=None,
                        description=None,
                        language="ja",
                        source_status="available",
                        metadata_fetched_at=datetime.now(timezone.utc),
                    )

                # Non-200 unexpected status
                logger.warning(f"[YoutubeMetadataProvider] Unexpected oEmbed status {resp.status_code} for {video_id}")

        except httpx.RequestError as re:
            logger.warning(f"[YoutubeMetadataProvider] Network error fetching metadata for {video_id}: {re}")

        # Fallback default metadata object if network fails
        return ShadowingVideoMetadata(
            video_id=video_id,
            url=canonical_url,
            canonical_url=canonical_url,
            title=f"YouTube Video ({video_id})",
            channel_name="YouTube Creator",
            thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            duration_seconds=0,
            source_status="available",
            metadata_fetched_at=datetime.now(timezone.utc),
        )
