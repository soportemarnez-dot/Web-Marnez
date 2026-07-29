"""Helpers de media: URLs públicas y guardado seguro de archivos del CMS."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from flask import current_app, url_for
from werkzeug.utils import secure_filename

MEDIA_PREFIX = "media:"
ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_VIDEO_EXT = {"mp4", "webm"}


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[áàäâ]", "a", text)
    text = re.sub(r"[éèëê]", "e", text)
    text = re.sub(r"[íìïî]", "i", text)
    text = re.sub(r"[óòöô]", "o", text)
    text = re.sub(r"[úùüû]", "u", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def is_media_ref(value: str | None) -> bool:
    return bool(value) and str(value).startswith(MEDIA_PREFIX)


def media_filename(value: str | None) -> str:
    if not value:
        return ""
    if is_media_ref(value):
        return value[len(MEDIA_PREFIX) :]
    return value


def desarrollo_img_url(slug: str, filename: str | None) -> str:
    """URL de imagen de desarrollo (static legacy o media subida)."""
    if not filename:
        return ""
    if is_media_ref(filename):
        return url_for("main.serve_media", filename=media_filename(filename))
    return url_for("static", filename=f"img/desarrollos/{slug}/{filename}")


def blog_img_url(imagen: str | None) -> str:
    if not imagen:
        return ""
    if is_media_ref(imagen):
        return url_for("main.serve_media", filename=media_filename(imagen))
    # Legacy: antal-02.jpg → img/desarrollos/antal/antal-02.jpg
    prefix = imagen.split("-")[0] if "-" in imagen else "blog"
    return url_for("static", filename=f"img/desarrollos/{prefix}/{imagen}")


def video_url(filename: str | None) -> str:
    if not filename:
        return ""
    if is_media_ref(filename):
        return url_for("main.serve_media", filename=media_filename(filename))
    return url_for("static", filename=f"video/{filename}")


def allowed_image(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_IMAGE_EXT


def allowed_video(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_VIDEO_EXT


def guardar_media(file_storage, *, as_video: bool = False) -> str:
    """Guarda en MEDIA_FOLDER y devuelve referencia media:uuid.ext."""
    original = secure_filename(file_storage.filename or "")
    if not original:
        raise ValueError("Archivo sin nombre.")
    ext = original.rsplit(".", 1)[-1].lower()
    if as_video:
        if ext not in ALLOWED_VIDEO_EXT:
            raise ValueError("El video debe ser MP4 o WEBM.")
    elif ext not in ALLOWED_IMAGE_EXT:
        raise ValueError("La imagen debe ser JPG, PNG, WEBP o GIF.")

    nombre = f"{uuid.uuid4().hex}.{ext}"
    folder = Path(current_app.config["MEDIA_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    file_storage.save(folder / nombre)
    return f"{MEDIA_PREFIX}{nombre}"


def borrar_media_si_aplica(ref: str | None) -> None:
    if not is_media_ref(ref):
        return
    path = Path(current_app.config["MEDIA_FOLDER"]) / media_filename(ref)
    if path.is_file():
        path.unlink(missing_ok=True)
