from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    current_app,
    abort,
)
from pathlib import Path

from ..extensions import db
from ..models import Lead, AjustesComercial
from ..data import TESTIMONIOS, CERTIFICACIONES, EQUIPO_FOTOS
from ..content import (
    list_desarrollos_activos,
    get_desarrollo,
    list_blog_posts,
    get_blog_post,
)
from ..media import desarrollo_img_url
from ..mail import enviar_notificacion_lead

main_bp = Blueprint("main", __name__, template_folder="../templates")


@main_bp.route("/")
def index():
    destacados = list_desarrollos_activos()[:3]
    return render_template(
        "index.html",
        destacados=destacados,
        testimonios=TESTIMONIOS,
        certificaciones=CERTIFICACIONES,
        posts=list_blog_posts(limit=3),
    )


@main_bp.route("/desarrollos")
def desarrollos():
    return render_template(
        "desarrollos/listado.html", desarrollos=list_desarrollos_activos()
    )


@main_bp.route("/desarrollos/<slug>")
def desarrollo_detalle(slug):
    desarrollo = get_desarrollo(slug)
    if not desarrollo:
        flash("Ese desarrollo no existe o ya no está disponible.", "warning")
        return redirect(url_for("main.desarrollos"))

    galeria = []
    for img in desarrollo.imagenes:
        if img.tipo != "galeria":
            continue
        galeria.append(desarrollo_img_url(desarrollo.slug, img.filename))

    if not galeria:
        # Compatibilidad seed: patrón slug-01.jpg en static
        count = desarrollo.galeria_count
        if not count:
            # si no hay registros, intentar contar no es posible; vacío
            pass

    otros = [d for d in list_desarrollos_activos() if d.slug != slug][:3]
    return render_template(
        "desarrollos/detalle.html", d=desarrollo, galeria=galeria, otros=otros
    )


@main_bp.route("/nosotros")
def nosotros():
    return render_template(
        "nosotros.html",
        certificaciones=CERTIFICACIONES,
        testimonios=TESTIMONIOS,
        equipo_fotos=EQUIPO_FOTOS[:8],
    )


@main_bp.route("/blog")
def blog():
    return render_template("blog/listado.html", posts=list_blog_posts())


@main_bp.route("/blog/<slug>")
def blog_post(slug):
    post = get_blog_post(slug)
    if not post:
        flash("Ese artículo no existe.", "warning")
        return redirect(url_for("main.blog"))
    relacionados = [p for p in list_blog_posts() if p.slug != slug][:2]
    return render_template("blog/detalle.html", post=post, relacionados=relacionados)


@main_bp.route("/contacto", methods=["GET", "POST"])
def contacto():
    desarrollos = list_desarrollos_activos()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        desarrollo_interes = request.form.get("desarrollo_interes", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        errores = []
        if not nombre:
            errores.append("Tu nombre es obligatorio.")
        if not email or "@" not in email:
            errores.append("Ingresa un correo válido.")
        if not telefono:
            errores.append("Tu teléfono es obligatorio.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "contacto.html", desarrollos=desarrollos, form=request.form
            ), 400

        lead = Lead(
            nombre=nombre,
            email=email,
            telefono=telefono,
            desarrollo_interes=desarrollo_interes or None,
            mensaje=mensaje or None,
        )
        db.session.add(lead)
        db.session.commit()

        destinos = AjustesComercial.get_or_create(
            defaults=current_app.config.get("EMPRESA")
        ).correos_destino()
        enviar_notificacion_lead(lead, destinos)

        flash("¡Gracias! Un asesor de Marnez te contactará muy pronto.", "success")
        return redirect(url_for("main.contacto"))

    desarrollo_sugerido = request.args.get("desarrollo", "")
    return render_template(
        "contacto.html",
        desarrollos=desarrollos,
        form={"desarrollo_interes": desarrollo_sugerido},
    )


@main_bp.route("/media/<path:filename>")
def serve_media(filename):
    """Sirve archivos subidos desde el CMS (fuera de static para control)."""
    # Evitar path traversal
    safe = Path(filename).name
    folder = Path(current_app.config["MEDIA_FOLDER"])
    if not (folder / safe).is_file():
        abort(404)
    return send_from_directory(folder, safe)
