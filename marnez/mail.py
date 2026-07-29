"""Envío de correos vía Resend (notificaciones de postulaciones)."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from flask import current_app, url_for

logger = logging.getLogger(__name__)


def enviar_email_resend(*, to: list[str], subject: str, html: str, attachments: list | None = None) -> bool:
    if not to:
        return False
    api_key = current_app.config.get("RESEND_API_KEY") or ""
    from_addr = current_app.config.get("RESEND_FROM") or ""
    if not api_key or not from_addr:
        logger.warning("Resend no configurado; omitiendo email.")
        return False
    try:
        import resend

        resend.api_key = api_key
        params: dict = {
            "from": from_addr,
            "to": to[:3],
            "subject": subject,
            "html": html,
        }
        if attachments:
            params["attachments"] = attachments
        resend.Emails.send(params)
        return True
    except Exception:
        logger.exception("Error enviando email Resend: %s", subject)
        return False


def enviar_notificacion_postulacion(postulacion, destinos: list[str], vacante=None) -> bool:
    """Envía aviso a Capital Humano. No lanza; retorna True si al menos un envío ok."""
    if not destinos:
        logger.info("Postulación %s sin correos destino; solo queda en panel.", postulacion.id)
        return False

    puesto = (
        vacante.titulo
        if vacante
        else (postulacion.puesto_deseado or "Candidatura espontánea")
    )
    subject = f"Nueva postulación: {puesto} — {postulacion.nombre}"
    if vacante:
        panel_url = url_for(
            "carreras.vacante_postulaciones", vacante_id=vacante.id, _external=True
        )
    else:
        panel_url = url_for("carreras.postulaciones_espontaneas", _external=True)
    cv_url = url_for("carreras.descargar_cv", postulacion_id=postulacion.id, _external=True)

    html = f"""
    <h2>Nueva postulación recibida</h2>
    <p><strong>Puesto:</strong> {puesto}</p>
    <p><strong>Nombre:</strong> {postulacion.nombre}</p>
    <p><strong>Correo:</strong> {postulacion.email}</p>
    <p><strong>Teléfono:</strong> {postulacion.telefono}</p>
    <p><strong>Mensaje:</strong><br>{(postulacion.mensaje or '—').replace(chr(10), '<br>')}</p>
    <p><a href="{cv_url}">Descargar CV ({postulacion.cv_nombre_original})</a></p>
    <p><a href="{panel_url}">Ver en el panel de Capital Humano</a></p>
    """

    attachments = []
    cv_path = Path(current_app.config["UPLOAD_FOLDER"]) / postulacion.cv_filename
    if cv_path.is_file() and cv_path.stat().st_size <= 5 * 1024 * 1024:
        attachments.append(
            {
                "filename": postulacion.cv_nombre_original,
                "content": base64.b64encode(cv_path.read_bytes()).decode("ascii"),
            }
        )

    ok = enviar_email_resend(to=destinos, subject=subject, html=html, attachments=attachments or None)
    if ok:
        logger.info("Notificación de postulación %s enviada a %s", postulacion.id, destinos)
    return ok


def enviar_notificacion_lead(lead, destinos: list[str]) -> bool:
    """Aviso de formulario de contacto / cotización a Comercial."""
    if not destinos:
        logger.info("Lead %s sin correos destino; solo queda en BD.", lead.id)
        return False
    subject = f"Nueva solicitud de contacto — {lead.nombre}"
    html = f"""
    <h2>Nueva solicitud de contacto / cotización</h2>
    <p><strong>Nombre:</strong> {lead.nombre}</p>
    <p><strong>Correo:</strong> {lead.email}</p>
    <p><strong>Teléfono:</strong> {lead.telefono}</p>
    <p><strong>Desarrollo de interés:</strong> {lead.desarrollo_interes or 'No especificado'}</p>
    <p><strong>Mensaje:</strong><br>{(lead.mensaje or '—').replace(chr(10), '<br>')}</p>
    """
    ok = enviar_email_resend(to=destinos, subject=subject, html=html)
    if ok:
        logger.info("Notificación de lead %s enviada a %s", lead.id, destinos)
    return ok
