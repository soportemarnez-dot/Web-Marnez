"""Pruebas Nivel B: secciones del inicio y categorías disponible/entregado."""

from __future__ import annotations

import pytest

from config import Config
from marnez import create_app
from marnez.extensions import db
from marnez.models import AjustesDiseno, Desarrollo
from marnez.content import invalidate_content_cache, list_desarrollos_disponibles, list_desarrollos_entregados


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RESEND_API_KEY = ""
    RESEND_FROM = ""


@pytest.fixture()
def app(tmp_path):
    TestConfig.UPLOAD_FOLDER = str(tmp_path / "cv")
    TestConfig.MEDIA_FOLDER = str(tmp_path / "media")
    application = create_app(TestConfig)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, app):
    client.post(
        "/panel-comercial/login",
        data={
            "email": app.config["COMERCIAL_EMAIL"],
            "password": app.config["COMERCIAL_PASSWORD"],
        },
        follow_redirects=True,
    )


def test_home_renders_disponibles_and_entregados_sections(client, app):
    with app.app_context():
        if Desarrollo.query.count() == 0:
            db.session.add(
                Desarrollo(
                    slug="costella-test",
                    nombre="Costella",
                    precio_desde=1,
                    categoria=Desarrollo.CAT_DISPONIBLE,
                    activo=True,
                )
            )
            db.session.add(
                Desarrollo(
                    slug="antal-test",
                    nombre="Antal",
                    precio_desde=1,
                    categoria=Desarrollo.CAT_ENTREGADO,
                    activo=True,
                    estatus="Entregado",
                )
            )
            db.session.commit()
            invalidate_content_cache()

    html = client.get("/").get_data(as_text=True)
    assert "Proyectos disponibles" in html or "Terrenos residenciales" in html
    assert "Proyectos entregados" in html or "Desarrollos que ya entregamos" in html


def test_mover_desarrollo_entre_categorias(client, app):
    _login(client, app)
    with app.app_context():
        d = Desarrollo.query.filter_by(slug="mover-test").first()
        if not d:
            d = Desarrollo(
                slug="mover-test",
                nombre="Mover Test",
                precio_desde=100,
                categoria=Desarrollo.CAT_DISPONIBLE,
                activo=True,
            )
            db.session.add(d)
            db.session.commit()
        did = d.id

    res = client.post(
        f"/panel-comercial/desarrollos/{did}/categoria",
        data={"categoria": "entregado"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "movido a Proyectos entregados" in res.get_data(as_text=True)

    with app.app_context():
        invalidate_content_cache()
        d = db.session.get(Desarrollo, did)
        assert d.categoria == "entregado"
        assert any(x.id == did for x in list_desarrollos_entregados())
        assert all(x.id != did for x in list_desarrollos_disponibles())

    res2 = client.post(
        f"/panel-comercial/desarrollos/{did}/categoria",
        data={"categoria": "disponible"},
        follow_redirects=True,
    )
    assert res2.status_code == 200
    with app.app_context():
        invalidate_content_cache()
        d = db.session.get(Desarrollo, did)
        assert d.categoria == "disponible"


def test_ocultar_seccion_home(client, app):
    _login(client, app)
    data = {
        "color_gold_hex": "#c9a962",
        "color_goldlight_hex": "#e4cf9c",
        "color_ink_hex": "#0f1115",
        "color_panel_hex": "#171a21",
        "color_cream_hex": "#f4efe6",
        "color_ink_light_hex": "#faf9f6",
        "color_panel_light_hex": "#ffffff",
        "color_gold_light_hex": "#a5802f",
        "color_goldlight_light_hex": "#7a5f23",
        "color_cream_light_hex": "#1a1814",
    }
    # Marcar todas visibles excepto blog
    for s in AjustesDiseno.HOME_SECCIONES_DEFAULT:
        data[f"sec_orden_{s['id']}"] = str(s["orden"])
        if s["id"] != "blog":
            data[f"sec_visible_{s['id']}"] = "on"

    res = client.post("/panel-comercial/diseno", data=data, follow_redirects=True)
    assert res.status_code == 200

    html = client.get("/").get_data(as_text=True)
    assert "Noticias relevantes" not in html


def test_listado_publico_separado(client, app):
    with app.app_context():
        if not Desarrollo.query.filter_by(slug="disp-pub").first():
            db.session.add(
                Desarrollo(
                    slug="disp-pub",
                    nombre="Disponible Pub",
                    precio_desde=10,
                    categoria="disponible",
                    activo=True,
                )
            )
            db.session.add(
                Desarrollo(
                    slug="ent-pub",
                    nombre="Entregado Pub",
                    precio_desde=10,
                    categoria="entregado",
                    activo=True,
                )
            )
            db.session.commit()
            invalidate_content_cache()

    html = client.get("/desarrollos").get_data(as_text=True)
    assert 'id="disponibles"' in html
    assert 'id="entregados"' in html
    assert "Disponible Pub" in html
    assert "Entregado Pub" in html
