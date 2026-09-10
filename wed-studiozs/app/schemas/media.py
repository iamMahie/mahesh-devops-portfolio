"""Image locations shared by the publishing forms and public galleries."""

import re
from urllib.parse import urlsplit


def validate_image_url(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if re.fullmatch(r"/static/[A-Za-z0-9_./-]+", value) and ".." not in value.split("/"):
        return value
    if any(character.isspace() or ord(character) < 32 for character in value) or "\\" in value:
        raise ValueError("Use an http(s) image URL or a /static/ image path.")
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
        if parsed.username or parsed.password:
            valid = False
        parsed.port
    except ValueError as exc:
        raise ValueError("Use a valid image URL.") from exc
    if not valid:
        raise ValueError("Use an http(s) image URL or a /static/ image path.")
    return value
