"""Seed inicial y migraciones ligeras de esquema SQLite."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from .extensions import db
from .models import (
    AjustesHR,
    AjustesComercial,
    BlogPost,
    Desarrollo,
    DesarrolloImagen,
    Usuario,
    ROL_CAPITAL_HUMANO,
    ROL_COMERCIAL,
)

logger = logging.getLogger(__name__)

# Columnas nuevas sobre tablas ya existentes (SQLite no altera con create_all).
_ALTERS = {
    "usuarios": [
        ("rol", "VARCHAR(40) DEFAULT 'capital_humano'"),
        ("activo", "BOOLEAN DEFAULT 1"),
    ],
    "vacantes": [
        ("correo_1", "VARCHAR(160)"),
        ("correo_2", "VARCHAR(160)"),
        ("correo_3", "VARCHAR(160)"),
        ("enlace_occ", "VARCHAR(500)"),
        ("enlace_extra_nombre", "VARCHAR(80)"),
        ("enlace_extra_url", "VARCHAR(500)"),
    ],
}


def ensure_schema(app) -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        existing = set(inspector.get_table_names())
        for table, cols in _ALTERS.items():
            if table not in existing:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, typedef in cols:
                if name in present:
                    continue
                sql = f"ALTER TABLE {table} ADD COLUMN {name} {typedef}"
                db.session.execute(text(sql))
                logger.info("Schema: %s", sql)
        # Normaliza estados legacy de postulaciones
        if "postulaciones" in existing:
            present = {c["name"] for c in inspector.get_columns("postulaciones")}
            if "estado" in present:
                db.session.execute(
                    text(
                        "UPDATE postulaciones SET estado = 'nuevo' "
                        "WHERE estado IS NULL OR LOWER(estado) IN ('nuevo', 'new')"
                    )
                )
        db.session.commit()


def seed_admins(app) -> None:
    from .models import Usuario

    # Backfill rol/activo en usuarios viejos
    for u in Usuario.query.all():
        changed = False
        if not getattr(u, "rol", None):
            u.rol = ROL_CAPITAL_HUMANO
            changed = True
        if getattr(u, "activo", None) is None:
            u.activo = True
            changed = True
        if changed:
            db.session.add(u)
    db.session.commit()

    hr_email = app.config["ADMIN_EMAIL"]
    hr = Usuario.query.filter_by(email=hr_email).first()
    if not hr:
        hr = Usuario(
            nombre="Capital Humano",
            email=hr_email,
            rol=ROL_CAPITAL_HUMANO,
            activo=True,
        )
        hr.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(hr)
        db.session.commit()
        app.logger.info("Usuario Capital Humano creado: %s", hr_email)
    else:
        if hr.rol != ROL_CAPITAL_HUMANO:
            hr.rol = ROL_CAPITAL_HUMANO
            db.session.commit()

    com_email = app.config.get("COMERCIAL_EMAIL")
    if com_email:
        com = Usuario.query.filter_by(email=com_email).first()
        if not com:
            com = Usuario(
                nombre="Comercial",
                email=com_email,
                rol=ROL_COMERCIAL,
                activo=True,
            )
            com.set_password(app.config["COMERCIAL_PASSWORD"])
            db.session.add(com)
            db.session.commit()
            app.logger.info("Usuario Comercial creado: %s", com_email)
        elif com.rol != ROL_COMERCIAL:
            com.rol = ROL_COMERCIAL
            db.session.commit()

    AjustesHR.get_or_create()
    AjustesComercial.get_or_create(defaults=app.config.get("EMPRESA"))


def seed_content_if_empty(app) -> None:
    if BlogPost.query.count() == 0:
        from .data import BLOG_POSTS

        for p in BLOG_POSTS:
            db.session.add(
                BlogPost(
                    slug=p["slug"],
                    titulo=p["titulo"],
                    resumen=p["resumen"],
                    cuerpo=p["cuerpo"],
                    imagen=p.get("imagen"),
                    font_size="base",
                    publicado=True,
                )
            )
        db.session.commit()
        app.logger.info("Seed: %s posts de blog", len(BLOG_POSTS))

    if Desarrollo.query.count() == 0:
        from .data import DESARROLLOS

        for idx, d in enumerate(DESARROLLOS):
            row = Desarrollo(
                slug=d["slug"],
                nombre=d["nombre"],
                tagline=d.get("tagline"),
                ubicacion=d.get("ubicacion"),
                resumen=d.get("resumen"),
                descripcion=d.get("descripcion"),
                precio_desde=int(d.get("precio_desde") or 0),
                enganche_min_pct=int(d.get("enganche_min_pct") or 10),
                estatus=d.get("estatus"),
                portada=d.get("portada"),
                hero_extra=d.get("hero_extra"),
                video=d.get("video"),
                video_poster=d.get("video_poster"),
                tour_360=d.get("tour_360"),
                video_youtube=d.get("video_youtube"),
                mapa_query=d.get("mapa_query"),
                mapa_img=d.get("mapa_img"),
                orden=idx,
                activo=True,
            )
            row.amenidades = d.get("amenidades") or []
            row.plazos_meses = d.get("plazos_meses") or [12, 24, 36]
            db.session.add(row)
            db.session.flush()
            count = int(d.get("galeria_count") or 0)
            for i in range(1, count + 1):
                db.session.add(
                    DesarrolloImagen(
                        desarrollo_id=row.id,
                        filename=f"{d['slug']}-{i:02d}.jpg",
                        tipo="galeria",
                        orden=i,
                    )
                )
        db.session.commit()
        app.logger.info("Seed: %s desarrollos", len(DESARROLLOS))
