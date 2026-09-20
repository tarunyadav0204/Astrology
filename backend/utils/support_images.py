"""Bounded, image-only support uploads. Never persist the original file."""
import base64
import binascii
import io
import json
from threading import BoundedSemaphore

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000
MAX_IMAGE_SIDE = 8192
MAX_BASE64_LENGTH = 4 * ((MAX_IMAGE_BYTES + 2) // 3)
MAX_REQUEST_BYTES = MAX_BASE64_LENGTH + 128 * 1024
_DECODE_SLOTS = BoundedSemaphore(2)


async def read_support_json(request):
    # Bound even chunked requests before JSON decoding or image parsing.
    if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
        raise HTTPException(415, 'Use application/json for support messages.')
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise HTTPException(413, 'Support image must be 5 MB or smaller.')
        body.extend(chunk)
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError()
        return payload
    except (ValueError, UnicodeError):
        raise HTTPException(400, 'Invalid support request.')


def normalize_support_image(encoded):
    if encoded is None:
        return None
    if not _DECODE_SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Image uploads are busy. Please try again shortly.')
    try:
        if not isinstance(encoded, str) or len(encoded) > MAX_BASE64_LENGTH:
            raise ValueError()
        blob = base64.b64decode(encoded, validate=True)
        if not blob or len(blob) > MAX_IMAGE_BYTES:
            raise ValueError()
        # Restrict decoder selection; filenames and client MIME types are untrusted.
        with Image.open(io.BytesIO(blob), formats=['JPEG', 'PNG']) as original:
            if (original.width * original.height > MAX_IMAGE_PIXELS
                    or max(original.size) > MAX_IMAGE_SIDE
                    or getattr(original, 'n_frames', 1) != 1):
                raise ValueError()
            original.load()
            # A fresh pixel-only image carries no EXIF/GPS, comments, profiles,
            # appended content, or client-controlled filename into storage.
            converted = original.convert('RGB')
            clean = Image.new('RGB', converted.size)
            clean.paste(converted)
            output = io.BytesIO()
            clean.save(output, format='JPEG', quality=90)
        result = output.getvalue()
        if len(result) > MAX_IMAGE_BYTES:
            raise ValueError()
        return result
    except (ValueError, binascii.Error, OSError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(400, 'Attach a valid, non-animated JPEG or PNG, up to 5 MB and 12 megapixels.')
    finally:
        _DECODE_SLOTS.release()
