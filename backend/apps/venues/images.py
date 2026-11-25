"""Image helpers: shrink uploads and convert them to WebP."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def to_webp(uploaded, max_edge: int, quality: int = 82):
    """Return (ContentFile, width, height) for a resized WebP copy of `uploaded`."""
    img = Image.open(uploaded)
    img = ImageOps.exif_transpose(img)  # respect phone camera rotation
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    name = Path(uploaded.name).stem[:80] + ".webp"
    return ContentFile(buf.getvalue(), name=name), img.width, img.height
