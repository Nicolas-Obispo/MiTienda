# app/routers/media_routers.py
# Router para manejo de uploads (MVP: filesystem local)

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
import os
import uuid

# ✅ Auth de MiPlaza/MiTienda (nombre real en tu proyecto)
from app.core.auth import obtener_usuario_actual
from app.models.usuarios_models import Usuario

router = APIRouter(
    prefix="/media",
    tags=["Media"]
)

# Extensiones MIME permitidas (MVP)
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Tamaño máximo (MVP) -> 5MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def _get_upload_dir() -> str:
    """
    Devuelve la ruta absoluta a la carpeta /uploads del backend.
    IMPORTANTE: Debe coincidir con lo montado en main.py.
    """
    # __file__ = backend/app/routers/media_routers.py
    # subimos 3 niveles -> backend/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
    return os.path.join(base_dir, "uploads")


@router.post("/upload")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Recibe un archivo por multipart/form-data, lo guarda en filesystem
    y devuelve una URL pública para accederlo via /uploads.

    Seguridad:
    - Requiere JWT válido (usuario_actual).
    """
    # usuario_actual se usa como guard de seguridad (no hace falta usarlo luego).

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {file.content_type}"
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Archivo demasiado grande (máx 5MB)"
        )

    upload_dir = _get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/uploads/{filename}"

    return {"url": public_url}
