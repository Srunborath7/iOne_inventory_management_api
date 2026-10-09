import asyncio
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
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


def _get_s3_client():
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError(
            "Install boto3 to use Supabase image storage: pip install boto3"
        ) from exc

    required = {
        "SUPABASE_S3_ENDPOINT": settings.supabase_s3_endpoint,
        "SUPABASE_S3_REGION": settings.supabase_s3_region,
        "SUPABASE_S3_ACCESS_KEY_ID": settings.supabase_s3_access_key_id,
        "SUPABASE_S3_SECRET_ACCESS_KEY": settings.supabase_s3_secret_access_key,
        "SUPABASE_STORAGE_BUCKET": settings.supabase_storage_bucket,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Supabase image storage is enabled but configuration is missing: "
            + ", ".join(missing)
        )

    return boto3.client(
        "s3",
        endpoint_url=settings.supabase_s3_endpoint,
        region_name=settings.supabase_s3_region,
        aws_access_key_id=settings.supabase_s3_access_key_id,
        aws_secret_access_key=settings.supabase_s3_secret_access_key,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )


def _public_object_url(key: str) -> str:
    endpoint = urlsplit(settings.supabase_s3_endpoint or "")
    host = endpoint.hostname or ""
    suffix = ".storage.supabase.co"
    if not host.endswith(suffix):
        raise RuntimeError("SUPABASE_S3_ENDPOINT must use the Supabase Storage hostname")
    project_ref = host[: -len(suffix)]
    return (
        f"https://{project_ref}.supabase.co/storage/v1/object/public/"
        f"{quote(settings.supabase_storage_bucket or '', safe='')}/{quote(key, safe='/')}"
    )


async def save_image(upload: UploadFile | None, folder: str) -> tuple[str, str] | None:
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
    if settings.image_storage_backend == "supabase":
        key = f"{folder}/{filename}"
        client = _get_s3_client()
        await asyncio.to_thread(
            client.put_object,
            Bucket=settings.supabase_storage_bucket,
            Key=key,
            Body=content,
            ContentType=image_format[2],
            CacheControl="public, max-age=31536000, immutable",
        )
        return _public_object_url(key), key

    directory = get_upload_dir() / folder
    destination = directory / filename
    await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(destination.write_bytes, content)
    return f"/uploads/{folder}/{filename}", str(destination)



async def remove_image(image_url: str | None) -> None:
    if not image_url:
        return

    if settings.image_storage_backend == "supabase" and image_url.startswith("https://"):
        parsed = urlsplit(image_url)
        prefix = f"/storage/v1/object/public/{settings.supabase_storage_bucket}/"
        if parsed.path.startswith(prefix):
            key = unquote(parsed.path[len(prefix):])
            client = _get_s3_client()
            await asyncio.to_thread(
                client.delete_object,
                Bucket=settings.supabase_storage_bucket,
                Key=key,
            )
        return

    url_path = Path(image_url)
    file_path = get_upload_dir() / url_path.parent.name / url_path.name
    await asyncio.to_thread(file_path.unlink, missing_ok=True)
