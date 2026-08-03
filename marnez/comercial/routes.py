from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, current_user
from werkzeug.datastructures import MultiDict

from ..extensions import db
from ..models import (
    Usuario,
    BlogPost,
    Desarrollo,
    DesarrolloImagen,
    AjustesComercial,
    AjustesDiseno,
    ROL_COMERCIAL,
)
from ..auth import require_rol, gestionar_cuenta
from ..content import invalidate_content_cache
from ..media import (
    slugify,
    guardar_media,
    borrar_media_si_aplica,
    allowed_image,
    allowed_video,
)

comercial_bp = Blueprint("comercial", __name__, template_folder="../templates/comercial")


@comercial_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.es_comercial and current_user.activo:
            return redirect(url_for("comercial.panel"))
        logout_user()
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(email=email, rol=ROL_COMERCIAL).first()
        if usuario and usuario.activo and usuario.check_password(password):
            login_user(usuario)
            flash(f"Bienvenido, {usuario.nombre}.", "success")
            return redirect(url_for("comercial.panel"))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("comercial/login.html")


@comercial_bp.route("/logout")
@require_rol(ROL_COMERCIAL)
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("comercial.login"))


@comercial_bp.route("/")
@require_rol(ROL_COMERCIAL)
def panel():
    return render_template(
        "comercial/panel.html",
        total_blogs=BlogPost.query.count(),
        total_desarrollos=Desarrollo.query.count(),
        blogs_pub=BlogPost.query.filter_by(publicado=True).count(),
        des_activos=Desarrollo.query.filter_by(activo=True).count(),
    )


@comercial_bp.route("/diseno", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def diseno_ajustes():
    """Colores de marca, logos, heroes y sección Únete (Nivel A low-code)."""
    row = AjustesDiseno.get_or_create()
    if request.method == "POST":
        color_fields = [
            "color_ink",
            "color_panel",
            "color_gold",
            "color_goldlight",
            "color_cream",
            "color_ink_light",
            "color_panel_light",
            "color_gold_light",
            "color_goldlight_light",
            "color_cream_light",
        ]
        for field in color_fields:
            hex_val = request.form.get(f"{field}_hex", "").strip()
            if hex_val:
                row.set_color_hex(field, hex_val)

        row.unete_eyebrow = (request.form.get("unete_eyebrow") or "").strip() or None
        row.unete_titulo = (request.form.get("unete_titulo") or "").strip() or None
        row.unete_texto = (request.form.get("unete_texto") or "").strip() or None

        img_fields = [
            "logo_oscuro",
            "logo_claro",
            "splash_img",
            "hero_1",
            "hero_2",
            "hero_3",
            "hero_4",
            "unete_imagen",
        ]
        for field in img_fields:
            if request.form.get(f"quitar_{field}") == "1":
                borrar_media_si_aplica(getattr(row, field))
                setattr(row, field, None)
                continue
            f = request.files.get(field)
            if f and f.filename:
                if not allowed_image(f.filename):
                    flash(f"Imagen inválida en {field} (usa JPG, PNG o WEBP).", "danger")
                    continue
                try:
                    borrar_media_si_aplica(getattr(row, field))
                    setattr(row, field, guardar_media(f))
                except ValueError as exc:
                    flash(str(exc), "danger")

        db.session.commit()
        flash("Diseño del sitio actualizado. Revisa la página pública.", "success")
        return redirect(url_for("comercial.diseno_ajustes"))

    return render_template("comercial/diseno.html", d=row, ctx=row.as_template_ctx())


@comercial_bp.route("/cuenta", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def cuenta():
    return gestionar_cuenta(ROL_COMERCIAL, "comercial/cuenta.html", "comercial.cuenta")


@comercial_bp.route("/contacto", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def contacto_ajustes():
    """Teléfono, correo, oficinas, WhatsApp y correos de cotización."""
    ajustes = AjustesComercial.get_or_create(defaults=current_app.config.get("EMPRESA"))
    if request.method == "POST":
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        direccion = request.form.get("direccion", "").strip()
        mapa_query = request.form.get("mapa_query", "").strip()
        whatsapp_raw = request.form.get("whatsapp", "").strip()
        digits = "".join(ch for ch in whatsapp_raw if ch.isdigit())

        c1 = request.form.get("correo_1", "").strip()
        c2 = request.form.get("correo_2", "").strip()
        c3 = request.form.get("correo_3", "").strip()
        errores = []
        if not telefono:
            errores.append("El teléfono público es obligatorio.")
        if not email or "@" not in email:
            errores.append("El correo público debe ser válido.")
        if not digits or len(digits) < 10:
            errores.append("Indica un número de WhatsApp válido (con lada país, ej. 529902293374).")
        llenos = [c for c in (c1, c2, c3) if c]
        if not llenos:
            errores.append("Indica al menos un correo para recibir cotizaciones / contacto.")
        for c in llenos:
            if "@" not in c:
                errores.append(f"Correo inválido: {c}")
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("comercial/contacto.html", a=ajustes, form=request.form), 400

        ajustes.telefono = telefono
        ajustes.email = email
        ajustes.direccion = direccion or None
        ajustes.mapa_query = mapa_query or None
        ajustes.whatsapp = digits
        ajustes.facebook = request.form.get("facebook", "").strip() or None
        ajustes.instagram = request.form.get("instagram", "").strip() or None
        ajustes.linkedin = request.form.get("linkedin", "").strip() or None
        ajustes.tiktok = request.form.get("tiktok", "").strip() or None
        ajustes.correo_1 = c1 or None
        ajustes.correo_2 = c2 or None
        ajustes.correo_3 = c3 or None
        db.session.commit()
        flash("Datos de contacto y correos de cotización actualizados.", "success")
        return redirect(url_for("comercial.contacto_ajustes"))

    return render_template("comercial/contacto.html", a=ajustes, form=MultiDict())


# ------------------------------------------------------------------ blogs --

@comercial_bp.route("/blogs")
@require_rol(ROL_COMERCIAL)
def blogs():
    posts = BlogPost.query.order_by(BlogPost.creado_en.desc()).all()
    return render_template("comercial/blogs.html", posts=posts)


@comercial_bp.route("/blogs/nuevo", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def blog_nuevo():
    if request.method == "POST":
        post = BlogPost()
        err = _blog_desde_form(post, request.form, request.files)
        if err:
            for e in err:
                flash(e, "danger")
            return render_template("comercial/blog_form.html", post=None, form=request.form), 400
        db.session.add(post)
        db.session.commit()
        invalidate_content_cache()
        flash("Artículo publicado.", "success")
        return redirect(url_for("comercial.blogs"))
    return render_template("comercial/blog_form.html", post=None, form={})


@comercial_bp.route("/blogs/<int:post_id>/editar", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def blog_editar(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == "POST":
        err = _blog_desde_form(post, request.form, request.files)
        if err:
            for e in err:
                flash(e, "danger")
            return render_template("comercial/blog_form.html", post=post, form=request.form), 400
        db.session.commit()
        invalidate_content_cache()
        flash("Artículo actualizado.", "success")
        return redirect(url_for("comercial.blogs"))
    return render_template("comercial/blog_form.html", post=post, form={})


@comercial_bp.route("/blogs/<int:post_id>/eliminar", methods=["POST"])
@require_rol(ROL_COMERCIAL)
def blog_eliminar(post_id):
    post = BlogPost.query.get_or_404(post_id)
    borrar_media_si_aplica(post.imagen)
    db.session.delete(post)
    db.session.commit()
    invalidate_content_cache()
    flash("Artículo eliminado.", "info")
    return redirect(url_for("comercial.blogs"))


@comercial_bp.route("/blogs/preview", methods=["POST"])
@require_rol(ROL_COMERCIAL)
def blog_preview():
    """Previsualización HTML del artículo (sin guardar)."""
    data = {
        "titulo": request.form.get("titulo", "Sin título"),
        "resumen": request.form.get("resumen", ""),
        "cuerpo": request.form.get("cuerpo", ""),
        "font_size": request.form.get("font_size", "base"),
        "imagen_url": request.form.get("imagen_preview_url") or "",
    }
    return render_template("comercial/blog_preview.html", p=data)


# ------------------------------------------------------------ desarrollos --

@comercial_bp.route("/desarrollos")
@require_rol(ROL_COMERCIAL)
def desarrollos():
    items = Desarrollo.query.order_by(Desarrollo.orden.asc(), Desarrollo.nombre.asc()).all()
    return render_template("comercial/desarrollos.html", desarrollos=items)


@comercial_bp.route("/desarrollos/nuevo", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def desarrollo_nuevo():
    if request.method == "POST":
        d = Desarrollo()
        err = _desarrollo_desde_form(d, request.form, request.files, is_new=True)
        if err:
            for e in err:
                flash(e, "danger")
            return render_template(
                "comercial/desarrollo_form.html", d=None, form=request.form
            ), 400
        db.session.add(d)
        db.session.commit()
        invalidate_content_cache()
        flash("Desarrollo creado.", "success")
        return redirect(url_for("comercial.desarrollo_editar", desarrollo_id=d.id))
    return render_template("comercial/desarrollo_form.html", d=None, form=MultiDict())


@comercial_bp.route("/desarrollos/<int:desarrollo_id>/editar", methods=["GET", "POST"])
@require_rol(ROL_COMERCIAL)
def desarrollo_editar(desarrollo_id):
    d = Desarrollo.query.get_or_404(desarrollo_id)
    if request.method == "POST":
        err = _desarrollo_desde_form(d, request.form, request.files, is_new=False)
        if err:
            for e in err:
                flash(e, "danger")
            return render_template("comercial/desarrollo_form.html", d=d, form=request.form), 400
        db.session.commit()
        invalidate_content_cache()
        flash("Desarrollo actualizado.", "success")
        return redirect(url_for("comercial.desarrollo_editar", desarrollo_id=d.id))
    return render_template("comercial/desarrollo_form.html", d=d, form=MultiDict())


@comercial_bp.route("/desarrollos/<int:desarrollo_id>/eliminar", methods=["POST"])
@require_rol(ROL_COMERCIAL)
def desarrollo_eliminar(desarrollo_id):
    d = Desarrollo.query.get_or_404(desarrollo_id)
    for field in (d.portada, d.hero_extra, d.video_poster, d.mapa_img, d.video):
        borrar_media_si_aplica(field)
    for img in list(d.imagenes):
        borrar_media_si_aplica(img.filename)
    db.session.delete(d)
    db.session.commit()
    invalidate_content_cache()
    flash("Desarrollo eliminado.", "info")
    return redirect(url_for("comercial.desarrollos"))


@comercial_bp.route("/desarrollos/<int:desarrollo_id>/galeria", methods=["POST"])
@require_rol(ROL_COMERCIAL)
def desarrollo_galeria_subir(desarrollo_id):
    d = Desarrollo.query.get_or_404(desarrollo_id)
    files = request.files.getlist("galeria")
    added = 0
    for f in files:
        if not f or not f.filename:
            continue
        if not allowed_image(f.filename):
            flash(f"Archivo no permitido: {f.filename}", "danger")
            continue
        try:
            ref = guardar_media(f)
        except ValueError as e:
            flash(str(e), "danger")
            continue
        orden = (d.galeria_count or 0) + 1
        db.session.add(
            DesarrolloImagen(desarrollo_id=d.id, filename=ref, tipo="galeria", orden=orden)
        )
        added += 1
    db.session.commit()
    invalidate_content_cache()
    flash(f"{added} imagen(es) agregada(s) a la galería.", "success" if added else "warning")
    return redirect(url_for("comercial.desarrollo_editar", desarrollo_id=d.id))


@comercial_bp.route(
    "/desarrollos/<int:desarrollo_id>/galeria/<int:imagen_id>/eliminar", methods=["POST"]
)
@require_rol(ROL_COMERCIAL)
def desarrollo_galeria_eliminar(desarrollo_id, imagen_id):
    d = Desarrollo.query.get_or_404(desarrollo_id)
    img = DesarrolloImagen.query.filter_by(id=imagen_id, desarrollo_id=d.id).first_or_404()
    borrar_media_si_aplica(img.filename)
    db.session.delete(img)
    db.session.commit()
    invalidate_content_cache()
    flash("Imagen eliminada de la galería.", "info")
    return redirect(url_for("comercial.desarrollo_editar", desarrollo_id=d.id))


def _blog_desde_form(post: BlogPost, form, files) -> list[str]:
    errores = []
    titulo = form.get("titulo", "").strip()
    resumen = form.get("resumen", "").strip()
    cuerpo = form.get("cuerpo", "").strip()
    slug = form.get("slug", "").strip() or slugify(titulo)
    font_size = form.get("font_size", "base").strip()
    if font_size not in ("sm", "base", "lg", "xl"):
        font_size = "base"
    if not titulo:
        errores.append("El título es obligatorio.")
    if not resumen:
        errores.append("El resumen es obligatorio.")
    if not cuerpo:
        errores.append("El cuerpo es obligatorio.")
    if not slug:
        errores.append("El slug es obligatorio.")
    else:
        existente = BlogPost.query.filter_by(slug=slug).first()
        if existente and existente.id != getattr(post, "id", None):
            errores.append("Ese slug ya existe.")
    if errores:
        return errores

    post.titulo = titulo
    post.resumen = resumen
    post.cuerpo = cuerpo
    post.slug = slug
    post.font_size = font_size
    post.publicado = form.get("publicado") == "on"

    img = files.get("imagen")
    if img and img.filename:
        if not allowed_image(img.filename):
            return ["La imagen debe ser JPG, PNG, WEBP o GIF."]
        try:
            nueva = guardar_media(img)
        except ValueError as e:
            return [str(e)]
        borrar_media_si_aplica(post.imagen)
        post.imagen = nueva
    return []


def _desarrollo_desde_form(d: Desarrollo, form, files, *, is_new: bool) -> list[str]:
    errores = []
    nombre = form.get("nombre", "").strip()
    slug = form.get("slug", "").strip() or slugify(nombre)
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not slug:
        errores.append("El slug es obligatorio.")
    else:
        existente = Desarrollo.query.filter_by(slug=slug).first()
        if existente and existente.id != getattr(d, "id", None):
            errores.append("Ese slug ya existe.")
    try:
        precio = int(form.get("precio_desde") or 0)
        enganche = int(form.get("enganche_min_pct") or 10)
    except ValueError:
        errores.append("Precio y enganche deben ser números.")
        precio, enganche = 0, 10

    meses_list = form.getlist("plazo_meses")
    interes_list = form.getlist("plazo_interes")
    plazos = []
    if meses_list:
        for m_raw, i_raw in zip(meses_list, interes_list + [""] * len(meses_list)):
            m_raw = (m_raw or "").strip()
            if not m_raw:
                continue
            try:
                meses = int(m_raw)
                interes = float((i_raw or "0").strip() or 0)
            except ValueError:
                errores.append(f"Plazo inválido: {m_raw} / interés {i_raw}")
                continue
            if meses <= 0:
                errores.append("Los plazos deben ser mayores a 0.")
                continue
            if interes < 0:
                errores.append("El interés no puede ser negativo.")
                continue
            plazos.append({"meses": meses, "interes_anual_pct": interes})
    else:
        # Compat formulario antiguo: "12, 24, 36"
        plazos_raw = form.get("plazos_meses", "")
        if plazos_raw:
            try:
                plazos = [
                    {"meses": int(x.strip()), "interes_anual_pct": 0}
                    for x in plazos_raw.split(",")
                    if x.strip()
                ]
            except ValueError:
                errores.append("Plazos inválidos.")

    if not plazos:
        errores.append("Agrega al menos un plazo de financiamiento.")

    amenidades = [
        line.strip()
        for line in (form.get("amenidades") or "").splitlines()
        if line.strip()
    ]

    if errores:
        return errores

    d.nombre = nombre
    d.slug = slug
    d.tagline = form.get("tagline", "").strip() or None
    d.ubicacion = form.get("ubicacion", "").strip() or None
    d.resumen = form.get("resumen", "").strip() or None
    d.descripcion = form.get("descripcion", "").strip() or None
    d.estatus = form.get("estatus", "").strip() or None
    d.precio_desde = precio
    d.enganche_min_pct = enganche
    d.plazos = plazos
    d.amenidades = amenidades
    d.tour_360 = form.get("tour_360", "").strip() or None
    d.video_youtube = form.get("video_youtube", "").strip() or None
    d.mapa_query = form.get("mapa_query", "").strip() or None
    d.orden = int(form.get("orden") or 0)
    d.activo = form.get("activo") == "on"

    # Campos de archivo
    for field, as_video in (
        ("portada", False),
        ("hero_extra", False),
        ("mapa_img", False),
        ("video_poster", False),
        ("video", True),
    ):
        f = files.get(field)
        if f and f.filename:
            if as_video and not allowed_video(f.filename):
                return ["El video debe ser MP4 o WEBM."]
            if not as_video and not allowed_image(f.filename):
                return [f"Archivo inválido en {field}."]
            try:
                ref = guardar_media(f, as_video=as_video)
            except ValueError as e:
                return [str(e)]
            borrar_media_si_aplica(getattr(d, field))
            setattr(d, field, ref)

    # Video legacy por nombre (archivo ya en static/video)
    video_nombre = form.get("video_nombre", "").strip()
    if video_nombre and not (files.get("video") and files.get("video").filename):
        d.video = video_nombre

    return []
