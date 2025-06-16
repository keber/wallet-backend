#!/bin/bash
# scripts/create-service.sh

SERVICE_NAME=wallet-backend
USER=$(whoami)
WORKDIR=$(pwd)
VENV_PATH="$WORKDIR/venv/bin/uvicorn"

echo "Creando archivo de servicio en /etc/systemd/system/$SERVICE_NAME.service"

sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=FastAPI Wallet Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$WORKDIR
ExecStart=$VENV_PATH main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Recargando systemd y habilitando servicio..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "Servicio $SERVICE_NAME creado y levantado. Verifica con: sudo systemctl status $SERVICE_NAME"

