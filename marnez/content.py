"""Consultas públicas de contenido con cache en memoria."""

from __future__ import annotations

from .cache import cached, cache_invalidate
from .models import BlogPost, Desarrollo


def invalidate_content_cache() -> None:
    cache_invalidate("desarrollos:", "blogs:", "desarrollo:", "blog:")


def list_desarrollos_activos():
    return cached(
        "desarrollos:activos",
        lambda: Desarrollo.query.filter_by(activo=True)
        .order_by(Desarrollo.orden.asc(), Desarrollo.nombre.asc())
        .all(),
    )


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
