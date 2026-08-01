# app/modules/media/routes/media_routers.py
# Router para manejo de uploads (MVP: filesystem local)

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
import os
import time
import uuid

# ✅ Auth de MiPlaza/MiTienda (nombre real en tu proyecto)
from app.core.auth import obtener_usuario_actual
from app.core.operation_metrics import (
    METRIC_UPLOAD_ACCEPTED_COUNT,
    METRIC_UPLOAD_DURATION_MS,
    METRIC_UPLOAD_REJECTED_COUNT,
    increment_counter,
    record_duration,
)
from app.modules.users.models.usuarios_models import Usuario

router = APIRouter(
    prefix="/media",
    tags=["Media"]
)

# Extensiones MIME permitidas (MVP)
ALLOWED_CONTENT_TYPES = {
    # Imágenes
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",

    # Videos
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/ogg": ".ogg",
    "video/quicktime": ".mov",
}

# Tamaño máximo (MVP)
# - Imágenes y videos comparten el mismo endpoint.
# - Subimos el límite porque un video corto pesa más que una imagen.
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def _get_upload_dir() -> str:
    """
    Devuelve la ruta absoluta a la carpeta /uploads del backend.
    Debe coincidir con lo montado en main.py.
    """
    # __file__ = backend/app/modules/media/routes/media_routers.py
    # subimos 5 niveles -> backend/
    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            )
        )
    )

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
    started = time.perf_counter()

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        _record_upload_metrics(started, accepted=False, reason="content_type")
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {file.content_type}"
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        _record_upload_metrics(started, accepted=False, reason="size")
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

    public_url = f"/uploads/{filename}"

    _record_upload_metrics(started, accepted=True, media_type=_media_type(file.content_type))
    return {"url": public_url}


def _record_upload_metrics(
    started: float,
    *,
    accepted: bool,
    reason: str | None = None,
    media_type: str | None = None,
) -> None:
    tags = {"result": "accepted" if accepted else "rejected"}
    if reason:
        tags["reason"] = reason
    if media_type:
        tags["media_type"] = media_type

    increment_counter(
        METRIC_UPLOAD_ACCEPTED_COUNT if accepted else METRIC_UPLOAD_REJECTED_COUNT,
        tags=tags,
    )
    record_duration(
        METRIC_UPLOAD_DURATION_MS,
        round((time.perf_counter() - started) * 1000, 3),
        tags=tags,
    )


def _media_type(content_type: str | None) -> str:
    if not content_type:
        return "unknown"
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("video/"):
        return "video"
    return "other"
