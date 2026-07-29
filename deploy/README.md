# Despliegue en VPS Hostinger (por IP)

IP actual: `45.132.241.101`  
Sin dominio todavía: nginx escucha en el puerto 80 y hace proxy a Gunicorn en `127.0.0.1:8000`.

## Instalación rápida (en la VPS, como root)

```bash
apt-get update -y && apt-get install -y git
git clone https://github.com/soportemarnez-dot/Web-Marnez.git /tmp/web-marnez-bootstrap
bash /tmp/web-marnez-bootstrap/deploy/install.sh
```

O, si el repo ya está clonado en `/var/www/web-marnez`:

```bash
cd /var/www/web-marnez && bash deploy/install.sh
```

Al terminar abre: **http://45.132.241.101/**

El script imprime las contraseñas iniciales de Capital Humano y Comercial. Guárdalas y cámbialas desde el panel.

## Actualizar después de un push a GitHub

```bash
cd /var/www/web-marnez
git pull origin main
.venv/bin/pip install -r requirements.txt
systemctl restart web-marnez
```

## Archivos de este directorio

| Archivo | Uso |
|---------|-----|
| `nginx-web-marnez.conf` | Sitio nginx (IP) |
| `web-marnez.service` | systemd + Gunicorn |
| `install.sh` | Instalación / reinstalación |

## Cuando agregues el dominio

1. Apunta el DNS A del dominio a `45.132.241.101`.
2. En `nginx-web-marnez.conf` cambia `server_name` al dominio.
3. `nginx -t && systemctl reload nginx`
4. Instala SSL: `apt install certbot python3-certbot-nginx && certbot --nginx -d tudominio.com`
