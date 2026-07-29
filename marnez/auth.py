from functools import wraps

from flask import flash, redirect, url_for, request, render_template
from flask_login import current_user, login_required

from .extensions import db
from .models import Usuario


def require_rol(*roles):
    """Exige sesión activa y que el usuario tenga uno de los roles dados."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.activo:
                flash("Tu cuenta está desactivada o la sesión expiró.", "danger")
                return redirect(url_for("carreras.login"))
            if current_user.rol not in roles:
                flash("No tienes permiso para acceder a esta sección.", "danger")
                if current_user.es_comercial:
                    return redirect(url_for("comercial.panel"))
                return redirect(url_for("carreras.panel"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def unauthorized_handler():
    """Redirige al login correcto según la ruta solicitada."""
    if request.path.startswith("/panel-comercial"):
        return redirect(url_for("comercial.login", next=request.url))
    return redirect(url_for("carreras.login", next=request.url))


def gestionar_cuenta(rol, template, endpoint):
    """Cambiar contraseña + alta / activar-desactivar usuarios del mismo rol."""
    usuarios = Usuario.query.filter_by(rol=rol).order_by(Usuario.nombre.asc()).all()
    if request.method == "POST":
        accion = request.form.get("accion", "")
        if accion == "password":
            actual = request.form.get("password_actual", "")
            nueva = request.form.get("password_nueva", "")
            confirmar = request.form.get("password_confirmar", "")
            if not current_user.check_password(actual):
                flash("La contraseña actual no es correcta.", "danger")
            elif len(nueva) < 8:
                flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
            elif nueva != confirmar:
                flash("La confirmación no coincide.", "danger")
            else:
                current_user.set_password(nueva)
                db.session.commit()
                flash("Contraseña actualizada.", "success")
            return redirect(url_for(endpoint))

        if accion == "nuevo":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not nombre or not email or "@" not in email:
                flash("Nombre y correo válidos son obligatorios.", "danger")
            elif len(password) < 8:
                flash("La contraseña debe tener al menos 8 caracteres.", "danger")
            elif Usuario.query.filter_by(email=email).first():
                flash("Ese correo ya está registrado.", "danger")
            else:
                u = Usuario(nombre=nombre, email=email, rol=rol, activo=True)
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                flash(f"Usuario {email} creado.", "success")
            return redirect(url_for(endpoint))

        if accion == "toggle":
            uid = request.form.get("usuario_id", type=int)
            u = Usuario.query.filter_by(id=uid, rol=rol).first_or_404()
            if u.id == current_user.id:
                flash("No puedes desactivar tu propia cuenta.", "warning")
            else:
                u.activo = not u.activo
                db.session.commit()
                flash(
                    f"Usuario {'activado' if u.activo else 'desactivado'}: {u.email}",
                    "success",
                )
            return redirect(url_for(endpoint))

    return render_template(template, usuarios=usuarios)