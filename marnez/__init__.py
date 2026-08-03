from datetime import datetime, UTC
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from config import Config
from .extensions import db, login_manager

csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["MEDIA_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from .auth import unauthorized_handler

    login_manager.unauthorized_handler(unauthorized_handler)

    from .main.routes import main_bp
    from .carreras.routes import carreras_bp
    from .comercial.routes import comercial_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(carreras_bp, url_prefix="/unete-a-nosotros")
    app.register_blueprint(comercial_bp, url_prefix="/panel-comercial")

    @app.context_processor
    def inject_globals():
        from .models import AjustesComercial, AjustesDiseno

        defaults = app.config["EMPRESA"]
        try:
            ajustes = AjustesComercial.get_or_create(defaults=defaults)
            empresa = ajustes.as_empresa_dict(defaults)
        except Exception:
            empresa = defaults
        try:
            diseno = AjustesDiseno.get_or_create().as_template_ctx()
        except Exception:
            from flask import url_for

            d = AjustesDiseno.DEFAULTS
            diseno = {
                "ink": d["color_ink"],
                "panel": d["color_panel"],
                "gold": d["color_gold"],
                "goldlight": d["color_goldlight"],
                "cream": d["color_cream"],
                "ink_light": d["color_ink_light"],
                "panel_light": d["color_panel_light"],
                "gold_light_theme": d["color_gold_light"],
                "goldlight_light": d["color_goldlight_light"],
                "cream_light": d["color_cream_light"],
                "logo_oscuro": url_for("static", filename=d["static_logo_oscuro"]),
                "logo_claro": url_for("static", filename=d["static_logo_claro"]),
                "splash": url_for("static", filename=d["static_splash"]),
                "heroes": [url_for("static", filename=h) for h in d["static_heroes"]],
                "unete_imagen": None,
                "unete_eyebrow": d["unete_eyebrow"],
                "unete_titulo": d["unete_titulo"],
                "unete_texto": d["unete_texto"],
                "hero_eyebrow": d["hero_eyebrow"],
                "hero_titulo": d["hero_titulo"],
                "hero_texto": d["hero_texto"],
                "desarrollos_eyebrow": d["desarrollos_eyebrow"],
                "desarrollos_titulo": d["desarrollos_titulo"],
                "entregados_eyebrow": d["entregados_eyebrow"],
                "entregados_titulo": d["entregados_titulo"],
                "nosotros_eyebrow": d["nosotros_eyebrow"],
                "nosotros_titulo": d["nosotros_titulo"],
                "nosotros_texto": d["nosotros_texto"],
                "nosotros_imagen": url_for("static", filename=d["static_nosotros"]),
                "home_secciones": list(AjustesDiseno.HOME_SECCIONES_DEFAULT),
            }
        return {"empresa": empresa, "diseno": diseno, "now_year": datetime.now(UTC).year}

    from .data import amenity_icon_key
    from .media import blog_img_url, desarrollo_img_url, video_url

    def _desarrollo_img_filter(filename, slug):
        return desarrollo_img_url(slug, filename)

    app.jinja_env.filters["amenity_icon"] = amenity_icon_key
    app.jinja_env.filters["blog_img"] = blog_img_url
    app.jinja_env.filters["desarrollo_img"] = _desarrollo_img_filter
    app.jinja_env.filters["video_url"] = video_url

    with app.app_context():
        from .seed import ensure_schema, seed_admins, seed_content_if_empty

        db.create_all()
        ensure_schema(app)
        seed_admins(app)
        seed_content_if_empty(app)

    return app
