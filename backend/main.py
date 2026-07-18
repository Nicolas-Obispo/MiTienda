# main.py — Servidor principal del backend MiTienda

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import SessionLocal
from app.modules.products.services.rubros_services import asegurar_catalogo_rubros

# Routers
from app.modules.products.routes.productos_routers import router as productos_routers
from app.modules.users.routes.usuarios_routers import router as usuarios_routers
from app.modules.spaces.routes.comercios_routers import router as comercios_router
from app.modules.products.routes.rubros_routers import router as rubros_routers
from app.modules.products.routes.secciones_routers import router as secciones_router
from app.modules.search.routes.sugerencias_busqueda_routers import (
    router as sugerencias_busqueda_router,
)
from app.modules.availability.routes.horarios_atencion_routers import (
    router as horarios_atencion_router,
)

from app.modules.social.routes.publicaciones_guardadas_routers import router as publicaciones_guardadas_router
from app.modules.posts.routes.publicaciones_routers import router as publicaciones_router

from app.modules.stories.routes.historias_routers import router as historias_router
from app.modules.social.routes.likes_publicaciones_routers import router as likes_publicaciones_router
from app.modules.posts.routes.ranking_publicaciones_routers import router as ranking_publicaciones_router
from app.modules.posts.routes.feed_publicaciones_routers import router as feed_publicaciones_router
from app.modules.media.routes.media_routers import router as media_router

# 🔥 ETAPA 60 — Seguidores
from app.modules.social.routes.seguidores_routers import router as seguidores_router

from app.modules.analytics.routes.comercios_metricas_sociales_routers import (
    router as comercios_metricas_sociales_router,
)

from app.modules.analytics.routes.comercios_analytics_routers import (
    router as comercios_analytics_router,
)

from app.modules.analytics.routes.comercios_score_routers import (
    router as comercios_score_router,
)

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
@app.on_event("startup")
def inicializar_catalogos():
    db = SessionLocal()
    try:
        asegurar_catalogo_rubros(db)
    finally:
        db.close()


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
app.include_router(sugerencias_busqueda_router)
app.include_router(horarios_atencion_router)

# IMPORTANTE: guardadas antes que publicaciones
app.include_router(publicaciones_guardadas_router)
app.include_router(publicaciones_router)

app.include_router(historias_router)
app.include_router(likes_publicaciones_router)
app.include_router(ranking_publicaciones_router)
app.include_router(feed_publicaciones_router)
app.include_router(media_router)

# 🔥 ETAPA 60 — Seguidores
app.include_router(seguidores_router)

# 🔥 ETAPA 62 — Métricas sociales
app.include_router(comercios_metricas_sociales_router)
# 🔥 ETAPA 63 — Analytics Engine
app.include_router(comercios_analytics_router)
# 🔥 ETAPA 63 — Space Score Engine
app.include_router(comercios_score_router)
