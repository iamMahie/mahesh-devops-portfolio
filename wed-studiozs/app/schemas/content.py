"""Validation for admin-managed media and contact details."""

from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, field_validator

from app.schemas.media import validate_image_url


class ReelInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    title: str = Field(min_length=2, max_length=150)
    video_url: str = Field(min_length=1, max_length=1000)
    poster_url: str = Field(min_length=1, max_length=1000)
    captions_url: str = Field(default="", max_length=1000)
    description: str = Field(default="", max_length=2000)
    display_order: int = Field(default=0, ge=0, le=100000)
    is_published: bool = False

    @field_validator("poster_url", "video_url", "captions_url")
    @classmethod
    def safe_media_location(cls, value: str) -> str:
        if not value:
            return value
        validate_image_url(value)
        if not value.startswith(("/static/", "https://")):
            raise ValueError("Use a permanent HTTPS URL or a local /static/ path.")
        return value

    @field_validator("video_url")
    @classmethod
    def direct_video(cls, value: str) -> str:
        if not urlsplit(value).path.lower().endswith((".mp4", ".webm")):
            raise ValueError("Use a direct .mp4 or .webm file, not an Instagram or YouTube page.")
        return value

    @field_validator("captions_url")
    @classmethod
    def caption_file(cls, value: str) -> str:
        if value and not urlsplit(value).path.lower().endswith(".vtt"):
            raise ValueError("Captions must point to a WebVTT (.vtt) file.")
        return value


class ReelRead(ReelInput):
    id: int


class SiteContentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    footer_text: str = Field(min_length=1, max_length=300)
    phone: str = Field(default="", max_length=30, pattern=r"^[+0-9() .-]*$")
    email: str = Field(default="", max_length=254)
    address: str = Field(default="", max_length=300)
    instagram_handle: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._]+$")

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        return str(TypeAdapter(EmailStr).validate_python(value)) if value else ""
