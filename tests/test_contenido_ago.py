"""Cambios de contenido: desactivar desarrollo, cifras, tema, cotizador."""

from __future__ import annotations

import pytest

from config import Config
from marnez import create_app
from marnez.extensions import db
from marnez.models import Desarrollo
from marnez.content import invalidate_content_cache, list_desarrollos_disponibles


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


def test_home_muestra_cifras_empresa(client):
    html = client.get("/").get_data(as_text=True)
    assert "+333,500" in html
    assert "Colaboradores" in html
    assert "INSEJUPY" in html
    assert "Protección jurídica patrimonial" not in html


def test_tema_default_es_claro(client):
    html = client.get("/").get_data(as_text=True)
    assert "saved !== 'dark'" in html


def test_nosotros_sin_certeza_juridica(client):
    html = client.get("/nosotros").get_data(as_text=True)
    assert "100%</p><p class=\"text-cream/70 text-sm\">Certeza jurídica" not in html
    assert "INSEJUPY" in html
    assert "+333,500" in html
    assert "m² vendidos" in html


def test_desactivar_desarrollo_oculta_en_publico(client, app):
    _login(client, app)
    with app.app_context():
        d = Desarrollo(
            slug="oculto-test",
            nombre="Oculto Test",
            precio_desde=100,
            categoria="disponible",
            activo=True,
        )
        db.session.add(d)
        db.session.commit()
        did = d.id

    res = client.post(
        f"/panel-comercial/desarrollos/{did}/activo",
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "oculto" in res.get_data(as_text=True).lower()

    with app.app_context():
        invalidate_content_cache()
        d = db.session.get(Desarrollo, did)
        assert d.activo is False
        assert all(x.slug != "oculto-test" for x in list_desarrollos_disponibles())

    assert client.get("/desarrollos/oculto-test").status_code in (302, 404)


def test_cotizador_bloqueado_en_entregado(client, app):
    with app.app_context():
        d = Desarrollo.query.filter_by(slug="entregado-calc").first()
        if not d:
            d = Desarrollo(
                slug="entregado-calc",
                nombre="Entregado Calc",
                precio_desde=500000,
                categoria="entregado",
                activo=True,
                estatus="Entregado",
            )
            db.session.add(d)
            db.session.commit()
        invalidate_content_cache()

    html = client.get("/desarrollos/entregado-calc").get_data(as_text=True)
    assert "data-cotizador" not in html
    assert "Ya entregamos este desarrollo" in html
    assert "Ver proyectos disponibles" in html
