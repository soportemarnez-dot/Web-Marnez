from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent.parent  # .../web marnez
SITE = Path(__file__).resolve().parent.parent  # .../sitio-marnez
IMG = SITE / "marnez" / "static" / "img"

def save(src: Path, dest: Path, max_w: int, quality: int = 80):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if w > max_w:
            im = im.resize((max_w, int(h * (max_w / w))), Image.LANCZOS)
        im.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"OK {dest.relative_to(SITE)}  {dest.stat().st_size // 1024} KB")

# ---- Mapas de ubicacion (renders personalizados) --------------------------
save(ROOT / "Maps Costella-03.png", IMG / "desarrollos" / "costella" / "costella-mapa.jpg", 1600, 85)
save(ROOT / "Gran Riviera Maps.png", IMG / "desarrollos" / "gran-riviera" / "gran-riviera-mapa.jpg", 1600, 85)
save(ROOT / "Arennea Maps_Mesa de trabajo 1.png", IMG / "desarrollos" / "arennea" / "arennea-mapa.jpg", 1600, 85)

# ---- Galeria Gran Riviera ---------------------------------------------------
GR = ROOT / "Render-Gran rivera"
gr_files = [
    GR / "Fachada 1 edit.png",
    GR / "Fachada 2 edit 3.png",
    GR / "GR CAOBA 1_Edit.png",
    GR / "GR Area Grill.png",
    GR / "Área de yoga.jpg",
    GR / "Área de lectura y relajación.jpg",
]
for i, f in enumerate(gr_files, start=1):
    save(f, IMG / "desarrollos" / "gran-riviera" / f"gran-riviera-render-{i:02d}.jpg", 1400)

# portada nueva (mas atractiva que el masterplan)
save(GR / "Fachada 1 edit.png", IMG / "desarrollos" / "gran-riviera" / "gran-riviera-portada.jpg", 1920)

# ---- Galeria Arennea ---------------------------------------------------
AR = ROOT / "Render-Arennea"
ar_files = [
    AR / "Glorieta 1.jpg",
    AR / "Pet Park 1.jpg",
    AR / "Asadores.jpg",
    AR / "Canchas.jpg",
    AR / "Área Verde Pequeña.jpg",
    AR / "Glorieta 2.jpg",
    AR / "Pet Park 2.jpg",
]
for i, f in enumerate(ar_files, start=1):
    save(f, IMG / "desarrollos" / "arennea" / f"arennea-render-{i:02d}.jpg", 1400)

save(AR / "Glorieta 1.jpg", IMG / "desarrollos" / "arennea" / "arennea-portada.jpg", 1920)

print("\nListo.")
