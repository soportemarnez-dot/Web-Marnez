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

    # Estados de revisión (estilo OCC / Indeed)
    ESTADO_NUEVO = "nuevo"
    ESTADO_INTERES = "interes"
    ESTADO_DUDA = "duda"
    ESTADO_DESCARTADO = "descartado"
    ESTADOS = {
        ESTADO_NUEVO: "Sin revisar",
        ESTADO_INTERES: "Me interesa",
        ESTADO_DUDA: "Por definir",
        ESTADO_DESCARTADO: "Descartado",
    }

    id = db.Column(db.Integer, primary_key=True)
    vacante_id = db.Column(db.Integer, db.ForeignKey("vacantes.id"), nullable=True)

    nombre = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    telefono = db.Column(db.String(40), nullable=False)
    puesto_deseado = db.Column(db.String(160), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)

    cv_filename = db.Column(db.String(255), nullable=False)
    cv_nombre_original = db.Column(db.String(255), nullable=False)

    estado = db.Column(db.String(30), nullable=False, default=ESTADO_NUEVO)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    @property
    def es_espontanea(self) -> bool:
        return self.vacante_id is None

    @property
    def cv_extension(self) -> str:
        name = (self.cv_nombre_original or self.cv_filename or "").rsplit(".", 1)
        return name[-1].lower() if len(name) == 2 else ""

    @property
    def cv_se_puede_previsualizar(self) -> bool:
        """PDF se puede ver en el navegador; Word requiere descarga."""
        return self.cv_extension == "pdf"

    @property
    def estado_key(self) -> str:
        raw = (self.estado or self.ESTADO_NUEVO).strip().lower()
        # Compatibilidad con valor legacy "Nuevo"
        if raw in ("nuevo", "new", ""):
            return self.ESTADO_NUEVO
        if raw in self.ESTADOS:
            return raw
        return self.ESTADO_NUEVO

    @property
    def estado_label(self) -> str:
        return self.ESTADOS.get(self.estado_key, "Sin revisar")


class PlantillaEmail(db.Model):
    """Plantilla HTML editable para correos a candidatos (CH)."""

    __tablename__ = "plantillas_email"

    TIPO_DESCARTADO = "descartado"
    TIPO_CIERRE = "cierre_vacante"
    TIPOS = {
        TIPO_DESCARTADO: "Agradecimiento al descartar",
        TIPO_CIERRE: "Cierre / pausa de vacante",
    }
    VARIABLES = (
        ("{{nombre}}", "Nombre del candidato"),
        ("{{email}}", "Correo del candidato"),
        ("{{puesto}}", "Puesto deseado o título"),
        ("{{vacante}}", "Título de la vacante"),
        ("{{empresa}}", "Nombre de la empresa"),
        ("{{fecha}}", "Fecha de hoy"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(40), nullable=False, index=True)
    asunto = db.Column(db.String(200), nullable=False)
    cuerpo_html = db.Column(db.Text, nullable=False)
    activa = db.Column(db.Boolean, default=False, nullable=False)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    actualizado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    @property
    def tipo_label(self) -> str:
        return self.TIPOS.get(self.tipo, self.tipo)

    @classmethod
    def activa_para(cls, tipo: str):
        return cls.query.filter_by(tipo=tipo, activa=True).first()

    def activar_unica(self) -> None:
        """Activa esta plantilla y desactiva las demás del mismo tipo."""
        for otra in self.query.filter_by(tipo=self.tipo, activa=True).all():
            if otra.id != self.id:
                otra.activa = False
        self.activa = True


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


def _hex_to_rgb_str(hex_color: str, fallback: str) -> str:
    raw = (hex_color or "").strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return fallback
    try:
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
    except ValueError:
        return fallback
    return f"{r} {g} {b}"


def _rgb_str_to_hex(rgb: str, fallback: str = "#c9a962") -> str:
    parts = (rgb or "").strip().split()
    if len(parts) != 3:
        return fallback
    try:
        r, g, b = (max(0, min(255, int(p))) for p in parts)
    except ValueError:
        return fallback
    return f"#{r:02x}{g:02x}{b:02x}"


class AjustesDiseno(db.Model):
    """Colores, imágenes y secciones del inicio editables (Nivel A + B)."""

    __tablename__ = "ajustes_diseno"

    HOME_SECCIONES_DEFAULT = [
        {"id": "hero", "label": "Hero principal", "visible": True, "orden": 0},
        {"id": "certificaciones", "label": "Cifras de la empresa", "visible": True, "orden": 1},
        {"id": "desarrollos", "label": "Proyectos disponibles", "visible": True, "orden": 2},
        {"id": "entregados", "label": "Proyectos entregados", "visible": True, "orden": 3},
        {"id": "nosotros", "label": "Nosotros (resumen)", "visible": True, "orden": 4},
        {"id": "testimonios", "label": "Testimonios", "visible": True, "orden": 5},
        {"id": "blog", "label": "Blog", "visible": True, "orden": 6},
        {"id": "unete", "label": "Únete a Nosotros", "visible": True, "orden": 7},
    ]

    DEFAULTS = {
        "color_ink": "15 17 21",
        "color_panel": "23 26 33",
        "color_gold": "201 169 98",
        "color_goldlight": "228 207 156",
        "color_cream": "244 239 230",
        "color_ink_light": "250 249 246",
        "color_panel_light": "255 255 255",
        "color_gold_light": "165 128 47",
        "color_goldlight_light": "122 95 35",
        "color_cream_light": "26 24 20",
        "unete_eyebrow": "Bolsa de trabajo",
        "unete_titulo": "Únete a Nosotros",
        "unete_texto": (
            "Buscamos talento que comparta nuestra visión. Consulta las vacantes abiertas o, "
            "si no encuentras el puesto que buscas, comparte tu CV para que Capital Humano lo revise."
        ),
        "hero_eyebrow": "Negocios Inmobiliarios · Yucatán",
        "hero_titulo": "Invierte en tierra con certeza y visión de futuro",
        "hero_texto": (
            "Marnez Desarrollos crea comunidades residenciales y vacacionales en las mejores "
            "ubicaciones de Yucatán, con acompañamiento legal y escrituración inmediata en cada etapa."
        ),
        "desarrollos_eyebrow": "Proyectos disponibles",
        "desarrollos_titulo": "Terrenos residenciales y vacacionales",
        "entregados_eyebrow": "Proyectos entregados",
        "entregados_titulo": "Desarrollos que ya entregamos",
        "nosotros_eyebrow": "Marnez Desarrollos",
        "nosotros_titulo": "Negocios inmobiliarios con visión de largo plazo",
        "nosotros_texto": (
            "Somos una empresa yucateca enfocada en la creación, desarrollo y comercialización de "
            "negocios inmobiliarios. Generamos productos de gran valor para socios e inversionistas "
            "y ofrecemos una visión de futuro que asegura el patrimonio y crecimiento de nuestros clientes."
        ),
        "static_logo_oscuro": "img/brand/logo-marnez-white.png",
        "static_logo_claro": "img/brand/logo-marnez.png",
        "static_splash": "img/hero/hero-night.jpg",
        "static_nosotros": "img/desarrollos/antal/antal-06.jpg",
        "static_heroes": [
            "img/hero/hero-night.jpg",
            "img/hero/hero-concept-1.jpg",
            "img/hero/hero-concept-2.jpg",
            "img/desarrollos/antal/antal-06.jpg",
        ],
    }

    id = db.Column(db.Integer, primary_key=True)
    color_ink = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_ink"])
    color_panel = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_panel"])
    color_gold = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_gold"])
    color_goldlight = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_goldlight"])
    color_cream = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_cream"])
    color_ink_light = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_ink_light"])
    color_panel_light = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_panel_light"])
    color_gold_light = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_gold_light"])
    color_goldlight_light = db.Column(
        db.String(20), nullable=False, default=DEFAULTS["color_goldlight_light"]
    )
    color_cream_light = db.Column(db.String(20), nullable=False, default=DEFAULTS["color_cream_light"])

    logo_oscuro = db.Column(db.String(255), nullable=True)
    logo_claro = db.Column(db.String(255), nullable=True)
    splash_img = db.Column(db.String(255), nullable=True)
    hero_1 = db.Column(db.String(255), nullable=True)
    hero_2 = db.Column(db.String(255), nullable=True)
    hero_3 = db.Column(db.String(255), nullable=True)
    hero_4 = db.Column(db.String(255), nullable=True)
    unete_imagen = db.Column(db.String(255), nullable=True)
    nosotros_imagen = db.Column(db.String(255), nullable=True)

    unete_eyebrow = db.Column(db.String(80), nullable=True)
    unete_titulo = db.Column(db.String(120), nullable=True)
    unete_texto = db.Column(db.Text, nullable=True)

    hero_eyebrow = db.Column(db.String(120), nullable=True)
    hero_titulo = db.Column(db.String(220), nullable=True)
    hero_texto = db.Column(db.Text, nullable=True)

    desarrollos_eyebrow = db.Column(db.String(80), nullable=True)
    desarrollos_titulo = db.Column(db.String(160), nullable=True)
    entregados_eyebrow = db.Column(db.String(80), nullable=True)
    entregados_titulo = db.Column(db.String(160), nullable=True)

    nosotros_eyebrow = db.Column(db.String(80), nullable=True)
    nosotros_titulo = db.Column(db.String(160), nullable=True)
    nosotros_texto = db.Column(db.Text, nullable=True)

    home_secciones_json = db.Column(db.Text, nullable=True)

    actualizado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    @property
    def home_secciones(self) -> list[dict]:
        try:
            raw = json.loads(self.home_secciones_json or "[]")
        except (TypeError, ValueError):
            raw = []
        by_id = {s.get("id"): s for s in raw if isinstance(s, dict) and s.get("id")}
        merged = []
        for default in self.HOME_SECCIONES_DEFAULT:
            cur = dict(default)
            if default["id"] in by_id:
                ov = by_id[default["id"]]
                cur["visible"] = bool(ov.get("visible", True))
                try:
                    cur["orden"] = int(ov.get("orden", default["orden"]))
                except (TypeError, ValueError):
                    cur["orden"] = default["orden"]
            merged.append(cur)
        merged.sort(key=lambda s: s["orden"])
        return merged

    @home_secciones.setter
    def home_secciones(self, value: list[dict]) -> None:
        self.home_secciones_json = json.dumps(value or [], ensure_ascii=False)

    def seccion_visible(self, seccion_id: str) -> bool:
        for s in self.home_secciones:
            if s["id"] == seccion_id:
                return bool(s.get("visible", True))
        return True

    def color_hex(self, field: str) -> str:
        rgb = getattr(self, field, None) or self.DEFAULTS.get(field, "201 169 98")
        return _rgb_str_to_hex(rgb)

    def set_color_hex(self, field: str, hex_color: str) -> None:
        fallback = self.DEFAULTS.get(field, "201 169 98")
        setattr(self, field, _hex_to_rgb_str(hex_color, fallback))

    def asset_url(self, ref: str | None, static_fallback: str) -> str:
        from flask import url_for
        from .media import is_media_ref, media_filename

        if is_media_ref(ref):
            return url_for("main.serve_media", filename=media_filename(ref))
        return url_for("static", filename=static_fallback)

    def as_template_ctx(self) -> dict:
        from flask import url_for
        from .media import is_media_ref, media_filename

        d = self.DEFAULTS
        heroes = []
        for ref, fb in zip(
            [self.hero_1, self.hero_2, self.hero_3, self.hero_4],
            d["static_heroes"],
            strict=True,
        ):
            if is_media_ref(ref):
                heroes.append(url_for("main.serve_media", filename=media_filename(ref)))
            else:
                heroes.append(url_for("static", filename=fb))

        unete_img = None
        if is_media_ref(self.unete_imagen):
            unete_img = url_for("main.serve_media", filename=media_filename(self.unete_imagen))

        nosotros_img = self.asset_url(self.nosotros_imagen, d["static_nosotros"])

        return {
            "ink": self.color_ink or d["color_ink"],
            "panel": self.color_panel or d["color_panel"],
            "gold": self.color_gold or d["color_gold"],
            "goldlight": self.color_goldlight or d["color_goldlight"],
            "cream": self.color_cream or d["color_cream"],
            "ink_light": self.color_ink_light or d["color_ink_light"],
            "panel_light": self.color_panel_light or d["color_panel_light"],
            "gold_light_theme": self.color_gold_light or d["color_gold_light"],
            "goldlight_light": self.color_goldlight_light or d["color_goldlight_light"],
            "cream_light": self.color_cream_light or d["color_cream_light"],
            "logo_oscuro": self.asset_url(self.logo_oscuro, d["static_logo_oscuro"]),
            "logo_claro": self.asset_url(self.logo_claro, d["static_logo_claro"]),
            "splash": self.asset_url(self.splash_img, d["static_splash"]),
            "heroes": heroes,
            "unete_imagen": unete_img,
            "unete_eyebrow": self.unete_eyebrow or d["unete_eyebrow"],
            "unete_titulo": self.unete_titulo or d["unete_titulo"],
            "unete_texto": self.unete_texto or d["unete_texto"],
            "hero_eyebrow": self.hero_eyebrow or d["hero_eyebrow"],
            "hero_titulo": self.hero_titulo or d["hero_titulo"],
            "hero_texto": self.hero_texto or d["hero_texto"],
            "desarrollos_eyebrow": self.desarrollos_eyebrow or d["desarrollos_eyebrow"],
            "desarrollos_titulo": self.desarrollos_titulo or d["desarrollos_titulo"],
            "entregados_eyebrow": self.entregados_eyebrow or d["entregados_eyebrow"],
            "entregados_titulo": self.entregados_titulo or d["entregados_titulo"],
            "nosotros_eyebrow": self.nosotros_eyebrow or d["nosotros_eyebrow"],
            "nosotros_titulo": self.nosotros_titulo or d["nosotros_titulo"],
            "nosotros_texto": self.nosotros_texto or d["nosotros_texto"],
            "nosotros_imagen": nosotros_img,
            "home_secciones": self.home_secciones,
        }

    @classmethod
    def get_or_create(cls):
        row = cls.query.first()
        if row:
            return row
        row = cls()
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

    CAT_DISPONIBLE = "disponible"
    CAT_ENTREGADO = "entregado"
    CATEGORIAS = {
        CAT_DISPONIBLE: "Proyectos disponibles",
        CAT_ENTREGADO: "Proyectos entregados",
    }

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
    # disponible = en venta / preventa · entregado = proyecto concluido
    categoria = db.Column(db.String(40), nullable=False, default="disponible", index=True)
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
