#!/usr/bin/env bash
# Instalación en VPS Hostinger (Ubuntu) — Marnez por IP
# Uso (como root):
#   curl -fsSL ... | bash
#   o: bash deploy/install.sh
set -euo pipefail

APP_DIR=/var/www/web-marnez
REPO=https://github.com/soportemarnez-dot/Web-Marnez.git
BRANCH=main
VPS_IP=45.132.241.101

echo "==> Paquetes del sistema"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx git

echo "==> Clonar / actualizar repo"
mkdir -p /var/www
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git fetch origin
  git reset --hard "origin/$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone -b "$BRANCH" "$REPO" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> Virtualenv y dependencias"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "==> Carpetas de uploads y logs"
mkdir -p uploads/cv uploads/media /var/log/web-marnez
chown -R www-data:www-data "$APP_DIR" /var/log/web-marnez
chmod -R u+rwX,g+rX "$APP_DIR"

if [ ! -f "$APP_DIR/.env" ]; then
  echo "==> Creando .env de producción (cámbialo después)"
  SECRET=$(openssl rand -hex 32)
  cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=${SECRET}
DATABASE_URL=sqlite:////var/www/web-marnez/marnez.db
UPLOAD_FOLDER=uploads/cv
MEDIA_FOLDER=uploads/media
MAX_CONTENT_LENGTH_MB=8
ADMIN_EMAIL=capitalhumano@marnez.mx
ADMIN_PASSWORD=MarnezCH$(openssl rand -hex 4)
COMERCIAL_EMAIL=comercial@marnez.mx
COMERCIAL_PASSWORD=MarnezCom$(openssl rand -hex 4)
RESEND_API_KEY=
RESEND_FROM=
EOF
  chown www-data:www-data "$APP_DIR/.env"
  chmod 640 "$APP_DIR/.env"
  echo "---- Contraseñas iniciales (guárdalas) ----"
  grep -E 'ADMIN_|COMERCIAL_' "$APP_DIR/.env"
  echo "-------------------------------------------"
fi

echo "==> Systemd"
cp "$APP_DIR/deploy/web-marnez.service" /etc/systemd/system/web-marnez.service
systemctl daemon-reload
systemctl enable web-marnez
systemctl restart web-marnez

echo "==> Nginx"
cp "$APP_DIR/deploy/nginx-web-marnez.conf" /etc/nginx/sites-available/web-marnez
ln -sfn /etc/nginx/sites-available/web-marnez /etc/nginx/sites-enabled/web-marnez
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Firewall básico (si ufw está activo)
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 'Nginx Full' || ufw allow 80/tcp || true
fi

echo ""
echo "Listo. Abre: http://${VPS_IP}/"
echo "Servicio: systemctl status web-marnez"
echo "Logs:     journalctl -u web-marnez -f"
echo "Cuando tengas dominio, edita deploy/nginx-web-marnez.conf (server_name) y añade Certbot."
