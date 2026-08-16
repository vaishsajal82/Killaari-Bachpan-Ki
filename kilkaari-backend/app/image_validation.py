"""
image_validation.py — validates uploaded files by their actual binary
content (magic bytes / file signature), not by the filename extension or
the browser-supplied Content-Type header, either of which a malicious
upload can trivially lie about (e.g. a PHP/HTML/SVG payload renamed to
"photo.jpg").

Deliberately dependency-free: `python-magic` is the more commonly
recommended tool for this, but it wraps libmagic, a *system* library that
isn't installed by default on Render's (or most) standard Python build
images — getting it working reliably would need a Dockerfile or a custom
build step, adding real deployment risk for a fixed, small set of image
formats. For "is this actually one of these 4 image formats", checking
the well-known signature bytes directly is just as reliable and has zero
extra moving parts. If this project later needs to validate a much wider
range of file types, revisit python-magic/`filetype` then.

SVG is deliberately NOT in the allowed set: SVG is XML and can embed
<script>, making it a stored-XSS vector if ever served or rendered
directly — allowing it would undo the escaping work done elsewhere in
this project.
"""

from typing import Optional

# (signature bytes, offset, resulting extension, MIME type)
_SIGNATURES = [
    (b"\xff\xd8\xff", 0, "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "png", "image/png"),
    (b"GIF87a", 0, "gif", "image/gif"),
    (b"GIF89a", 0, "gif", "image/gif"),
    # WEBP: RIFF <4-byte size> WEBP — check both fixed parts, size varies.
    (b"RIFF", 0, "webp", "image/webp"),  # narrowed further below
]


def sniff_image(data: bytes) -> Optional[tuple[str, str]]:
    """Returns (extension, mime_type) if `data` is a recognized image
    format, or None if it isn't one of the formats this app accepts —
    regardless of what filename/extension/Content-Type came with it.
    """
    if len(data) < 12:
        return None

    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ("webp", "image/webp")

    for sig, offset, ext, mime in _SIGNATURES:
        if sig == b"RIFF":
            continue  # handled above with the extra WEBP check
        if data[offset:offset + len(sig)] == sig:
            return (ext, mime)

    return None
