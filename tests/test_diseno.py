"""Pruebas del CMS de diseño (Nivel A): colores, imágenes y sección Únete."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from config import Config
from marnez import create_app
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


def _png_file(color=(201, 169, 98)):
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_diseno_seed_and_home_injects_css(client, app):
    with app.app_context():
        row = AjustesDiseno.get_or_create()
        assert row is not None
        assert "201" in row.color_gold

    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'id="marnez-diseno"' in html
    assert "--c-gold:" in html
    assert "Únete a Nosotros" in html
    assert "Bolsa de trabajo" in html


def test_diseno_color_update_appears_on_home(client, app):
    email = app.config["COMERCIAL_EMAIL"]
    password = app.config["COMERCIAL_PASSWORD"]
    client.post(
        "/panel-comercial/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    res = client.post(
        "/panel-comercial/diseno",
        data={
            "color_gold_hex": "#112233",
            "color_goldlight_hex": "#445566",
            "color_ink_hex": "#0a0a0a",
            "color_panel_hex": "#111111",
            "color_cream_hex": "#eeeeee",
            "color_ink_light_hex": "#fafafa",
            "color_panel_light_hex": "#ffffff",
            "color_gold_light_hex": "#aa8830",
            "color_goldlight_light_hex": "#886622",
            "color_cream_light_hex": "#1a1a1a",
            "unete_eyebrow": "Equipo Marnez",
            "unete_titulo": "Trabaja con nosotros",
            "unete_texto": "Texto de prueba del CMS.",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        row = AjustesDiseno.query.first()
        assert row.color_gold == "17 34 51"
        assert row.unete_titulo == "Trabaja con nosotros"

    home = client.get("/")
    html = home.get_data(as_text=True)
    assert "17 34 51" in html
    assert "Trabaja con nosotros" in html
    assert "Equipo Marnez" in html
    assert "Texto de prueba del CMS." in html


def test_unete_image_upload_shows_on_home(client, app):
    email = app.config["COMERCIAL_EMAIL"]
    password = app.config["COMERCIAL_PASSWORD"]
    client.post(
        "/panel-comercial/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
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
        "unete_eyebrow": "Bolsa de trabajo",
        "unete_titulo": "Únete a Nosotros",
        "unete_texto": "Buscamos talento.",
        "unete_imagen": (_png_file(), "unete.png"),
    }
    res = client.post(
        "/panel-comercial/diseno",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        row = AjustesDiseno.query.first()
        assert row.unete_imagen and row.unete_imagen.startswith("media:")

    home = client.get("/").get_data(as_text=True)
    assert "/media/" in home
    assert 'alt="Únete a Nosotros"' in home


def test_hex_helpers():
    from marnez.models import _hex_to_rgb_str, _rgb_str_to_hex

    assert _hex_to_rgb_str("#c9a962", "0 0 0") == "201 169 98"
    assert _rgb_str_to_hex("201 169 98") == "#c9a962"


def test_diseno_panel_requires_login(client):
    res = client.get("/panel-comercial/diseno", follow_redirects=False)
    assert res.status_code in (302, 401)
