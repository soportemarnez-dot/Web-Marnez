import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-solo-para-desarrollo")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'marnez.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    UPLOAD_FOLDER = str(BASE_DIR / os.environ.get("UPLOAD_FOLDER", "uploads/cv"))
    MEDIA_FOLDER = str(BASE_DIR / os.environ.get("MEDIA_FOLDER", "uploads/media"))
    ALLOWED_CV_EXTENSIONS = {"pdf", "doc", "docx"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 1024)) * 1024 * 1024

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "capitalhumano@marnez.mx")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "marnez2026")
    COMERCIAL_EMAIL = os.environ.get("COMERCIAL_EMAIL", "comercial@marnez.mx")
    COMERCIAL_PASSWORD = os.environ.get("COMERCIAL_PASSWORD", "marnez2026")

    RESEND_API_KEY = (os.environ.get("RESEND_API_KEY") or "").strip()
    _from = (os.environ.get("RESEND_FROM") or "").strip()
    if (_from.startswith('"') and _from.endswith('"')) or (
        _from.startswith("'") and _from.endswith("'")
    ):
        _from = _from[1:-1].strip()
    RESEND_FROM = _from

    EMPRESA = {
        "nombre": "Marnez Desarrollos",
        "telefono": "+52 990 229 3374",
        "email": "hola@marnez.mx",
        "direccion": "Calle 21 #410, Col. Jardines de Mérida, C.P. 97135, Mérida, Yucatán",
        "mapa_query": "Marnez Desarrollos, Calle 21 410, Jardines de Merida, 97135 Merida, Yuc.",
        "facebook": "https://www.facebook.com/marnezdesarrollos",
        "instagram": "https://www.instagram.com/marnezdesarrollos/",
        "linkedin": "https://mx.linkedin.com/company/marnez-desarrollos",
        "tiktok": "https://www.tiktok.com/@marnezdesarrollosmid",
        "whatsapp": "https://wa.me/529902293374",
    }
