# PROJECT.md — MiTienda

## 1. Visión general

MiTienda es un proyecto tipo marketplace con arquitectura por capas.
El sistema está compuesto por Frontend, Backend y Base de Datos, cada uno
independiente y comunicándose únicamente mediante interfaces bien definidas.

Este documento es la **fuente única de la verdad** del proyecto.
Cualquier cambio que contradiga este archivo debe ser aprobado explícitamente.

---

## 2. Arquitectura por capas (obligatoria)

Estructura física del proyecto:

C:\Mitienda
├── frontend   → Interfaz de usuario (React)
├── backend    → API, lógica de negocio y seguridad (FastAPI)
└── database   → Base de datos física (MySQL)

---

## 3. Reglas obligatorias de arquitectura

- El frontend NO accede directamente a la base de datos.
- El frontend NO importa código del backend.
- El backend NO contiene código del frontend.
- La base de datos NO contiene código de aplicación.
- Toda comunicación entre capas se realiza mediante API REST (HTTP + JSON).
- El backend es la única capa autorizada a acceder a la base de datos.

---

## 4. Reglas de trabajo, calidad y consistencia (OBLIGATORIAS)

Estas reglas rigen **cómo se desarrolla** MiTienda y **cómo se protege** el código.
Son vinculantes para todas las etapas del proyecto.

### 4.1 Método de avance (paso a paso)

- El desarrollo se realiza **paso a paso**.
- El asistente propone **un solo paso por vez**.
- El usuario confirma explícitamente antes de continuar.
- Se evita avanzar múltiples pasos juntos para no saltear lógica ni romper flujo.

### 4.2 Protección del código y la arquitectura existente

- No se recrean archivos existentes sin indicación explícita.
- No se mueven ni renombran carpetas o archivos sin confirmación previa si afecta arquitectura.
- Todo cambio estructural debe ser informado y aprobado antes de aplicarse.

### 4.3 Estilo, nombres y mantenibilidad

- Todo código nuevo debe incluir **comentarios claros** explicando:
  - propósito del archivo
  - responsabilidad de funciones
  - decisiones relevantes
- Los nombres deben ser:
  - semánticos
  - explícitos
  - coherentes con su responsabilidad
- Se mantiene consistencia de nombres entre capas.

Ejemplos:
- `usuarios_models.py` ↔ `usuarios_services.py` ↔ `usuarios_routers.py`
- `AuthContext.jsx` ↔ `authService.js`

### 4.4 Gestión de archivos (lista archivero)

- Se mantiene una **lista archivero lógica** que contempla:
  - carpetas creadas
  - archivos creados
  - propósito de cada archivo
- Antes de crear algo nuevo se debe verificar:
  - que no exista algo equivalente
  - que el nombre sea coherente con la estructura actual
- No se crean archivos duplicados para una misma responsabilidad.

### 4.5 Regla de modificación de archivos

- Siempre debe indicarse si un cambio implica:
  - **reemplazar completamente** un archivo existente, o
  - **agregar/modificar** partes puntuales.
- El asistente debe aclararlo antes de escribir código.

### 4.6 Documentación por bloques (ESTADOS)

- 🟢 **ESTADO A — Desarrollo normal**
  - Se avanza con código.
  - NO se actualiza PROJECT.md ni HISTORY.md por cambios pequeños.

- 🟡 **ESTADO B — Cierre de bloque**
  - Se alcanza un punto estable y probado.
  - Se actualiza:
    - PROJECT.md (si hay cambios estructurales)
    - HISTORY.md (registro del avance).

- 🔴 **ESTADO C — Retomar**
  - Para continuar se utiliza la frase:
    > “Quiero continuar el proyecto MiTienda.  
    > Tengo PROJECT.md y HISTORY.md actualizados.”

### 4.7 Regla de no suposición de estado

- El asistente NO debe asumir:
  - que un archivo existe si no fue mostrado o documentado
  - que un paso está hecho si no figura en HISTORY.md
- Ante duda, se debe **verificar o preguntar**, nunca inferir.

---

## 5. Capa Backend (FastAPI)

### 5.1 Ubicación física

C:\Mitienda\backend

---

### 5.2 Rol del Backend

El backend es la **capa central del sistema** y cumple las siguientes responsabilidades:

- Exponer una API REST consumida por el frontend.
- Implementar toda la lógica de negocio.
- Gestionar la autenticación y autorización (JWT).
- Acceder de forma exclusiva a la base de datos.
- Validar datos de entrada y salida.
- Proteger endpoints y reglas de seguridad.

El backend es la **fuente de la verdad** del sistema.

---

### 5.3 Estructura interna del Backend

backend/
├── main.py
├── create_tables.py
├── .env
│
└── app/
    ├── core/
    │    ├── config.py
    │    ├── database.py
    │    ├── security.py
    │    └── auth.py
    │
    ├── models/
    ├── schemas/
    ├── services/
    └── routers/

---

### 5.4 Estado actual del Backend

- Registro de usuarios
- Login con JWT
- Tokens con expiración
- Endpoint /usuarios/me
- Logout real con revocación de tokens
- Seguridad por dependencias
- Variables de entorno (.env)

Backend considerado **estable**.

---

## 6. Capa Frontend (React)

### 6.1 Ubicación física

C:\Mitienda\frontend

---

### 6.2 Stack tecnológico

- React
- Vite
- TailwindCSS v4
- JavaScript
- Node.js / npm

---

### 6.3 Rol del Frontend

- Renderizar UI
- Navegación entre vistas
- Consumo de API backend
- Manejo del estado de autenticación (JWT)

No contiene lógica de negocio crítica.

---

### 6.4 Estructura actual del Frontend

frontend/
├── src/
│   ├── main.jsx
│   ├── index.css
│   ├── context/
│   ├── layouts/
│   ├── pages/
│   ├── router/
│   └── services/
│
├── public/
├── index.html
├── package.json
├── vite.config.js
└── README.md

---

### 6.5 TailwindCSS

- TailwindCSS v4
- Sin tailwind.config.js
- Importación directa en index.css

---

## 7. Capa Database

### 7.1 Ubicación

C:\Mitienda\database

---

### 7.2 Rol

- Almacenamiento de datos
- Scripts SQL (opcional)
- Backups

Sin lógica de aplicación.

---

## 8. Comunicación entre capas

Frontend → Backend: HTTP + JSON + JWT  
Backend → Database: SQLAlchemy ORM  

---

## 9. Estado actual del proyecto

- Backend estable
- Frontend con auth y navegación base
- Database operativa
- Arquitectura respetada

---

## 10. Punto exacto para continuar

Frontend — PASO 6  
Carga y visualización del usuario autenticado (`/usuarios/me`).

Todo lo previo se considera **estable y documentado**.
