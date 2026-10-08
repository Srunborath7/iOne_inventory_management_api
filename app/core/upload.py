import asyncio
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import BadRequest


MAX_IMAGE_SIZE = 5 * 1024 * 1024
IMAGE_FORMATS = (
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
)


def get_upload_dir() -> Path:
    return settings.upload_dir



async def save_image(upload: UploadFile | None, folder: str) -> tuple[str, Path] | None:
    """Validate and store an image under uploads/<folder>/. Returns (url, path)."""
    if upload is None or not upload.filename:
        return None

    content = await upload.read(MAX_IMAGE_SIZE + 1)
    if not content:
        raise BadRequest("The uploaded image is empty.")
    if len(content) > MAX_IMAGE_SIZE:
        raise BadRequest("Image must be 5 MB or smaller.")

    image_format = next(
        (fmt for fmt in IMAGE_FORMATS if content.startswith(fmt[0])),
        None,
    )
    if (
        image_format is None
        and len(content) >= 12
        and content[:4] == b"RIFF"
        and content[8:12] == b"WEBP"
    ):
        image_format = (b"RIFF", ".webp", "image/webp")
    if image_format is None:
        raise BadRequest("Upload a PNG, JPEG, or WebP image.")

    _, extension, _ = image_format
    filename = f"{uuid4().hex}{extension}"
    directory = get_upload_dir() / folder
    destination = directory / filename
    await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(destination.write_bytes, content)
    return f"/uploads/{folder}/{filename}", destination



async def remove_image(image_url: str | None) -> None:
    if not image_url:
        return
    url_path = Path(image_url)
    file_path = get_upload_dir() / url_path.parent.name / url_path.name
    await asyncio.to_thread(file_path.unlink, missing_ok=True)