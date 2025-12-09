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


## 4. Capa Backend (FastAPI)

### 4.1 Ubicación física

C:\Mitienda\backend

---

### 4.2 Rol del Backend

El backend es la **capa central del sistema** y cumple las siguientes responsabilidades:

- Exponer una API REST consumida por el frontend.
- Implementar toda la lógica de negocio.
- Gestionar la autenticación y autorización (JWT).
- Acceder de forma exclusiva a la base de datos.
- Validar datos de entrada y salida.
- Proteger endpoints y reglas de seguridad.

El backend es la **fuente de la verdad** del sistema.

---

### 4.3 Estructura interna del Backend

backend/
├── main.py                 → Punto de entrada de FastAPI
├── create_tables.py        → Creación inicial de tablas
├── .env                    → Variables de entorno
│
└── app/
    ├── core/               → Infraestructura y seguridad
    │    ├── config.py      → Carga de configuración desde .env
    │    ├── database.py    → Engine, SessionLocal y Base ORM
    │    ├── security.py    → Hash y verificación de contraseñas
    │    └── auth.py        → JWT, usuario actual y logout
    │
    ├── models/             → Modelos ORM (SQLAlchemy)
    ├── schemas/            → Modelos de validación (Pydantic)
    ├── services/           → Lógica de negocio
    └── routers/            → Endpoints HTTP (API REST)

---

### 4.4 Estado actual del Backend

Funcionalidades implementadas y probadas:

- Registro de usuarios
- Login con JWT
- Tokens con expiración
- Endpoint protegido /usuarios/me
- Logout real con revocación de tokens en base de datos
- Protección de rutas mediante dependencias
- Configuración segura por variables de entorno

El backend se considera **estable** y no debe modificarse sin autorización explícita.


## 5. Capa Frontend (React)

### 5.1 Ubicación física

C:\Mitienda\frontend

---

### 5.2 Stack tecnológico del Frontend

- React
- Vite
- TailwindCSS v4
- JavaScript (no TypeScript)
- Node.js / npm

---

### 5.3 Rol del Frontend

El frontend es responsable exclusivamente de:

- Renderizar la interfaz de usuario.
- Gestionar la experiencia del usuario (UI/UX).
- Navegar entre vistas.
- Consumir la API del backend mediante HTTP.
- Manejar el estado del usuario autenticado (token JWT).

El frontend **no contiene lógica de negocio crítica**  
y **no accede directamente a la base de datos**.

---

### 5.4 Estructura actual del Frontend

frontend/
├── src/
│   ├── App.jsx          → Componente raíz de la aplicación
│   ├── main.jsx         → Punto de entrada de React
│   └── index.css        → Estilos globales (TailwindCSS)
│
├── public/
├── index.html
├── package.json
├── vite.config.js
└── README.md

---

### 5.5 Configuración de TailwindCSS

El proyecto utiliza **TailwindCSS v4**.

- No se usa tailwind.config.js por defecto.
- No se usa postcss.config.js por defecto.
- Tailwind se activa mediante importación directa en CSS.

Archivo clave:

src/index.css

Contenido mínimo requerido:

@import "tailwindcss";

---

### 5.6 Estado actual del Frontend

Estado validado:

- Proyecto creado correctamente con Vite.
- Separación física del backend confirmada.
- TailwindCSS v4 funcionando correctamente.
- Renderizado probado en navegador.
- Sin conexión aún al backend (intencional).

El frontend está listo para comenzar la navegación y conexión con la API.


## 6. Capa Database (Base de Datos)

### 6.1 Ubicación física

C:\Mitienda\database

---

### 6.2 Rol de la capa Database

La carpeta database representa la **base de datos física** y su entorno,
no la lógica de acceso ni el ORM.

Sus responsabilidades son:

- Almacenar datos persistentes.
- Contener scripts SQL manuales (opcional).
- Contener backups o dumps de la base de datos.
- Documentación relacionada a la base de datos.

---

### 6.3 Restricciones importantes

- La carpeta database NO contiene código Python.
- La carpeta database NO contiene código JavaScript.
- La carpeta database NO contiene lógica de negocio.
- El acceso a la base de datos se realiza exclusivamente desde el backend.
- SQLAlchemy (ORM) vive en la capa backend, no aquí.

---

### 6.4 Motor de base de datos utilizado

- Motor: MySQL
- Acceso: SQLAlchemy ORM (desde backend)
- Configuración: Variables de entorno (.env)

---

### 6.5 Estado actual de la capa Database

- Base de datos configurada y operativa.
- Tablas creadas mediante SQLAlchemy.
- Integración estable con el backend.

La capa database se considera **estable**.

## 7. Comunicación entre capas

### 7.1 Frontend → Backend

La comunicación entre frontend y backend se realiza exclusivamente mediante
HTTP utilizando una API REST.

Características:

- Protocolo: HTTP
- Formato de datos: JSON
- Autenticación: JWT (Bearer Token)
- Transporte seguro: HTTPS (en producción)

Ejemplos de endpoints:

- POST /usuarios/login
- POST /usuarios/registrar
- GET /usuarios/me
- POST /usuarios/logout

El frontend **nunca accede directamente a la base de datos**.

---

### 7.2 Backend → Database

La comunicación entre backend y base de datos se realiza exclusivamente mediante:

- SQLAlchemy ORM
- Sesiones controladas (SessionLocal)
- Modelos ORM declarativos

Características:

- El backend es el único que conoce la estructura de la base de datos.
- El backend gestiona transacciones, commits y rollbacks.
- La base de datos no conoce al frontend.

---

### 7.3 Restricciones de comunicación

- El frontend NO se comunica con la base de datos.
- La base de datos NO expone endpoints.
- El frontend NO contiene lógica de negocio crítica.
- Toda validación de reglas de negocio vive en el backend.

Estas reglas son obligatorias para mantener la arquitectura por capas.

## 8. Estado actual del proyecto

### 8.1 Componentes validados

Backend:
- API FastAPI operativa.
- Registro y login de usuarios funcionando.
- Autenticación JWT implementada.
- Expiración de tokens configurada.
- Endpoint /usuarios/me funcionando.
- Logout real con revocación de tokens en base de datos.
- Configuración por variables de entorno (.env).
- Arquitectura por capas respetada.
- Backend considerado estable.

Frontend:
- Proyecto React creado con Vite.
- Separación física del backend confirmada.
- TailwindCSS v4 instalado y funcionando.
- Renderizado de estilos validado en navegador.
- Frontend considerado estable para continuar.

Database:
- Base de datos MySQL operativa.
- Tablas creadas mediante SQLAlchemy.
- Acceso exclusivo desde backend.
- Capa database considerada estable.

---

### 8.2 Restricciones actuales

- No modificar el backend sin autorización explícita.
- No cambiar la estructura de carpetas.
- No romper la separación por capas.
- No introducir lógica de negocio en el frontend.
- No acceder a la base de datos fuera del backend.

---

### 8.3 Punto exacto para continuar

El proyecto se encuentra en la siguiente etapa:

Frontend — PASO 3  
Instalar y configurar React Router para navegación entre vistas.

Todo el trabajo previo se considera estable y documentado.
Cualquier avance debe continuar desde este punto.

