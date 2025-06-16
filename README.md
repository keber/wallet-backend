# Wallet Backend (FastAPI + SQLite)

API backend para una wallet digital, desarrollado con FastAPI, SQLite y bcrypt.

## Requisitos

- Python 3.10+
- `venv`
- `uvicorn`

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configurar como servicio

```bash
chmod +x ./scripts/create-service.sh
./scripts/create-service.sh
```

Esto debería levantar el servicio. Verificar con 

```bash
sudo systemctl status wallet-backend
```

### Habilitar y levantar el servicio manualmente

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable wallet-backend.service
sudo systemctl start wallet-backend.service
```


## Configurar subdominio

### Crear sub dominio en DNS

Crear registro tipo A , de nombre wallet-api apuntando a la IP del vps
- wallet-api.tudominio.com

### Crear sitio con EasyEngine

Estas instrucciones asumen la existencia de un dominio previamente creado con EasyEngine con certificado ssl wildcard de letsencrypt.

```bash
sudo ee site create walet-api.tudominio.com --type=html --ssl=inherit
```

### Editar el bloque nginx para hacer proxy

```bash
sudo vim /opt/easyengine/sites/wallet-api.tudominio.com/config/nginx/conf/user.conf
```

Agregar lo siguiente:
```nginx
location / {
    proxy_pass http://IP_DEL_VPS:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Reiniciar nginx
```bash
sudo ee site reload wallet-api.tudominio.com
```

## Verificar

```bash
curl https://wallet-api.tudominio.com/register
```

Deberías obtener una respuesta del backend
