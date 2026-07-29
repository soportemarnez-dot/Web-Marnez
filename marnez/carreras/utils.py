import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_cv(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_CV_EXTENSIONS"]


def guardar_cv(file_storage) -> tuple[str, str]:
    """Guarda el archivo con un nombre único en disco y devuelve
    (nombre_guardado, nombre_original)."""
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    nombre_guardado = f"{uuid.uuid4().hex}.{ext}"
    destino = Path(current_app.config["UPLOAD_FOLDER"]) / nombre_guardado
    file_storage.save(destino)
    return nombre_guardado, original
