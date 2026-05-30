"""HTTP serving for decrypted images without writing plaintext files."""

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote, urlparse

from modules.utils.encryption import ImageEncryption


ROUTE_PREFIX = "/sdcpp-decrypted-image"
_TOKEN_SECRET = os.urandom(32)
_TOKENS = {}


@dataclass(frozen=True)
class DecryptedImageResponse:
    content: bytes
    media_type: str
    filename: str


def detect_image_media_type(data: bytes) -> Optional[str]:
    """Return an image media type from file magic bytes."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"BM"):
        return "image/bmp"
    return None


def get_request_base_url(request=None) -> str:
    """Build the browser-visible origin for URLs returned to Gradio."""
    if request is None:
        return ""

    headers = getattr(request, "headers", {}) or {}
    referer = headers.get("referer") or headers.get("origin")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    host = headers.get("x-forwarded-host") or headers.get("host")
    if not host:
        return ""

    proto = headers.get("x-forwarded-proto")
    if not proto:
        raw_request = getattr(request, "request", None)
        raw_url = getattr(raw_request, "url", None)
        proto = getattr(raw_url, "scheme", "http")

    return f"{proto}://{host}"


def _token_for_path(path: str) -> str:
    stat = os.stat(path)
    payload = f"{path}\0{stat.st_size}\0{stat.st_mtime_ns}".encode("utf-8")
    return hmac.new(_TOKEN_SECRET, payload, hashlib.sha256).hexdigest()


def create_decrypted_image_url(path: str, base_url: str = "") -> str:
    """Create a signed HTTP URL for an encrypted image path."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    token = _token_for_path(abs_path)
    _TOKENS[token] = abs_path

    filename = quote(os.path.basename(abs_path))
    return f"{base_url}{ROUTE_PREFIX}/{token}/{filename}"


def can_decrypt_image(path: str, encryptor: ImageEncryption) -> bool:
    """Check whether decrypting the file prefix yields a supported image."""
    try:
        return detect_image_media_type(encryptor.decrypt_file_prefix(path)) is not None
    except OSError:
        return False


def read_decrypted_image(token: str) -> DecryptedImageResponse:
    """Decrypt the image referenced by token and return bytes from memory."""
    path = _TOKENS.get(token)
    if not path:
        raise FileNotFoundError("Unknown decrypted image token.")

    expected_token = _token_for_path(path)
    if not hmac.compare_digest(token, expected_token):
        _TOKENS.pop(token, None)
        raise FileNotFoundError("Expired decrypted image token.")

    from modules.config import ConfigManager

    password = ConfigManager().get('encryption_password', '123')
    image_bytes = ImageEncryption(password).decrypt_image_bytes(path)
    media_type = detect_image_media_type(image_bytes)
    if media_type is None:
        raise ValueError("Decrypted bytes are not a supported image.")

    return DecryptedImageResponse(
        content=image_bytes,
        media_type=media_type,
        filename=os.path.basename(path),
    )


def register_decrypted_image_route(blocks):
    """Attach the decrypted image HTTP route to the Gradio FastAPI app."""
    app = getattr(blocks, "app", None)
    if app is None:
        raise RuntimeError("Unable to register decrypted image route.")

    if getattr(app.state, "sdcpp_decrypted_image_route_registered", False):
        return

    from fastapi import HTTPException
    from starlette.responses import Response

    async def serve_decrypted_image(token: str, filename: str = ""):
        try:
            image = read_decrypted_image(token)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        safe_filename = image.filename.replace('"', '')

        return Response(
            content=image.content,
            media_type=image.media_type,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Content-Disposition": f'inline; filename="{safe_filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    app.add_api_route(
        f"{ROUTE_PREFIX}/{{token}}/{{filename:path}}",
        serve_decrypted_image,
        methods=["GET"],
    )
    app.state.sdcpp_decrypted_image_route_registered = True
