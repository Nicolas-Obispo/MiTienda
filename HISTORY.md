# HISTORY.md — MiTienda

Este documento registra el **histórico paso a paso** del proyecto MiTienda.
Su objetivo es permitir retomar el desarrollo en cualquier momento,
sin perder contexto ni repetir trabajo ya realizado.

El orden de las etapas es **cronológico y acumulativo**.
Cada bloque cerrado representa un punto estable del sistema.

---

## Etapa 0 — Definición inicial del proyecto

En esta etapa se definieron los objetivos y las reglas base del proyecto:

- El proyecto se estructura por capas: frontend, backend y database.
- Cada capa es independiente y se comunica solo mediante interfaces definidas.
- El backend es la fuente de la verdad.
- Se prioriza la estabilidad y la documentación antes de avanzar.
- PROJECT.md se establece como fuente única de la verdad.
- HISTORY.md se establece como registro cronológico del proyecto.

Esta etapa define las reglas que rigen todo el desarrollo posterior.

---

## Etapa 1 — Backend (FastAPI + JWT)

En esta etapa se implementó un backend completo y funcional con FastAPI.

### Trabajo realizado
- Creación del proyecto backend.
- Configuración de entorno virtual.
- Configuración de conexión a base de datos MySQL.
- Implementación de modelos ORM con SQLAlchemy.
- Registro de usuarios.
- Login con JWT.
- Expiración de tokens.
- Endpoint protegido `/usuarios/me`.
- Logout real con revocación de tokens.
- Uso de variables de entorno (`.env`).
- Pruebas completas en Swagger, curl y navegador.

### Resultado
- Backend completamente funcional.
- Arquitectura por capas respetada.
- Backend considerado estable.

---

## Etapa 2 — Separación por capas

En esta etapa se realizó la separación física y lógica del proyecto.

### Trabajo realizado
- Separación definitiva de carpetas:
  - `frontend`
  - `backend`
  - `database`
- Verificación de que el backend funciona de forma independiente.
- Confirmación de que el frontend no accede directamente a la base de datos.
- Ajustes de ejecución para iniciar backend y frontend por separado.

### Resultado
- Capas desacopladas entre sí.
- Proyecto organizado para escalar sin romper dependencias.

---

## Etapa 3 — Frontend base (React + TailwindCSS)

En esta etapa se creó y validó el frontend base del proyecto.

### Trabajo realizado
- Creación del frontend con Vite + React.
- Ubicación del frontend fuera del backend.
- Instalación y configuración de TailwindCSS v4.
- Ajustes por cambios de Tailwind v4 (sin `tailwind.config.js`).
- Validación de estilos en navegador.
- Confirmación del servidor de desarrollo.

### Resultado
- Frontend operativo y separado del backend.
- Sistema de estilos funcionando correctamente.
- Frontend listo para navegación y conexión con la API.

---

## Etapa 4 — Navegación frontend (React Router)

En esta etapa se implementó la navegación base del frontend.

### Trabajo realizado
- Instalación y configuración de React Router.
- Definición de rutas principales (`/`, `/login`).
- Creación de estructura semántica:
  - `pages`
  - `layouts`
  - `router`
- Implementación de layout principal (`MainLayout`).
- Navegación funcionando correctamente.

### Resultado
- Navegación estable.
- Base sólida para flujo de autenticación.

---

## Etapa 5 — Autenticación Frontend (COMPLETADA)

Estado: ✅ **Estable y funcional**

En esta etapa se implementó el flujo completo de autenticación en el frontend,
integrado con el backend FastAPI.

### Funcionalidades logradas
- Login desde frontend contra backend.
- Manejo de JWT con React Context (AuthContext).
- Persistencia de sesión usando `localStorage`.
- Logout frontend con revocación real en backend.
- Comunicación frontend ↔ backend habilitada mediante CORS.
- Estado global de autenticación accesible desde toda la app.

### Detalles técnicos
- `AuthContext` centraliza token y estado de sesión.
- `authService` abstrae llamadas HTTP de autenticación.
- `Login.jsx` guarda correctamente el token en el contexto.
- `Home.jsx` fue utilizado temporalmente para debug y luego limpiado.
- Backend configurado con `CORSMiddleware`.

### Resultado
El frontend puede:
- Autenticarse correctamente.
- Mantener sesión activa.
- Cerrar sesión de forma segura.

---

## ✅ Checkpoint actual

El proyecto se encuentra en un **estado estable y seguro**.

### Estado actual
- Backend estable y documentado.
- Frontend con navegación y autenticación funcionando.
- Arquitectura por capas respetada.
- Código limpio (sin debug temporal).
- PROJECT.md alineado con el sistema real.
- Repositorio versionado en GitHub.

### Punto exacto para continuar

👉 **PASO 6 — Protección de rutas y autorización frontend**

A partir de este checkpoint, cualquier avance debe continuar desde este punto,
sin modificar ni repetir el trabajo previo.
