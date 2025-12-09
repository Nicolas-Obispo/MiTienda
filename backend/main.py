# main.py — Servidor principal del backend MiTienda

from fastapi import FastAPI

# Routers
from app.routers.productos_routers import router as productos_routers
from app.routers.usuarios_routers import router as usuarios_routers  

app = FastAPI(
    title="MiTienda API",
    version="1.0"
)

@app.get("/")
def home():
    return {"mensaje": "Bienvenido a MiTienda API 🚀"}

# ✅ Registrar routers
app.include_router(productos_routers)
app.include_router(usuarios_routers)  
