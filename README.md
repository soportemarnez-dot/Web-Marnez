# Web Marnez — Sitio oficial de Marnez Desarrollos

Sitio web corporativo de **Marnez Desarrollos** (Mérida / Yucatán): desarrollos inmobiliarios, blog, contacto y bolsas de trabajo internas, con paneles de administración separados para Capital Humano y Comercial.

Repositorio: [soportemarnez-dot/Web-Marnez](https://github.com/soportemarnez-dot/Web-Marnez)

---

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3 + Flask |
| Plantillas | Jinja2 |
| Base de datos | SQLite + SQLAlchemy (Flask-SQLAlchemy) |
| Auth | Flask-Login (roles: Capital Humano / Comercial) |
| Formularios | Flask-WTF (CSRF) |
| Correo | Resend (notificaciones de postulaciones) |
| Frontend | Tailwind (CDN), Alpine.js, AOS, CSS/JS propios |

---

## Funcionalidades principales

### Sitio público
- Inicio, listado y detalle de **desarrollos** (galería, video, tour 360, mapa, cotizador)
- **Blog** editorial
- **Nosotros** y **Contacto** (leads en base de datos)
- **Únete a Nosotros**: vacantes activas, postulación con CV y candidatura espontánea

### Panel Capital Humano (`/unete-a-nosotros/panel`)
- Login exclusivo para rol `capital_humano`
- CRUD de vacantes
- Revisión de postulaciones y descarga de CVs
- Hasta **3 correos globales** de notificación (CVs espontáneos **y** postulaciones a vacantes)
- Correos extra opcionales por vacante
- Cambio de contraseña y alta / desactivación de usuarios del mismo rol

### Panel Comercial (`/panel-comercial`)
- Login exclusivo para rol `comercial`
- CMS de **blogs** (textos, imagen, tamaño de letra, previsualización)
- CMS de **desarrollos** (textos, precios, amenidades, portada, galería, videos)
- Plazos de financiamiento con **interés anual opcional** por plazo (cotizador con cuota fija)
- Gestión de cuenta y usuarios del rol comercial

---

## Requisitos

- Python 3.10+ recomendado
- Cuenta Resend (opcional en desarrollo; sin API key las postulaciones se guardan igual)

---

## Instalación local

```bash
git clone https://github.com/soportemarnez-dot/Web-Marnez.git
cd Web-Marnez

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copia el ejemplo de variables de entorno y ajústalo:

```bash
copy .env.example .env
# o: cp .env.example .env
```

Edita `.env` (nunca subas este archivo al repositorio):

```env
SECRET_KEY=una-clave-larga-y-aleatoria
DATABASE_URL=sqlite:///marnez.db

ADMIN_EMAIL=capitalhumano@marnez.mx
ADMIN_PASSWORD=cambia-esta-password

COMERCIAL_EMAIL=comercial@marnez.mx
COMERCIAL_PASSWORD=cambia-esta-password

RESEND_API_KEY=re_xxxxxxxx
RESEND_FROM=Capital Humano <noreply@tudominio-verificado.com>

UPLOAD_FOLDER=uploads/cv
MEDIA_FOLDER=uploads/media
MAX_CONTENT_LENGTH_MB=8
```

Arranque:

```bash
python app.py
```

Por defecto: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Al primer arranque se crean las tablas, se siembra el contenido editorial base (desarrollos / blog) y los usuarios admin definidos en `.env`.

---

## URLs útiles

| Ruta | Descripción |
|------|-------------|
| `/` | Inicio |
| `/desarrollos` | Catálogo |
| `/blog` | Artículos |
| `/contacto` | Formulario de contacto |
| `/unete-a-nosotros` | Vacantes públicas |
| `/unete-a-nosotros/panel/login` | Panel Capital Humano |
| `/panel-comercial/login` | Panel Comercial |

---

## Estructura del proyecto

```
Web-Marnez/
├── app.py                 # Punto de entrada
├── config.py              # Configuración desde .env
├── requirements.txt
├── .env.example
├── marnez/
│   ├── __init__.py        # Factory Flask
│   ├── models.py          # Usuarios, vacantes, blogs, desarrollos…
│   ├── data.py            # Semilla editorial (testimonios, etc.)
│   ├── mail.py            # Envío Resend
│   ├── content.py         # Consultas públicas + cache
│   ├── media.py           # Uploads y URLs de medios
│   ├── carreras/          # Blueprint RRHH / vacantes
│   ├── comercial/         # Blueprint CMS comercial
│   ├── main/              # Rutas del sitio público
│   ├── static/            # CSS, JS, imágenes, video
│   └── templates/         # Jinja2
├── uploads/               # CV y media (ignorados en git salvo .gitkeep)
└── scripts/               # Utilidades (p. ej. optimización de imágenes)
```

---

## Seguridad

- Secretos solo en `.env` (listado en `.gitignore`)
- Contraseñas con hash Werkzeug
- Roles separados: un usuario de Capital Humano no entra al panel comercial y viceversa
- CSRF en formularios de paneles y públicos
- Validación de extensiones y tamaño en CVs e imágenes/videos del CMS
- La base SQLite (`*.db`) **no** se versiona

---

## Cotizador en desarrollos

En el panel comercial, cada plazo puede llevar un **interés anual %**:

- `0%` → mensualidad = (precio − enganche) ÷ meses  
- Con interés → cuota fija (amortización francesa)

Es un cálculo referencial para el visitante; no sustituye una cotización formal.

---

## Producción (notas)

1. Cambia `SECRET_KEY` y todas las contraseñas por defecto.
2. Usa un dominio verificado en Resend para `RESEND_FROM`.
3. Sirve la app detrás de un process manager (gunicorn / waitress) y un proxy (nginx).
4. Respaldos periódicos del archivo SQLite y de `uploads/`.
5. Considera HTTPS obligatorio y cookies seguras en el despliegue real.

---

## Autor

**Nilson Manuel Novelo Ek**  
Proyecto web Marnez Desarrollos — repositorio institucional de soporte.

---

## Licencia

Uso interno / propiedad de Marnez Desarrollos. Todos los derechos reservados.
