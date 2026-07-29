"""
Optimiza y organiza las imagenes fuente del cliente hacia static/img.
Redimensiona a un ancho maximo razonable para web y comprime a JPEG/WEBP.
Se ejecuta una sola vez (o cuando se agreguen fotos nuevas) - no forma
parte del request/response de la app en produccion.
"""
import os
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent.parent  # .../web marnez
SITE = Path(__file__).resolve().parent.parent  # .../sitio-marnez
OUT = SITE / "marnez" / "static" / "img"

MAX_W_HERO = 1920
MAX_W_GALLERY = 1400
MAX_W_THUMB = 640
JPEG_QUALITY = 78

def save_optimized(src: Path, dest: Path, max_w: int, quality: int = JPEG_QUALITY):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB") if im.mode in ("RGBA", "P", "LA") else im
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if w > max_w:
            new_h = int(h * (max_w / w))
            im = im.resize((max_w, new_h), Image.LANCZOS)
        im.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"OK  {dest.relative_to(SITE)}  ({dest.stat().st_size // 1024} KB)")

def save_png_logo(src: Path, dest: Path, max_w: int = 800):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        w, h = im.size
        if w > max_w:
            new_h = int(h * (max_w / w))
            im = im.resize((max_w, new_h), Image.LANCZOS)
        im.save(dest, "PNG", optimize=True)
    print(f"OK  {dest.relative_to(SITE)}  ({dest.stat().st_size // 1024} KB)")

# ---- Branding (logos, iconos) -------------------------------------------------
BRAND_SRC = ROOT / "Sitio Web"
save_png_logo(BRAND_SRC / "Grupo -1.png", OUT / "brand" / "logo-marnez.png", 600)

# ---- Desarrollos: carpeta fuente -> slug del proyecto -------------------------
DEVELOPMENTS = {
    "costella": {
        "src": BRAND_SRC,
        "pick": ["MP.png"],  # masterplan
        "max_w": MAX_W_GALLERY,
    },
    "antal": {
        "src": ROOT / "Antal_Entrega_Foto",
        "pick": None,  # todas (se limita con LIMIT)
        "max_w": MAX_W_GALLERY,
    },
    "marnez-central": {
        "src": ROOT / "Entrega Marnez 29 nov 2024",
        "pick": None,
        "max_w": MAX_W_GALLERY,
    },
    "kinich": {
        "src": ROOT / "Entrega_Kinich" / "Entrega_Kinich",
        "pick": None,
        "max_w": MAX_W_GALLERY,
    },
    "paraiso": {
        "src": ROOT / "Paraiso_Entrega",
        "pick": None,
        "max_w": MAX_W_GALLERY,
    },
    "taruma": {
        "src": ROOT / "Taruma_Entrega_Fotos",
        "pick": None,
        "max_w": MAX_W_GALLERY,
    },
}

LIMIT_PER_GALLERY = 14
VALID_EXT = {".jpg", ".jpeg", ".png"}

for slug, cfg in DEVELOPMENTS.items():
    src_dir = cfg["src"]
    if not src_dir.exists():
        print(f"SKIP {slug}: {src_dir} no existe")
        continue
    if cfg["pick"]:
        files = [src_dir / name for name in cfg["pick"]]
    else:
        files = sorted(
            [p for p in src_dir.iterdir() if p.suffix.lower() in VALID_EXT and "_edit" not in p.stem.lower()],
            key=lambda p: p.stat().st_size,
            reverse=True,
        )[:LIMIT_PER_GALLERY]
    for i, f in enumerate(files, start=1):
        if not f.exists():
            print(f"MISSING {f}")
            continue
        dest = OUT / "desarrollos" / slug / f"{slug}-{i:02d}.jpg"
        try:
            save_optimized(f, dest, cfg["max_w"])
        except Exception as e:
            print(f"ERROR {f}: {e}")

print("\nListo.")
