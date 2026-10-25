import base64
from io import BytesIO
import mimetypes
from pathlib import Path

from PIL import Image


# The OpenAI-compatible vision endpoints used by this project generally accept
# JPEG/PNG/WebP/GIF data URLs, but not BMP. Keep supported formats unchanged and
# normalize unsupported raster formats before building the request.
_SUPPORTED_IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def image_to_data_url(path: Path) -> str:
    '''
    判断图片后缀、读取图片进行 base64 编码，返回 data url
    '''
    mime, _ = mimetypes.guess_type(str(path))
    raw = path.read_bytes()

    if mime not in _SUPPORTED_IMAGE_MIMES:
        # In particular, BMP files are valid source images but are rejected by
        # the upstream vision API when sent as data:image/bmp URLs.
        try:
            with Image.open(BytesIO(raw)) as image:
                converted = BytesIO()
                image.convert("RGB").save(converted, format="PNG")
                raw = converted.getvalue()
            mime = "image/png"
        except (OSError, ValueError) as exc:
            raise ValueError(f"Unsupported image format for model input: {path}") from exc

    data = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{data}"

