from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent.parent
SITE = Path(__file__).resolve().parent.parent
OUT = SITE / "marnez" / "static" / "img" / "hero"
OUT.mkdir(parents=True, exist_ok=True)
BRAND_SRC = ROOT / "Sitio Web"

FILES = {
    "hero-night.jpg": BRAND_SRC / "bf5a0f1a-bcb8-4dbb-9445-7961495f1667-2026-04-23.jpeg",
    "hero-concept-1.jpg": BRAND_SRC / "freepik__necesito-que-generes-una-imagen-utilizando-la-refe__8621.png",
    "hero-concept-2.jpg": BRAND_SRC / "freepik__necessito-que-se-genere-una-imagen-con-base-a-la-i__83885.png",
    "hero-masterplan.jpg": BRAND_SRC / "Mapa_Mesa de trabajo 1.png",
    "hero-careers.jpg": ROOT / "Entrega Marnez 29 nov 2024" / "DSC_7903.jpg",
}

for name, src in FILES.items():
    if not src.exists():
        print("MISSING", src)
        continue
    with Image.open(src) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        max_w = 1920
        if w > max_w:
            im = im.resize((max_w, int(h * (max_w / w))), Image.LANCZOS)
        dest = OUT / name
        im.save(dest, "JPEG", quality=80, optimize=True, progressive=True)
        print("OK", dest, dest.stat().st_size // 1024, "KB")
