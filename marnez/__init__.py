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
        from .models import AjustesComercial

        defaults = app.config["EMPRESA"]
        try:
            ajustes = AjustesComercial.get_or_create(defaults=defaults)
            empresa = ajustes.as_empresa_dict(defaults)
        except Exception:
            empresa = defaults
        return {"empresa": empresa, "now_year": datetime.now(UTC).year}

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
