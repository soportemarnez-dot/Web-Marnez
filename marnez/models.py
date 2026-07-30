from datetime import datetime, UTC
import json
import re

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db

ROL_CAPITAL_HUMANO = "capital_humano"
ROL_COMERCIAL = "comercial"


class Usuario(UserMixin, db.Model):
    """Cuenta de panel (Capital Humano o Comercial)."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(40), nullable=False, default=ROL_CAPITAL_HUMANO, index=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def es_capital_humano(self) -> bool:
        return self.rol == ROL_CAPITAL_HUMANO

    @property
    def es_comercial(self) -> bool:
        return self.rol == ROL_COMERCIAL


class Vacante(db.Model):
    __tablename__ = "vacantes"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    ubicacion = db.Column(db.String(120), nullable=False, default="Mérida, Yucatán")
    modalidad = db.Column(db.String(60), nullable=False, default="Presencial")
    tipo_contrato = db.Column(db.String(60), nullable=False, default="Tiempo completo")
    descripcion = db.Column(db.Text, nullable=False)
    requisitos = db.Column(db.Text, nullable=False)
    ofrecemos = db.Column(db.Text, nullable=True)
    salario = db.Column(db.String(120), nullable=True)
    correo_1 = db.Column(db.String(160), nullable=True)
    correo_2 = db.Column(db.String(160), nullable=True)
    correo_3 = db.Column(db.String(160), nullable=True)
    # Enlaces a otras plataformas (OCC, Computrabajo, etc.)
    enlace_occ = db.Column(db.String(500), nullable=True)
    enlace_extra_nombre = db.Column(db.String(80), nullable=True)
    enlace_extra_url = db.Column(db.String(500), nullable=True)
    activa = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    actualizado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    creado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    creado_por = db.relationship("Usuario", backref="vacantes")
    postulaciones = db.relationship(
        "Postulacion", backref="vacante", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def total_postulaciones(self) -> int:
        return self.postulaciones.count()

    def correos_destino(self) -> list[str]:
        return [c for c in (self.correo_1, self.correo_2, self.correo_3) if c and "@" in c]

    @property
    def salario_display(self) -> str | None:
        """Formatea números sueltos como $10,000; deja texto libre igual."""
        if not self.salario:
            return None
        raw = str(self.salario).strip()
        # Solo dígitos / separadores → formato moneda
        if re.fullmatch(r"[\d\s,\.]+", raw):
            digits = re.sub(r"[^\d]", "", raw)
            if digits:
                return f"${int(digits):,}"
        # Si ya trae $ pero es un solo número, normalizar
        if re.fullmatch(r"\$?\s*[\d\s,\.]+", raw):
            digits = re.sub(r"[^\d]", "", raw)
            if digits:
                return f"${int(digits):,}"
        return raw

    @property
    def creado_en_fmt(self) -> str:
        if not self.creado_en:
            return "—"
        dt = self.creado_en
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return dt.strftime("%d/%m/%Y")

    def enlaces_externos(self) -> list[dict]:
        """Lista de {nombre, url} para la ficha pública."""
        links = []
        if self.enlace_occ:
            links.append({"nombre": "Ver en OCC", "url": self.enlace_occ})
        if self.enlace_extra_url:
            links.append(
                {
                    "nombre": self.enlace_extra_nombre or "Otra publicación",
                    "url": self.enlace_extra_url,
                }
            )
        return links


class Postulacion(db.Model):
    """Aplicación de un candidato a una vacante concreta o candidatura espontánea."""

    __tablename__ = "postulaciones"

    id = db.Column(db.Integer, primary_key=True)
    vacante_id = db.Column(db.Integer, db.ForeignKey("vacantes.id"), nullable=True)

    nombre = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    telefono = db.Column(db.String(40), nullable=False)
    puesto_deseado = db.Column(db.String(160), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)

    cv_filename = db.Column(db.String(255), nullable=False)
    cv_nombre_original = db.Column(db.String(255), nullable=False)

    estado = db.Column(db.String(30), nullable=False, default="Nuevo")
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    @property
    def es_espontanea(self) -> bool:
        return self.vacante_id is None


class AjustesHR(db.Model):
    """Configuración global de Capital Humano (correos de notificación)."""

    __tablename__ = "ajustes_hr"

    id = db.Column(db.Integer, primary_key=True)
    correo_1 = db.Column(db.String(160), nullable=True)
    correo_2 = db.Column(db.String(160), nullable=True)
    correo_3 = db.Column(db.String(160), nullable=True)

    def correos_destino(self) -> list[str]:
        return [c for c in (self.correo_1, self.correo_2, self.correo_3) if c and "@" in c]

    @classmethod
    def get_or_create(cls):
        row = cls.query.first()
        if row:
            return row
        row = cls()
        db.session.add(row)
        db.session.commit()
        return row


class AjustesComercial(db.Model):
    """Datos públicos de contacto + correos de cotización / asesores."""

    __tablename__ = "ajustes_comercial"

    id = db.Column(db.Integer, primary_key=True)
    telefono = db.Column(db.String(60), nullable=True)
    email = db.Column(db.String(160), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    mapa_query = db.Column(db.String(255), nullable=True)
    # Número WhatsApp (solo dígitos con lada país, ej. 529902293374)
    whatsapp = db.Column(db.String(40), nullable=True)
    facebook = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    tiktok = db.Column(db.String(255), nullable=True)
    # Correos que reciben el formulario de contacto / cotización
    correo_1 = db.Column(db.String(160), nullable=True)
    correo_2 = db.Column(db.String(160), nullable=True)
    correo_3 = db.Column(db.String(160), nullable=True)

    def correos_destino(self) -> list[str]:
        return [c for c in (self.correo_1, self.correo_2, self.correo_3) if c and "@" in c]

    @property
    def whatsapp_url(self) -> str:
        digits = "".join(ch for ch in (self.whatsapp or "") if ch.isdigit())
        if not digits:
            return "https://wa.me/529902293374"
        return f"https://wa.me/{digits}"

    def as_empresa_dict(self, defaults: dict | None = None) -> dict:
        base = dict(defaults or {})
        base.update(
            {
                "telefono": self.telefono or base.get("telefono", ""),
                "email": self.email or base.get("email", ""),
                "direccion": self.direccion or base.get("direccion", ""),
                "mapa_query": self.mapa_query or base.get("mapa_query", ""),
                "whatsapp": self.whatsapp_url,
                "facebook": self.facebook or base.get("facebook", ""),
                "instagram": self.instagram or base.get("instagram", ""),
                "linkedin": self.linkedin or base.get("linkedin", ""),
                "tiktok": self.tiktok or base.get("tiktok", ""),
            }
        )
        if "nombre" not in base:
            base["nombre"] = "Marnez Desarrollos"
        return base

    @classmethod
    def get_or_create(cls, defaults: dict | None = None):
        row = cls.query.first()
        if row:
            return row
        d = defaults or {}
        wa = d.get("whatsapp") or ""
        digits = "".join(ch for ch in wa.replace("https://wa.me/", "") if ch.isdigit())
        row = cls(
            telefono=d.get("telefono"),
            email=d.get("email"),
            direccion=d.get("direccion"),
            mapa_query=d.get("mapa_query"),
            whatsapp=digits or "529902293374",
            facebook=d.get("facebook"),
            instagram=d.get("instagram"),
            linkedin=d.get("linkedin"),
            tiktok=d.get("tiktok"),
            correo_1=d.get("email"),
        )
        db.session.add(row)
        db.session.commit()
        return row


class Lead(db.Model):
    """Contacto general / interés en un desarrollo, desde el formulario de Contacto."""

    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    telefono = db.Column(db.String(40), nullable=False)
    desarrollo_interes = db.Column(db.String(120), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    titulo = db.Column(db.String(220), nullable=False)
    resumen = db.Column(db.Text, nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.String(255), nullable=True)
    font_size = db.Column(db.String(20), nullable=False, default="base")
    publicado = db.Column(db.Boolean, default=True, nullable=False, index=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    actualizado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Desarrollo(db.Model):
    __tablename__ = "desarrollos"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(160), nullable=False)
    tagline = db.Column(db.String(220), nullable=True)
    ubicacion = db.Column(db.String(220), nullable=True)
    resumen = db.Column(db.Text, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    amenidades_json = db.Column(db.Text, nullable=False, default="[]")
    precio_desde = db.Column(db.Integer, nullable=False, default=0)
    enganche_min_pct = db.Column(db.Integer, nullable=False, default=10)
    plazos_json = db.Column(db.Text, nullable=False, default="[12, 24, 36]")
    estatus = db.Column(db.String(120), nullable=True)
    portada = db.Column(db.String(255), nullable=True)
    hero_extra = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    video_poster = db.Column(db.String(255), nullable=True)
    tour_360 = db.Column(db.String(500), nullable=True)
    video_youtube = db.Column(db.String(80), nullable=True)
    mapa_query = db.Column(db.String(255), nullable=True)
    mapa_img = db.Column(db.String(255), nullable=True)
    orden = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    actualizado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    imagenes = db.relationship(
        "DesarrolloImagen",
        backref="desarrollo",
        cascade="all, delete-orphan",
        order_by="DesarrolloImagen.orden",
        lazy="joined",
    )

    @property
    def amenidades(self) -> list:
        try:
            return json.loads(self.amenidades_json or "[]")
        except (TypeError, ValueError):
            return []

    @amenidades.setter
    def amenidades(self, value):
        self.amenidades_json = json.dumps(value or [], ensure_ascii=False)

    @staticmethod
    def _normalizar_plazos(raw) -> list[dict]:
        """Acepta [12,24] o [{"meses":12,"interes_anual_pct":0}, ...]."""
        if not raw:
            return []
        out = []
        for item in raw:
            if isinstance(item, dict):
                try:
                    meses = int(item.get("meses") or 0)
                    interes = float(item.get("interes_anual_pct") or 0)
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    meses = int(item)
                    interes = 0.0
                except (TypeError, ValueError):
                    continue
            if meses <= 0:
                continue
            out.append({"meses": meses, "interes_anual_pct": max(0.0, interes)})
        return out

    @property
    def plazos(self) -> list[dict]:
        try:
            raw = json.loads(self.plazos_json or "[]")
        except (TypeError, ValueError):
            return []
        return self._normalizar_plazos(raw)

    @plazos.setter
    def plazos(self, value):
        self.plazos_json = json.dumps(self._normalizar_plazos(value), ensure_ascii=False)

    @property
    def plazos_meses(self) -> list:
        """Compat: lista de meses (sin interés). Preferir `.plazos`."""
        return [p["meses"] for p in self.plazos]

    @plazos_meses.setter
    def plazos_meses(self, value):
        self.plazos = value

    @property
    def galeria_count(self) -> int:
        return len([i for i in self.imagenes if i.tipo == "galeria"])


class DesarrolloImagen(db.Model):
    __tablename__ = "desarrollo_imagenes"

    id = db.Column(db.Integer, primary_key=True)
    desarrollo_id = db.Column(db.Integer, db.ForeignKey("desarrollos.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(40), nullable=False, default="galeria")
    orden = db.Column(db.Integer, nullable=False, default=0)
