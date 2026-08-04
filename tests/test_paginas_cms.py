"""CMS low-code para páginas Nosotros y Únete."""

from __future__ import annotations

import pytest

from config import Config
from marnez import create_app
from marnez.extensions import db
from marnez.models import AjustesDiseno


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


def test_nosotros_usa_textos_cms(client, app):
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
        "nosotros_page_titulo": "Titulo Nosotros CMS",
        "nosotros_historia": "Historia editada desde el panel.",
        "nosotros_mision": "Mision CMS",
        "cifra_valor_0": "99",
        "cifra_texto_0": "Prueba",
        "cifra_valor_1": "1",
        "cifra_texto_1": "Uno",
        "cifra_valor_2": "2",
        "cifra_texto_2": "Dos",
        "cifra_valor_3": "3",
        "cifra_texto_3": "Tres",
    }
    for s in AjustesDiseno.NOSOTROS_SECCIONES_DEFAULT:
        data[f"nos_orden_{s['id']}"] = str(s["orden"])
        if s["id"] != "testimonios":
            data[f"nos_visible_{s['id']}"] = "on"

    res = client.post("/panel-comercial/diseno", data=data, follow_redirects=True)
    assert res.status_code == 200

    html = client.get("/nosotros").get_data(as_text=True)
    assert "Titulo Nosotros CMS" in html
    assert "Historia editada desde el panel." in html
    assert "Mision CMS" in html
    assert "Lo que dicen de nosotros" not in html  # sección oculta
    assert ">99<" in html or "99</p>" in html


def test_unete_page_usa_cms(client, app):
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
        "unete_eyebrow": "Carrera Marnez",
        "unete_titulo": "Trabaja con nosotros CMS",
        "unete_page_subtitulo": "Subtitulo unete CMS",
        "unete_vacantes_titulo": "Puestos abiertos CMS",
        "unete_cv_titulo": "Manda tu CV CMS",
    }
    for s in AjustesDiseno.UNETE_PAGE_SECCIONES_DEFAULT:
        data[f"une_orden_{s['id']}"] = str(s["orden"])
        data[f"une_visible_{s['id']}"] = "on"

    res = client.post("/panel-comercial/diseno", data=data, follow_redirects=True)
    assert res.status_code == 200

    html = client.get("/unete-a-nosotros/").get_data(as_text=True)
    assert "Carrera Marnez" in html
    assert "Trabaja con nosotros CMS" in html
    assert "Subtitulo unete CMS" in html
    assert "Puestos abiertos CMS" in html
    assert "Manda tu CV CMS" in html
