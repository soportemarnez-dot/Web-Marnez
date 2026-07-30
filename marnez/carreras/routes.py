from pathlib import Path

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    send_from_directory, send_file, current_app,
)
from flask_login import login_user, logout_user, current_user
from sqlalchemy import or_

from ..extensions import db
from ..models import Usuario, Vacante, Postulacion, AjustesHR, ROL_CAPITAL_HUMANO
from ..auth import require_rol, gestionar_cuenta
from ..mail import enviar_notificacion_postulacion
from .utils import allowed_cv, guardar_cv

carreras_bp = Blueprint("carreras", __name__, template_folder="../templates/carreras")


# ---------------------------------------------------------------- público --

@carreras_bp.route("/")
def index():
    vacantes = Vacante.query.filter_by(activa=True).order_by(Vacante.creado_en.desc()).all()
    return render_template("carreras/index.html", vacantes=vacantes)


@carreras_bp.route("/<int:vacante_id>")
def detalle(vacante_id):
    vacante = Vacante.query.get(vacante_id)
    if vacante is None:
        flash(
            "Esta vacante ya no está disponible. Puedes enviarnos tu CV de forma espontánea.",
            "warning",
        )
        return redirect(url_for("carreras.postular_espontanea"))

    # Pausada: el público va a CV espontáneo. Solo CH con ?preview=1 (panel) puede verla.
    if not vacante.activa:
        es_preview_hr = (
            request.args.get("preview") == "1"
            and current_user.is_authenticated
            and getattr(current_user, "es_capital_humano", False)
        )
        if not es_preview_hr:
            flash(
                "Esta vacante ya no está disponible. Puedes enviarnos tu CV de forma espontánea.",
                "warning",
            )
            return redirect(url_for("carreras.postular_espontanea"))

    return render_template("carreras/detalle.html", vacante=vacante)


@carreras_bp.route("/<int:vacante_id>/postular", methods=["GET", "POST"])
def postular(vacante_id):
    vacante = Vacante.query.get(vacante_id)
    if vacante is None or not vacante.activa:
        flash("Esta vacante ya no está disponible, pero puedes enviarnos tu CV.", "warning")
        return redirect(url_for("carreras.postular_espontanea"))
    return _procesar_postulacion(vacante=vacante)


@carreras_bp.route("/postular-espontanea", methods=["GET", "POST"])
def postular_espontanea():
    return _procesar_postulacion(vacante=None)


def _procesar_postulacion(vacante):
    template = "carreras/postular.html"
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        puesto_deseado = request.form.get("puesto_deseado", "").strip()
        mensaje = request.form.get("mensaje", "").strip()
        cv = request.files.get("cv")

        errores = []
        if not nombre:
            errores.append("Tu nombre es obligatorio.")
        if not email or "@" not in email:
            errores.append("Ingresa un correo válido.")
        if not telefono:
            errores.append("Tu teléfono es obligatorio.")
        if not cv or cv.filename == "":
            errores.append("Adjunta tu CV en PDF o Word.")
        elif not allowed_cv(cv.filename):
            errores.append("El CV debe ser PDF, DOC o DOCX.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(template, vacante=vacante, form=request.form), 400

        nombre_guardado, nombre_original = guardar_cv(cv)
        postulacion = Postulacion(
            vacante_id=vacante.id if vacante else None,
            nombre=nombre,
            email=email,
            telefono=telefono,
            puesto_deseado=puesto_deseado or (vacante.titulo if vacante else None),
            mensaje=mensaje or None,
            cv_filename=nombre_guardado,
            cv_nombre_original=nombre_original,
        )
        db.session.add(postulacion)
        db.session.commit()

        # Regla: siempre notifican los correos globales de Ajustes HR.
        # Si hay vacante, también los correos extra de esa vacante (sin duplicados).
        destinos = list(AjustesHR.get_or_create().correos_destino())
        if vacante:
            for c in vacante.correos_destino():
                if c not in destinos:
                    destinos.append(c)
        enviar_notificacion_postulacion(postulacion, destinos, vacante=vacante)

        flash("¡Postulación enviada! Capital Humano revisará tu perfil pronto.", "success")
        return redirect(url_for("carreras.index"))

    return render_template(template, vacante=vacante, form={})


# ------------------------------------------------------------- HR / login --

@carreras_bp.route("/panel/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.es_capital_humano and current_user.activo:
            return redirect(url_for("carreras.panel"))
        logout_user()
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(email=email, rol=ROL_CAPITAL_HUMANO).first()
        if usuario and usuario.activo and usuario.check_password(password):
            login_user(usuario)
            flash(f"Bienvenido, {usuario.nombre}.", "success")
            return redirect(url_for("carreras.panel"))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("carreras/login.html")


@carreras_bp.route("/panel/logout")
@require_rol(ROL_CAPITAL_HUMANO)
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("carreras.login"))


@carreras_bp.route("/panel")
@require_rol(ROL_CAPITAL_HUMANO)
def panel():
    estado = request.args.get("estado", "todas")
    q = Vacante.query.order_by(Vacante.creado_en.desc())
    if estado == "activas":
        q = q.filter_by(activa=True)
    elif estado == "pausadas":
        q = q.filter_by(activa=False)
    vacantes = q.all()
    total_postulaciones = Postulacion.query.count()
    conteos = {
        "todas": Vacante.query.count(),
        "activas": Vacante.query.filter_by(activa=True).count(),
        "pausadas": Vacante.query.filter_by(activa=False).count(),
    }
    return render_template(
        "carreras/panel.html",
        vacantes=vacantes,
        total_postulaciones=total_postulaciones,
        estado=estado,
        conteos=conteos,
    )


@carreras_bp.route("/panel/vacantes/nueva", methods=["GET", "POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_nueva():
    if request.method == "POST":
        errores = _validar_correos_form(request.form, obligatorio=False)
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("carreras/vacante_form.html", vacante=None, form=request.form), 400
        vacante = _vacante_desde_form(Vacante(), request.form)
        vacante.creado_por_id = current_user.id
        db.session.add(vacante)
        db.session.commit()
        flash("Vacante publicada.", "success")
        return redirect(url_for("carreras.panel"))
    return render_template("carreras/vacante_form.html", vacante=None, form={})


@carreras_bp.route("/panel/vacantes/<int:vacante_id>/editar", methods=["GET", "POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_editar(vacante_id):
    vacante = Vacante.query.get_or_404(vacante_id)
    if request.method == "POST":
        errores = _validar_correos_form(request.form, obligatorio=False)
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "carreras/vacante_form.html", vacante=vacante, form=request.form
            ), 400
        _vacante_desde_form(vacante, request.form)
        db.session.commit()
        flash("Vacante actualizada.", "success")
        return redirect(url_for("carreras.panel"))
    return render_template("carreras/vacante_form.html", vacante=vacante, form={})


@carreras_bp.route("/panel/vacantes/<int:vacante_id>/toggle", methods=["POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_toggle(vacante_id):
    """Activa o pone en pausa (no elimina: sirve como plantilla para reactivar)."""
    vacante = Vacante.query.get_or_404(vacante_id)
    vacante.activa = not vacante.activa
    db.session.commit()
    if vacante.activa:
        flash(f"«{vacante.titulo}» reactivada y visible públicamente.", "success")
    else:
        flash(
            f"«{vacante.titulo}» en pausa (ya no se muestra en la bolsa; puedes reactivarla después).",
            "info",
        )
    estado = request.form.get("estado") or request.args.get("estado") or "todas"
    return redirect(url_for("carreras.panel", estado=estado))


@carreras_bp.route("/panel/vacantes/<int:vacante_id>/duplicar", methods=["POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_duplicar(vacante_id):
    """Crea una nueva vacante copiando una existente (plantilla). Queda en pausa para editar."""
    origen = Vacante.query.get_or_404(vacante_id)
    nueva = Vacante(
        titulo=f"{origen.titulo} (nueva)",
        area=origen.area,
        ubicacion=origen.ubicacion,
        modalidad=origen.modalidad,
        tipo_contrato=origen.tipo_contrato,
        descripcion=origen.descripcion,
        requisitos=origen.requisitos,
        ofrecemos=origen.ofrecemos,
        salario=origen.salario,
        correo_1=origen.correo_1,
        correo_2=origen.correo_2,
        correo_3=origen.correo_3,
        enlace_occ=origen.enlace_occ,
        enlace_extra_nombre=origen.enlace_extra_nombre,
        enlace_extra_url=origen.enlace_extra_url,
        activa=False,
        creado_por_id=current_user.id,
    )
    db.session.add(nueva)
    db.session.commit()
    flash(
        "Plantilla duplicada. Ajusta título, salario u otros datos y reactívala cuando esté lista.",
        "success",
    )
    return redirect(url_for("carreras.vacante_editar", vacante_id=nueva.id))


@carreras_bp.route("/panel/vacantes/<int:vacante_id>/eliminar", methods=["POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_eliminar(vacante_id):
    """Elimina la vacante y sus postulaciones (incluidos CV en disco)."""
    vacante = Vacante.query.get_or_404(vacante_id)
    titulo = vacante.titulo
    n = vacante.total_postulaciones
    upload = Path(current_app.config["UPLOAD_FOLDER"])
    for p in vacante.postulaciones.all():
        if p.cv_filename:
            cv_path = upload / p.cv_filename
            if cv_path.is_file():
                try:
                    cv_path.unlink()
                except OSError:
                    pass
    db.session.delete(vacante)
    db.session.commit()
    extra = f" Se eliminaron también {n} postulación(es)." if n else ""
    flash(f"Vacante «{titulo}» eliminada.{extra}", "success")
    estado = request.form.get("estado") or "todas"
    return redirect(url_for("carreras.panel", estado=estado))


@carreras_bp.route("/panel/vacantes/<int:vacante_id>/postulaciones")
@require_rol(ROL_CAPITAL_HUMANO)
def vacante_postulaciones(vacante_id):
    vacante = Vacante.query.get_or_404(vacante_id)
    filtro = request.args.get("filtro", "todas")
    q = vacante.postulaciones
    postulaciones = _filtrar_postulaciones(q, filtro)
    conteos = _conteos_postulaciones(vacante.postulaciones)
    return render_template(
        "carreras/postulaciones.html",
        vacante=vacante,
        postulaciones=postulaciones,
        filtro=filtro,
        conteos=conteos,
    )


@carreras_bp.route("/panel/postulaciones-espontaneas")
@require_rol(ROL_CAPITAL_HUMANO)
def postulaciones_espontaneas():
    filtro = request.args.get("filtro", "todas")
    q = Postulacion.query.filter_by(vacante_id=None)
    postulaciones = _filtrar_postulaciones(q, filtro)
    conteos = _conteos_postulaciones(Postulacion.query.filter_by(vacante_id=None))
    return render_template(
        "carreras/postulaciones.html",
        vacante=None,
        postulaciones=postulaciones,
        filtro=filtro,
        conteos=conteos,
    )


@carreras_bp.route("/panel/postulaciones/<int:postulacion_id>/estado", methods=["POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def postulacion_estado(postulacion_id):
    postulacion = Postulacion.query.get_or_404(postulacion_id)
    nuevo = (request.form.get("estado") or "").strip().lower()
    if nuevo not in Postulacion.ESTADOS:
        flash("Estado no válido.", "danger")
    else:
        postulacion.estado = nuevo
        db.session.commit()
        flash(f"Marcado como «{Postulacion.ESTADOS[nuevo]}».", "success")

    filtro = request.form.get("filtro") or "todas"
    if postulacion.vacante_id:
        return redirect(
            url_for(
                "carreras.vacante_postulaciones",
                vacante_id=postulacion.vacante_id,
                filtro=filtro,
            )
        )
    return redirect(url_for("carreras.postulaciones_espontaneas", filtro=filtro))


@carreras_bp.route("/panel/cv/<int:postulacion_id>")
@require_rol(ROL_CAPITAL_HUMANO)
def descargar_cv(postulacion_id):
    postulacion = Postulacion.query.get_or_404(postulacion_id)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        postulacion.cv_filename,
        as_attachment=True,
        download_name=postulacion.cv_nombre_original,
    )


@carreras_bp.route("/panel/cv/<int:postulacion_id>/ver")
@require_rol(ROL_CAPITAL_HUMANO)
def ver_cv(postulacion_id):
    """Sirve el CV en línea (inline) para el modal de previsualización."""
    postulacion = Postulacion.query.get_or_404(postulacion_id)
    path = Path(current_app.config["UPLOAD_FOLDER"]) / postulacion.cv_filename
    if not path.is_file():
        flash("No se encontró el archivo del CV.", "danger")
        return redirect(url_for("carreras.panel"))

    ext = postulacion.cv_extension
    mime = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")

    resp = send_file(
        path,
        mimetype=mime,
        as_attachment=False,
        download_name=postulacion.cv_nombre_original,
        conditional=True,
    )
    resp.headers["Content-Disposition"] = (
        f'inline; filename="{postulacion.cv_nombre_original}"'
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


def _filtrar_postulaciones(query, filtro: str):
    """Aplica filtro de revisión y ordena por más reciente."""
    # Compatibilidad con "Nuevo" legacy
    if filtro == Postulacion.ESTADO_NUEVO:
        query = query.filter(
            or_(
                Postulacion.estado == Postulacion.ESTADO_NUEVO,
                Postulacion.estado == "Nuevo",
                Postulacion.estado.is_(None),
            )
        )
    elif filtro in Postulacion.ESTADOS:
        query = query.filter(Postulacion.estado == filtro)
    return query.order_by(Postulacion.creado_en.desc()).all()


def _conteos_postulaciones(query) -> dict:
    rows = query.all() if hasattr(query, "all") else list(query)
    # Si viene un Query de relationship dynamic o filter
    if not isinstance(rows, list):
        rows = list(rows)
    conteos = {
        "todas": len(rows),
        Postulacion.ESTADO_NUEVO: 0,
        Postulacion.ESTADO_INTERES: 0,
        Postulacion.ESTADO_DUDA: 0,
        Postulacion.ESTADO_DESCARTADO: 0,
    }
    for p in rows:
        key = p.estado_key
        if key in conteos:
            conteos[key] += 1
    return conteos


@carreras_bp.route("/panel/ajustes", methods=["GET", "POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def ajustes():
    ajustes_row = AjustesHR.get_or_create()
    if request.method == "POST":
        errores = _validar_correos_form(request.form, obligatorio=True)
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("carreras/ajustes.html", ajustes=ajustes_row), 400
        ajustes_row.correo_1 = request.form.get("correo_1", "").strip() or None
        ajustes_row.correo_2 = request.form.get("correo_2", "").strip() or None
        ajustes_row.correo_3 = request.form.get("correo_3", "").strip() or None
        db.session.commit()
        flash("Correos de notificación actualizados. Recibirán CVs espontáneos y postulaciones a vacantes.", "success")
        return redirect(url_for("carreras.ajustes"))
    return render_template("carreras/ajustes.html", ajustes=ajustes_row)


@carreras_bp.route("/panel/cuenta", methods=["GET", "POST"])
@require_rol(ROL_CAPITAL_HUMANO)
def cuenta():
    return gestionar_cuenta(ROL_CAPITAL_HUMANO, "carreras/cuenta.html", "carreras.cuenta")


def _validar_correos_form(form, obligatorio=True) -> list[str]:
    correos = [
        form.get("correo_1", "").strip(),
        form.get("correo_2", "").strip(),
        form.get("correo_3", "").strip(),
    ]
    errores = []
    llenos = [c for c in correos if c]
    if obligatorio and not llenos:
        errores.append("Indica al menos un correo para recibir las postulaciones.")
    for c in llenos:
        if "@" not in c or "." not in c.split("@")[-1]:
            errores.append(f"Correo inválido: {c}")
    return errores


def _vacante_desde_form(vacante: Vacante, form) -> Vacante:
    vacante.titulo = form.get("titulo", "").strip()
    vacante.area = form.get("area", "").strip()
    vacante.ubicacion = form.get("ubicacion", "Mérida, Yucatán").strip()
    vacante.modalidad = form.get("modalidad", "Presencial").strip()
    vacante.tipo_contrato = form.get("tipo_contrato", "Tiempo completo").strip()
    vacante.descripcion = form.get("descripcion", "").strip()
    vacante.requisitos = form.get("requisitos", "").strip()
    vacante.ofrecemos = form.get("ofrecemos", "").strip() or None
    vacante.salario = form.get("salario", "").strip() or None
    vacante.correo_1 = form.get("correo_1", "").strip() or None
    vacante.correo_2 = form.get("correo_2", "").strip() or None
    vacante.correo_3 = form.get("correo_3", "").strip() or None
    vacante.enlace_occ = form.get("enlace_occ", "").strip() or None
    vacante.enlace_extra_nombre = form.get("enlace_extra_nombre", "").strip() or None
    vacante.enlace_extra_url = form.get("enlace_extra_url", "").strip() or None
    vacante.activa = form.get("activa") == "on"
    return vacante
