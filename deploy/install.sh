#!/usr/bin/env bash
# One-shot installer for Ubuntu 22.04/24.04.
#
#   sudo bash deploy/install.sh
#
# Expects the repository (including a built frontend/dist and a filled .env)
# to be located at /opt/academic-paper-assistant.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/academic-paper-assistant}"
PIP_INDEX="${PIP_INDEX:-https://mirrors.cloud.tencent.com/pypi/simple}"

echo "==> installing into ${APP_DIR}"
cd "${APP_DIR}"

if [[ ! -f .env ]]; then
  echo "!! .env not found. Copy .env.example to .env and fill in LLM_API_KEY first." >&2
  exit 1
fi
if [[ ! -f frontend/dist/index.html ]]; then
  echo "!! frontend/dist is missing. Build it locally with: cd frontend && npm ci && npm run build" >&2
  exit 1
fi

echo "==> creating service user"
id -u apa >/dev/null 2>&1 || useradd --system --home "${APP_DIR}" --shell /usr/sbin/nologin apa

echo "==> python environment"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip -i "${PIP_INDEX}"
.venv/bin/pip install -r backend/requirements.txt -i "${PIP_INDEX}"

echo "==> permissions"
mkdir -p data
chown -R apa:apa "${APP_DIR}/data"
chown apa:apa .env
chmod 600 .env

echo "==> systemd unit"
install -m 644 deploy/apa.service /etc/systemd/system/apa.service
systemctl daemon-reload
systemctl enable apa
systemctl restart apa

sleep 2
systemctl --no-pager --lines=20 status apa || true
echo
echo "==> health check"
curl -fsS http://127.0.0.1/api/health || echo "health check failed - see: journalctl -u apa -n 100"
echo
echo "Done. Open http://<server-ip>/ and sign in with the ADMIN_* account from .env."
