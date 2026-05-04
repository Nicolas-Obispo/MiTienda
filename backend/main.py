# main.py — Servidor principal del backend MiTienda

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routers.productos_routers import router as productos_routers
from app.routers.usuarios_routers import router as usuarios_routers
from app.routers.comercios_routers import router as comercios_router
from app.routers.rubros_routers import router as rubros_routers
from app.routers.secciones_routers import router as secciones_router

from app.routers.publicaciones_guardadas_routers import router as publicaciones_guardadas_router
from app.routers.publicaciones_routers import router as publicaciones_router

from app.routers.historias_routers import router as historias_router
from app.routers.likes_publicaciones_routers import router as likes_publicaciones_router
from app.routers.ranking_publicaciones_routers import router as ranking_publicaciones_router
from app.routers.feed_publicaciones_routers import router as feed_publicaciones_router
from app.routers.media_routers import router as media_router

# 🔥 ETAPA 60 — Seguidores
from app.routers.seguidores_routers import router as seguidores_router

# ------------------------------
# Soporte para archivos estáticos (uploads)
# ------------------------------
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="MiTienda API",
    version="1.0"
)

# ------------------------------
# CORS (CORREGIDO PARA PC + CELULAR)
# ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"mensaje": "Bienvenido a MiTienda API 🚀"}

# ------------------------------
# Configuración carpeta uploads
# ------------------------------
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ------------------------------
# Registrar routers
# ------------------------------
app.include_router(productos_routers)
app.include_router(usuarios_routers)
app.include_router(comercios_router)
app.include_router(rubros_routers)
app.include_router(secciones_router)

# IMPORTANTE: guardadas antes que publicaciones
app.include_router(publicaciones_guardadas_router)
app.include_router(publicaciones_router)

app.include_router(historias_router)
app.include_router(likes_publicaciones_router)
app.include_router(ranking_publicaciones_router)
app.include_router(feed_publicaciones_router)
app.include_router(media_router)

# 🔥 ETAPA 60 — Seguidores (al final, no rompe nada existente)
app.include_router(seguidores_router)