"""Consultas públicas de contenido con cache en memoria."""

from __future__ import annotations

from .cache import cached, cache_invalidate
from .models import BlogPost, Desarrollo


def invalidate_content_cache() -> None:
    cache_invalidate("desarrollos:", "blogs:", "desarrollo:", "blog:")


def list_desarrollos_activos(categoria: str | None = None):
    key = f"desarrollos:activos:{categoria or 'all'}"

    def loader():
        q = Desarrollo.query.filter_by(activo=True)
        if categoria:
            q = q.filter_by(categoria=categoria)
        return q.order_by(Desarrollo.orden.asc(), Desarrollo.nombre.asc()).all()

    return cached(key, loader)


def list_desarrollos_disponibles():
    return list_desarrollos_activos(Desarrollo.CAT_DISPONIBLE)


def list_desarrollos_entregados():
    return list_desarrollos_activos(Desarrollo.CAT_ENTREGADO)


def get_desarrollo(slug: str):
    return cached(
        f"desarrollo:{slug}",
        lambda: Desarrollo.query.filter_by(slug=slug, activo=True).first(),
    )


def list_blog_posts(limit: int | None = None):
    key = f"blogs:publicados:{limit or 'all'}"

    def loader():
        q = BlogPost.query.filter_by(publicado=True).order_by(BlogPost.creado_en.desc())
        if limit:
            return q.limit(limit).all()
        return q.all()

    return cached(key, loader)


def get_blog_post(slug: str):
    return cached(
        f"blog:{slug}",
        lambda: BlogPost.query.filter_by(slug=slug, publicado=True).first(),
    )
