import pytest
from app.domains.shadowing.youtube.url_resolver import YoutubeUrlResolver
from app.shared.errors.exceptions import ValidationException


def test_resolve_standard_watch_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    vid = YoutubeUrlResolver.extract_video_id(url)
    assert vid == "dQw4w9WgXcQ"
    assert YoutubeUrlResolver.get_canonical_url(vid) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_resolve_watch_url_with_extra_params():
    url = "https://youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=share"
    vid = YoutubeUrlResolver.extract_video_id(url)
    assert vid == "dQw4w9WgXcQ"


def test_resolve_short_youtu_be_url():
    url = "https://youtu.be/dQw4w9WgXcQ?t=10"
    vid = YoutubeUrlResolver.extract_video_id(url)
    assert vid == "dQw4w9WgXcQ"


def test_resolve_shorts_url():
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    vid = YoutubeUrlResolver.extract_video_id(url)
    assert vid == "dQw4w9WgXcQ"


def test_resolve_raw_11_char_id():
    raw = "dQw4w9WgXcQ"
    vid = YoutubeUrlResolver.extract_video_id(raw)
    assert vid == "dQw4w9WgXcQ"


def test_invalid_url_raises_validation_exception():
    with pytest.raises(ValidationException):
        YoutubeUrlResolver.extract_video_id("https://vimeo.com/12345678")

    with pytest.raises(ValidationException):
        YoutubeUrlResolver.extract_video_id("not-a-valid-url")

    with pytest.raises(ValidationException):
        YoutubeUrlResolver.extract_video_id("")
