"""
Contenido semilla: desarrollos, blog y testimonios.
Los desarrollos y posts se migran a SQLite al arrancar (si la BD está vacía).
TESTIMONIOS / CERTIFICACIONES / EQUIPO siguen siendo estáticos aquí.
"""

DESARROLLOS = [
    {
        "slug": "costella",
        "nombre": "Costella",
        "tagline": "Telchac Residencial · Club de playa incluido",
        "ubicacion": "Telchac, Yucatán · 70 km de Mérida",
        "resumen": "Residencial de playa por etapas con club de playa, muelle, grill y áreas de bienestar frente al mar.",
        "descripcion": (
            "Costella Telchac Residencial está diseñado para ofrecerte una inversión segura y un estilo "
            "de vida inigualable cerca del mar. Con un proyecto urbanizado en 5 etapas, seguridad, "
            "infraestructura de calidad y planes de crecimiento, este desarrollo combina plusvalía, "
            "tranquilidad y proyección a futuro. Se encuentra a 70 km de Mérida y a 7 km del puerto de "
            "Telchac, cerca del Pueblo Mágico de Motul, la Marina Kinuh y la Reserva Ecológica de "
            "Sayachaltún."
        ),
        "amenidades": [
            "5 etapas · 533 lotes residenciales", "Lotes de 160 a 350 m²", "Acceso controlado 24/7",
            "Avenidas de 8 m y calles de 7 m", "Áreas verdes con vegetación endémica",
            "Torres departamentales y villas (futuro)", "Contrato adherido a PROFECO", "Escrituración inmediata",
        ],
        "precio_desde": 950000,
        "enganche_min_pct": 10,
        "plazos_meses": [12, 24, 36, 48],
        "estatus": "Disponible · Preventa",
        "portada": "costella-01.jpg",
        "galeria_count": 3,
        "hero_extra": "costella-masterplan.jpg",
        "video": "costella-anuncio.mp4",
        "video_poster": "costella-video-poster.jpg",
        "tour_360": "https://pap3ds.com/virtualtour/COSTELLA/index.htm",
        "video_youtube": "Xkwl8hI_CSc",
        "mapa_query": "Costella Telchac Residencial, Telchac Puerto, Yucatán",
        "mapa_img": "costella-mapa.jpg",
    },
    {
        "slug": "gran-riviera",
        "nombre": "Gran Riviera",
        "tagline": "Privada Caoba · Última etapa",
        "ubicacion": "Dzidzantún, Yucatán · 10 min de playa Santa Clara",
        "resumen": "Última etapa disponible (Caoba) del desarrollo semi urbanizado Gran Riviera, a 10 minutos de la playa.",
        "descripcion": (
            "Gran Riviera se encuentra ubicado estratégicamente a 10 minutos de las paradisiacas playas "
            "de Santa Clara en Dzidzantún, Yucatán, y a 45 minutos de la Ciudad de Mérida. Un desarrollo "
            "semi urbanizado organizado en privadas (Ceiba, Makulis, Cedros y Robles, ya vendidas, y "
            "Caoba, su última etapa disponible), ideal para quienes buscan cercanía a la playa con la "
            "tranquilidad de vivir fuera de la ciudad."
        ),
        "amenidades": ["Semi urbanizado", "10 min de playa Santa Clara", "Privada Caoba disponible", "Vialidades trazadas"],
        "precio_desde": 590000,
        "enganche_min_pct": 10,
        "plazos_meses": [12, 24, 36],
        "estatus": "Disponible · Privada Caoba",
        "portada": "gran-riviera-portada.jpg",
        "galeria_count": 6,
        "video": "gran-riviera-anuncio.mp4",
        "video_poster": "gran-riviera-video-poster.jpg",
        "mapa_query": "Dzidzantún, Yucatán, cerca de Playa Santa Clara",
        "mapa_img": "gran-riviera-mapa.jpg",
        "hero_extra": "gran-riviera-masterplan-3d.jpg",
    },
    {
        "slug": "antal",
        "nombre": "Antal",
        "tagline": "Semi urbanizado · Entregado",
        "ubicacion": "Yucatán",
        "resumen": "Residencial ya entregado, con amenidades consolidadas y comunidad activa.",
        "descripcion": (
            "Antal es uno de los desarrollos ya entregados por Marnez: un residencial semi urbanizado y "
            "consolidado, con una comunidad de vecinos activa. Ideal para quienes buscan un terreno con "
            "entrega inmediata y plusvalía comprobada."
        ),
        "amenidades": ["Áreas verdes", "Vialidades terminadas", "Seguridad 24/7", "Amenidades entregadas"],
        "precio_desde": 780000,
        "enganche_min_pct": 15,
        "plazos_meses": [12, 24, 36],
        "estatus": "Entregado",
        "portada": "antal-01.jpg",
        "galeria_count": 14,
        "mapa_query": "Yucatán, México",
        "mapa_img": "antal-mapa.jpg",
    },
    {
        "slug": "kinich",
        "nombre": "Kinich",
        "tagline": "Motul, Yucatán",
        "ubicacion": "Motul, Yucatán",
        "resumen": "Comunidad entregada en Motul, con enfoque en espacios familiares y naturaleza.",
        "descripcion": (
            "Kinich combina lotes residenciales con amplias áreas verdes y espacios familiares en Motul, "
            "Yucatán. Un desarrollo ya entregado, pensado para quienes valoran la tranquilidad sin "
            "alejarse de la ciudad."
        ),
        "amenidades": ["Parque central", "Andadores", "Áreas verdes", "Seguridad perimetral"],
        "precio_desde": 690000,
        "enganche_min_pct": 15,
        "plazos_meses": [12, 24, 36],
        "estatus": "Entregado",
        "portada": "kinich-01.jpg",
        "galeria_count": 14,
        "mapa_query": "Motul, Yucatán, México",
        "mapa_img": "kinich-mapa.jpg",
    },
    {
        "slug": "paraiso",
        "nombre": "Paraíso Telchac",
        "tagline": "Telchac, Yucatán",
        "ubicacion": "Telchac, Yucatán",
        "resumen": "Residencial entregado en Telchac con amenidades recreativas para toda la familia.",
        "descripcion": (
            "Paraíso Telchac es un residencial entregado con espacios recreativos pensados para toda la "
            "familia, vialidades terminadas y una plusvalía en crecimiento constante desde su entrega."
        ),
        "amenidades": ["Alberca", "Palapa social", "Áreas verdes", "Andadores"],
        "precio_desde": 720000,
        "enganche_min_pct": 15,
        "plazos_meses": [12, 24, 36],
        "estatus": "Entregado",
        "portada": "paraiso-01.jpg",
        "galeria_count": 13,
        "mapa_query": "Telchac Puerto, Yucatán, México",
        "mapa_img": "paraiso-mapa.jpg",
    },
    {
        "slug": "taruma",
        "nombre": "Tarumá",
        "tagline": "Riviera Telchac",
        "ubicacion": "Telchac, Yucatán",
        "resumen": "Desarrollo entregado en la Riviera de Telchac, con diseño contemporáneo y amenidades premium.",
        "descripcion": (
            "Tarumá, en la Riviera de Telchac, ofrece un diseño contemporáneo con amenidades premium ya "
            "entregadas: alberca, casa club y áreas verdes cuidadosamente planeadas para la vida en "
            "comunidad."
        ),
        "amenidades": ["Alberca", "Casa club", "Gimnasio", "Áreas verdes"],
        "precio_desde": 810000,
        "enganche_min_pct": 15,
        "plazos_meses": [12, 24, 36],
        "estatus": "Entregado",
        "portada": "taruma-01.jpg",
        "galeria_count": 14,
        "mapa_query": "Riviera Telchac, Telchac Puerto, Yucatán",
        "mapa_img": "taruma-mapa.jpg",
    },
    {
        "slug": "arennea",
        "nombre": "Arennea",
        "tagline": "Playa Santa Clara · Próximamente",
        "ubicacion": "97503 Dzidzantún, Yucatán · Playa Santa Clara",
        "resumen": "Nuevo desarrollo en Playa Santa Clara con 8 etapas y zona comercial central.",
        "descripcion": (
            "Arennea es el más nuevo desarrollo de Marnez en Playa Santa Clara: 8 etapas (Las Marinas, "
            "Las Conchas, Los Alisios, Las Palmas, Pelicanos, Los Muelles, Los Faros y Los Corales) "
            "organizadas alrededor de dos zonas comerciales centrales. Un proyecto pensado para quienes "
            "buscan invertir cerca de la playa con amenidades para toda la familia."
        ),
        "amenidades": ["Estacionamientos para autos", "Pet Park", "Canchas de usos múltiples", "Áreas de asadores", "Áreas verdes", "2 zonas comerciales"],
        "precio_desde": 490000,
        "enganche_min_pct": 10,
        "plazos_meses": [12, 24, 36],
        "estatus": "Próximamente",
        "portada": "arennea-portada.jpg",
        "galeria_count": 7,
        "mapa_query": "97503 Dzidzantún, Yucatán, México",
        "mapa_img": "arennea-mapa.jpg",
        "hero_extra": "arennea-masterplan-3d.jpg",
    },
]


def get_desarrollo(slug):
    return next((d for d in DESARROLLOS if d["slug"] == slug), None)


TESTIMONIOS = [
    {
        "nombre": "Karla Sugey Caballero Pérez",
        "iniciales": "KC",
        "detalle": "Cliente de Tarumá",
        "texto": "Es una empresa con certeza jurídica e información clara y precisa.",
    },
    {
        "nombre": "Vicente Alfredo Martín Cab",
        "iniciales": "VM",
        "detalle": "Cliente de Antal",
        "texto": "Considero a Marnez una empresa responsable en cada etapa del proceso.",
    },
    {
        "nombre": "Fernanda Ortiz",
        "iniciales": "FO",
        "detalle": "Cliente de Kinich",
        "texto": "El acompañamiento del equipo fue clave para tomar la mejor decisión de inversión.",
    },
]

CERTIFICACIONES = [
    "Protección jurídica patrimonial",
    "Escrituración inmediata",
    "Programa de referidos",
    "Cumplimiento normativo PROFECO",
]

BLOG_POSTS = [
    {
        "slug": "evita-fraudes-inmobiliarios-yucatan",
        "titulo": "Cómo evitar fraudes inmobiliarios en Yucatán",
        "resumen": "Revisa avances de obra reales, infraestructura visible y trayectoria comprobable antes de invertir en tierra.",
        "cuerpo": (
            "Antes de invertir en un terreno en Yucatán, visita el desarrollo, solicita evidencia de "
            "avance de obra y verifica la trayectoria de la desarrolladora ante instancias como INSEJUPY "
            "y PROFECO. En Marnez ponemos a tu disposición visitas guiadas y documentación de cada etapa "
            "de construcción para que inviertas con certeza."
        ),
        "imagen": "antal-02.jpg",
    },
    {
        "slug": "documentos-clave-antes-de-comprar",
        "titulo": "3 documentos clave que necesitas verificar antes de comprar",
        "resumen": "Te mostramos los documentos indispensables para adquirir una propiedad con seguridad jurídica.",
        "cuerpo": (
            "Escritura o título de propiedad, certificado de libertad de gravamen y el régimen de "
            "condominio son los tres documentos que todo comprador debe revisar. En Marnez ofrecemos "
            "escrituración inmediata y acompañamiento legal durante todo el proceso."
        ),
        "imagen": "kinich-03.jpg",
    },
    {
        "slug": "terrenos-con-club-de-playa",
        "titulo": "Terrenos en Yucatán con club de playa incluido",
        "resumen": "Descubre Costella en Telchac y vive tu inversión desde el primer día.",
        "cuerpo": (
            "Costella integra un club de playa exclusivo para residentes desde la primera etapa de "
            "entrega. Muelle, alberca, zona de grill y restaurante forman parte de la experiencia de "
            "vivir frente al mar en Telchac, Yucatán."
        ),
        "imagen": "costella-01.jpg",
    },
]


def get_post(slug):
    return next((p for p in BLOG_POSTS if p["slug"] == slug), None)


EQUIPO_FOTOS = [f"equipo-{i:02d}.jpg" for i in range(1, 18)]


_AMENITY_ICON_KEYWORDS = [
    (("playa", "muelle", "club de playa"), "beach"),
    (("alberca", "grill", "pet park y grill"), "pool"),
    (("kids park", "pet park", "mascota"), "paw"),
    (("ciclopista", "bici"), "bike"),
    (("torre", "departamento", "villas"), "building"),
    (("wellness", "gym", "gimnasio"), "dumbbell"),
    (("área verde", "areas verdes", "parque", "vegetación", "paisaj"), "leaf"),
    (("acceso controlado", "seguridad", "vigilancia", "24/7"), "shield"),
    (("avenida", "calle", "vialidad"), "road"),
    (("lote", "m²"), "grid"),
    (("casa club",), "home"),
    (("estacionamiento",), "car"),
    (("cancha",), "ball"),
    (("asador",), "fire"),
    (("comercial",), "shop"),
    (("semi urbaniz", "etapa"), "crane"),
    (("privada", "disponible"), "flag"),
    (("profeco", "contrato", "escritura"), "doc"),
]


def amenity_icon_key(texto: str) -> str:
    """Elige un icono representativo segun palabras clave del texto de la amenidad."""
    t = (texto or "").lower()
    for keywords, key in _AMENITY_ICON_KEYWORDS:
        if any(kw in t for kw in keywords):
            return key
    return "check"
