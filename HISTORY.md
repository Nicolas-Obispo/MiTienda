# HISTORY.md — MiTienda

Este documento registra el **histórico paso a paso** del proyecto MiTienda.
Su objetivo es permitir retomar el desarrollo en cualquier momento,
sin perder contexto ni repetir trabajo ya realizado.

El orden de las etapas es cronológico y acumulativo.

---

## Etapa 0 — Definición inicial del proyecto

(Arquitectura, objetivos y reglas base)

---

## Etapa 1 — Backend (FastAPI + JWT)

(Implementación de autenticación y seguridad)

---

## Etapa 2 — Separación por capas

(Separación física de frontend, backend y database)

---

## Etapa 3 — Frontend base

(Creación del frontend y configuración de estilos)

---

## Checkpoint actual

(Punto seguro para continuar el proyecto)

## Etapa 0 — Definición inicial del proyecto

En esta etapa se definieron los objetivos y las reglas base del proyecto:

- El proyecto se estructura por capas: frontend, backend y database.
- Cada capa es independiente y se comunica solo mediante interfaces definidas.
- El backend es la fuente de la verdad.
- Se prioriza la estabilidad y la documentación antes de avanzar.
- Se establece PROJECT.md como fuente única de la verdad.
- Se establece HISTORY.md como registro cronológico del proyecto.

Esta etapa define las reglas que rigen todo el desarrollo posterior.

---

## Etapa 1 — Backend (FastAPI + JWT)

En esta etapa se implementó un backend completo y funcional con FastAPI.

Trabajo realizado:

- Creación del proyecto backend.
- Configuración de entorno virtual.
- Configuración de conexión a base de datos MySQL.
- Implementación de modelos ORM con SQLAlchemy.
- Implementación de registro de usuarios.
- Implementación de login con JWT.
- Configuración de expiración de tokens.
- Implementación del endpoint protegido /usuarios/me.
- Implementación de logout real con revocación de tokens.
- Uso de variables de entorno (.env).
- Pruebas completas en Swagger, curl y navegador.

Resultado:

- Backend completamente funcional.
- Arquitectura por capas respetada.
- Backend considerado estable.

## Etapa 2 — Separación por capas

En esta etapa se realizó la separación física y lógica del proyecto.

Trabajo realizado:

- Separación definitiva de carpetas:
  - frontend
  - backend
  - database
- Verificación de que el backend funciona de forma independiente.
- Verificación de que el frontend no depende del backend.
- Confirmación de que la base de datos es accedida solo por el backend.
- Ajustes de ejecución para iniciar backend y frontend por separado.

Resultado:

- Arquitectura por capas respetada.
- Capas desacopladas entre sí.
- Proyecto organizado para escalar sin romper dependencias.

---

## Etapa 3 — Frontend base (React + TailwindCSS)

En esta etapa se creó y validó el frontend base del proyecto.

Trabajo realizado:

- Creación del frontend con Vite + React.
- Ubicación del frontend fuera del backend.
- Instalación y configuración de TailwindCSS v4.
- Ajuste por cambios de Tailwind v4 (sin tailwind.config.js).
- Validación de estilos en navegador.
- Confirmación de funcionamiento del servidor de desarrollo.

Resultado:

- Frontend operativo y separado del backend.
- Sistema de estilos funcionando correctamente.
- Frontend listo para navegación y conexión con la API.

---

## Checkpoint actual

El proyecto se encuentra en un punto seguro y estable.

Estado actual:

- Backend estable y documentado.
- Frontend base estable y documentado.
- Arquitectura por capas respetada.
- PROJECT.md completo y cerrado.
- HISTORY.md actualizado hasta el estado actual.

Punto exacto para continuar:

Frontend — PASO 3  
Instalar y configurar React Router para navegación entre vistas.

A partir de este checkpoint, cualquier avance debe continuar desde este punto,
sin modificar el trabajo previo.

