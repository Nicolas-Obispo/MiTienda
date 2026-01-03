# NUEVOHISTORY — MiPlaza

Este documento registra el **histórico de decisiones, diseño y evolución**
del proyecto **MiPlaza**, construido sobre la base técnica existente de
**MiTienda**.

Su objetivo es permitir:
- retomar el proyecto desde cualquier momento,
- comprender por qué se tomaron ciertas decisiones,
- y garantizar que no se pierda contexto durante la transición.

El orden de las etapas es **cronológico y acumulativo**.
Cada bloque cerrado representa un punto conceptual estable,
aunque aún no esté implementado en código.

---

## Etapa 0 — Base técnica heredada (MiTienda)

MiPlaza se construye **sobre la base técnica estable del proyecto MiTienda**.

### Estado heredado
- Backend FastAPI funcional y estable.
- Autenticación completa con JWT.
- Logout real con revocación de tokens.
- Arquitectura por capas respetada.
- Frontend React con autenticación y navegación base.
- PROJECT.md y HISTORY.md de MiTienda actualizados y confiables.

📌 **Importante**  
Durante esta etapa:
- No se modifica código existente.
- No se elimina funcionalidad.
- MiTienda se mantiene como fuente técnica estable.

---

## Etapa 1 — Cambio de enfoque del producto (pivot)

En esta etapa se redefine el **fin del producto**, sin romper la base técnica.

### Decisión tomada
- El proyecto deja de apuntar a un marketplace clásico.
- Se redefine como una **plataforma de descubrimiento y publicidad**
  para comercios y servicios.

### Motivación
- Mayor viabilidad como proyecto individual.
- Menor complejidad operativa (sin pagos por venta, sin logística).
- Diferenciación frente a marketplaces existentes.
- Valor real para comercios pequeños y medianos.

📌 El backend existente sigue siendo válido para este nuevo enfoque.

---

## Etapa 2 — Definición de identidad del producto (MiPlaza)

Se define la identidad conceptual del nuevo producto.

### Nombre
- **MiPlaza** (nombre de trabajo, no definitivo).

### Mensaje clave
- “Descubrí negocios y servicios cerca tuyo.”
- “Entrá a pasear, mirá y descubrí.”
- “MiPlaza es tu vidriera digital.”
- “Las personas ya están buscando. Vos decidís si te encuentran o no.”
- Frase de valor:  
  **“Te ponemos clientes en la puerta. Vos hacés el resto.”**

### Posicionamiento
- Producto orientado principalmente al comerciante / prestador de servicios.
- El usuario es central, pero el modelo de negocio se apoya en el publicador.
- MiPlaza no vende: **conecta personas con negocios**.

---

## Etapa 3 — Definición de actores y modos de uso

Se definen los actores principales del sistema:

### Usuario (Consumidor)
- Busca, explora y descubre.
- Interactúa con comercios.
- Contacta por WhatsApp / Maps / redes.

### Publicador (Comerciante / Servicio)
- Representa un negocio real.
- Publica contenido.
- Mide interés y rendimiento.

📌 **Regla clave**  
Existe **una sola cuenta**, con **dos modos de uso**:
- Usuario
- Publicador  
El modo solo cambia permisos y vistas, no la identidad.

---

## Etapa 4 — Definición de principios rectores

Se establecen principios no negociables para MiPlaza:

- Simplicidad de uso.
- Privacidad por defecto.
- Igualdad de herramientas entre comercios.
- IA como apoyo, no como juez.
- Descubrimiento real, no forzado.
- Claridad conceptual antes de implementación técnica.
- Arquitectura adaptable a MiTienda.

Estos principios guían todas las decisiones posteriores.

---

## Etapa 5 — Arquitectura funcional por capas

Se confirma que MiPlaza hereda y respeta la arquitectura por capas de MiTienda.

### Patrón adoptado


### Reglas
- Routers: solo HTTP.
- Services: funciones de negocio puras.
- Models: estructura de datos.
- Schemas: validación.
- Prohibido mezclar responsabilidades.

---

## Etapa 6 — Definición de módulos del sistema

Se definen los módulos conceptuales de MiPlaza:

- Autenticación & Cuenta
- Perfil & Modo
- Comercios
- Rubros
- Secciones del comercio
- Publicaciones
- Historias (contenido temporal)
- Búsqueda con apoyo de IA
- Interacciones
- Métricas & Rendimiento
- Bloqueo & Confianza
- Planes & Monetización

Estos módulos sirven como guía directa para la implementación.

---

## Etapa 7 — Definición de flujos principales

Se definen los flujos de uso del sistema:

### Usuario
Entrar → buscar → explorar → descubrir → contactar

### Publicador
Crear comercio → publicar → medir interés → decidir → mejorar → invertir (opcional)

### Cambio de modo
Usuario ↔ Publicador  
Sin duplicar cuentas ni datos.

---

## Etapa 8 — Definición de entidades y modelo de datos (conceptual)

Se definen las entidades principales del sistema:

- Usuario
- Comercio
- Rubro
- Sección
- Publicación
- Historia
- Interacción
- Métrica
- Bloqueo
- Plan

El modelo de datos queda documentado de forma conceptual
y será transformado en migraciones SQL en etapas posteriores.

---

## Etapa 9 — Reglas heredadas de MiTienda

MiPlaza hereda explícitamente las reglas de trabajo de MiTienda:

- Avance paso a paso.
- Un solo paso por vez.
- No recrear archivos sin confirmación.
- Indicar siempre si un archivo se reemplaza o se modifica.
- Nombres semánticos y consistentes.
- Código comentado.
- No asumir estados no documentados.
- Documentación por bloques (ESTADO A / B / C).

Estas reglas son obligatorias durante todo el desarrollo de MiPlaza.

---

## ✅ Cierre de bloque — Arquitectura y visión MiPlaza

Con esta etapa se considera **cerrado un bloque conceptual completo**:

- Identidad del producto definida.
- Arquitectura funcional definida.
- Módulos definidos.
- Flujos definidos.
- Entidades definidas.
- Estrategia de transición clara.

📌 A partir de este punto:
- No se modifica esta definición sin documentar.
- La implementación debe respetar lo aquí establecido.
- El próximo avance corresponde a migraciones SQL o implementación modular.

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 10 — Definición completa de migraciones SQL (MiPlaza)

En esta etapa se definió **toda la estructura de base de datos necesaria**
para implementar MiPlaza, **sin ejecutar migraciones**, y sin modificar
la base estable de MiTienda.

El objetivo fue:
- diseñar la estructura completa,
- validar relaciones y responsabilidades,
- asegurar compatibilidad con MiTienda,
- y evitar errores antes de escribir código.

---

### Migraciones diseñadas (NO ejecutadas)

Se definieron las siguientes migraciones SQL, todas idempotentes
y compatibles con MySQL 8:

1. **Usuarios**
   - Extensión de la tabla `usuarios`
   - Agregado de:
     - provincia
     - ciudad
     - modo_activo
     - onboarding_completo
     - activo
   - Sin romper autenticación ni JWT existentes.

2. **Rubros**
   - Nueva tabla `rubros`
   - Lista curada y controlada
   - Base de navegación y búsqueda.

3. **Comercios**
   - Nueva tabla `comercios`
   - Entidad central del sistema
   - Relación usuario → comercio
   - Ubicación propia del comercio
   - Portada obligatoria a nivel lógica.

4. **Secciones del comercio**
   - Nueva tabla `secciones_comercio`
   - Organización interna libre por comercio
   - Orden visual configurable.

5. **Publicaciones**
   - Nueva tabla `publicaciones`
   - Evolución conceptual de `productos` (MiTienda)
   - Contenido visual permanente
   - Likes como señal de interés, no red social.

6. **Historias**
   - Nueva tabla `historias`
   - Contenido temporal
   - Likes como feedback rápido
   - Expiración automática.

7. **Interacciones**
   - Nueva tabla `interacciones`
   - Registro anónimo de acciones:
     - likes
     - clicks
     - favoritos
   - Base para métricas, bloqueos y ranking.

8. **Métricas**
   - Nueva tabla `metricas_comercio`
   - Datos agregados mensuales
   - Sin exponer identidades
   - Optimizada para dashboards.

9. **Bloqueos & Confianza**
   - Nueva tabla `bloqueos_usuarios`
   - Bloqueo comercio → usuario
   - Solo permitido con interacción previa
   - Usuario no notificado
   - Sistema auditable.

---

### Estado del sistema tras esta etapa

- Ninguna migración fue ejecutada.
- No se modificó código productivo.
- MiTienda permanece estable.
- MiPlaza cuenta con modelo de datos completo y validado.
- La arquitectura de datos se considera **cerrada como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Definición de módulos backend (services y responsabilidades)**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.

---

## Etapa 11 — Definición de módulos backend (MiPlaza)

En esta etapa se definió la **arquitectura lógica de módulos backend**
del proyecto MiPlaza, respetando la base técnica heredada de MiTienda
y la arquitectura por capas orientada a funciones.

El objetivo fue:
- separar responsabilidades,
- evitar lógica mezclada,
- preparar el terreno para endpoints claros,
- y facilitar la implementación progresiva sin romper estabilidad.

---

### Principio estructural

Todos los módulos backend respetan el patrón:

Router (HTTP) → Service (lógica de negocio) → Model (datos)

Los routers solo orquestan requests y responses.
Toda la lógica vive en services.
Los models representan estructura y persistencia.

---

### Módulos definidos

Se definieron los siguientes módulos backend:

1. **Autenticación & Cuenta**
   - Registro, login, JWT y logout
   - Compatibilidad total con MiTienda

2. **Perfil & Modo**
   - Gestión de modo activo (Usuario / Publicador)
   - Onboarding inicial
   - Validación de permisos por modo

3. **Rubros**
   - Listado de rubros curados
   - Obtención por slug
   - Validación de rubros activos

4. **Comercios**
   - Creación y edición de comercios
   - Perfil público del comercio
   - Validación de ownership

5. **Secciones del comercio**
   - Organización interna del comercio
   - Orden visual y activación

6. **Publicaciones**
   - Gestión de publicaciones permanentes
   - Asociación a secciones
   - Likes como señal de interés

7. **Historias**
   - Contenido temporal
   - Expiración automática
   - Likes como feedback rápido

8. **Interacciones**
   - Registro anónimo de acciones
   - Base para métricas, bloqueos y ranking

9. **Métricas**
   - Agregación mensual
   - Exposición de datos anónimos al publicador

10. **Bloqueo & Confianza**
    - Bloqueo comercio → usuario
    - Validación por interacción previa
    - Sistema auditable

11. **Búsqueda (IA)**
    - Procesamiento de texto libre
    - Filtros por ciudad y rubro
    - Ranking de resultados
    - Integración futura de IA

12. **Planes & Monetización**
    - Gestión de planes
    - Control de visibilidad
    - Integración de pagos (no MVP)

---

### Estado del sistema tras esta etapa

- Los módulos backend quedaron **completamente definidos**.
- No existe solapamiento de responsabilidades.
- La arquitectura es consistente con el modelo de datos.
- No se escribió código ni endpoints aún.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de ENDPOINTS REST (contratos HTTP)**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 12 — Diseño de endpoints REST (Autenticación & Cuenta)

En esta etapa se diseñaron los **contratos HTTP iniciales**
de la API de MiPlaza, correspondientes al módulo de
**Autenticación & Cuenta**.

El objetivo fue:
- definir claramente cómo se comunica el frontend con el backend,
- evitar improvisaciones al escribir código,
- mantener compatibilidad con MiTienda,
- y asegurar un flujo claro para usuarios y publicadores.

---

### Convenciones generales definidas

- Base URL versionada: `/api/v1`
- Autenticación mediante JWT (`Authorization: Bearer <token>`)
- Formato estándar de respuestas:
  - `success: true` con `data`
  - `success: false` con `error`
- Validación de permisos basada en `modo_activo`
- No existen roles duros (admin / seller), solo contexto de uso.

---

### Endpoints diseñados

Se definieron los siguientes endpoints:

1. **POST /api/v1/auth/register**
   - Registro simple de usuario
   - Baja fricción
   - Ubicación no requerida en este paso

2. **POST /api/v1/auth/login**
   - Login con email y contraseña
   - Retorna JWT válido

3. **POST /api/v1/auth/logout**
   - Revocación real de token
   - Uso de tabla `tokens_revocados`

4. **GET /api/v1/usuarios/me**
   - Obtención del perfil del usuario autenticado
   - Retorna modo activo y estado de onboarding

5. **POST /api/v1/usuarios/modo**
   - Cambio de modo activo (Usuario ↔ Publicador)
   - No crea cuentas nuevas

6. **POST /api/v1/usuarios/onboarding**
   - Registro de provincia y ciudad
   - Marca onboarding como completo

---

### Estado del sistema tras esta etapa

- Los endpoints de autenticación y cuenta quedaron
  **definidos a nivel contractual**.
- No se implementó código aún.
- No se modificó la base técnica existente.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de endpoints REST — Rubros y Comercios**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 13 — Diseño de endpoints REST (Rubros y Comercios)

En esta etapa se diseñaron los **endpoints REST correspondientes a los módulos
Rubros y Comercios**, pilares del sistema de descubrimiento de MiPlaza.

El objetivo fue:
- definir contratos HTTP claros,
- separar vistas públicas de acciones privadas,
- establecer permisos por modo de uso,
- y mantener coherencia con la arquitectura heredada de MiTienda.

---

### Endpoints de Rubros

Se definieron endpoints de solo lectura, públicos y curados:

1. **GET /api/v1/rubros**
   - Lista de rubros activos
   - Utilizado en home, navegación y filtros

2. **GET /api/v1/rubros/{slug}**
   - Obtención de rubro por identificador legible
   - Permite URLs limpias y semánticas

Los rubros no pueden ser creados ni modificados por usuarios.

---

### Endpoints de Comercios

Se definieron los endpoints principales del núcleo del sistema:

1. **POST /api/v1/comercios**
   - Creación de comercio
   - Requiere autenticación
   - Requiere modo publicador
   - Imagen de portada obligatoria

2. **GET /api/v1/comercios**
   - Listado público de comercios
   - Soporta filtros por rubro, ciudad y provincia
   - Endpoint base para descubrimiento

3. **GET /api/v1/comercios/{id}**
   - Perfil público del comercio
   - No expone métricas privadas ni datos sensibles

4. **PUT /api/v1/comercios/{id}**
   - Edición de datos del comercio
   - Solo permitido al usuario dueño

5. **POST /api/v1/comercios/{id}/desactivar**
   - Desactivación lógica del comercio
   - No elimina datos (soft delete)

6. **GET /api/v1/mis-comercios**
   - Listado de comercios del publicador autenticado
   - Visible solo en modo publicador

---

### Estado del sistema tras esta etapa

- Los endpoints de Rubros y Comercios quedaron
  **definidos a nivel contractual**.
- No se implementó código aún.
- No se afectó la base técnica de MiTienda.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de endpoints REST — Secciones y Publicaciones**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 14 — Diseño de endpoints REST (Secciones y Publicaciones)

En esta etapa se diseñaron los **endpoints REST correspondientes a los módulos
Secciones del comercio y Publicaciones**, responsables de la organización
y visualización del contenido permanente de cada comercio en MiPlaza.

El objetivo fue:
- permitir a los publicadores organizar su vidriera,
- ofrecer al usuario una exploración clara y ordenada,
- tratar los likes como señal de interés (no red social),
- y mantener coherencia con la arquitectura por capas.

---

### Endpoints de Secciones

Se definieron los siguientes endpoints:

1. **POST /api/v1/comercios/{comercio_id}/secciones**
   - Creación de secciones internas del comercio
   - Requiere autenticación y modo publicador
   - Solo permitido al dueño del comercio

2. **GET /api/v1/comercios/{comercio_id}/secciones**
   - Listado público de secciones activas
   - Usado para organizar el perfil del comercio

3. **PUT /api/v1/secciones/{seccion_id}**
   - Edición de nombre y orden de la sección
   - Restringido al dueño del comercio

4. **POST /api/v1/secciones/{seccion_id}/desactivar**
   - Desactivación lógica de la sección
   - No elimina datos (soft delete)

---

### Endpoints de Publicaciones

Se definieron los siguientes endpoints:

1. **POST /api/v1/secciones/{seccion_id}/publicaciones**
   - Creación de publicaciones
   - Imagen obligatoria
   - Precio opcional

2. **GET /api/v1/secciones/{seccion_id}/publicaciones**
   - Listado público de publicaciones activas
   - Incluye contador de likes como señal de interés

3. **PUT /api/v1/publicaciones/{publicacion_id}**
   - Edición de publicación
   - Restringido al dueño del comercio

4. **POST /api/v1/publicaciones/{publicacion_id}/desactivar**
   - Desactivación lógica de la publicación

5. **POST /api/v1/publicaciones/{publicacion_id}/like**
   - Registro de like como señal de interés
   - No expone identidad del usuario

---

### Estado del sistema tras esta etapa

- Los endpoints de Secciones y Publicaciones quedaron
  **definidos a nivel contractual**.
- No se implementó código aún.
- No se afectó la base técnica de MiTienda.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de endpoints REST — Historias e Interacciones**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 15 — Diseño de endpoints REST (Historias e Interacciones)

En esta etapa se diseñaron los **endpoints REST correspondientes a los módulos
Historias e Interacciones**, orientados a capturar señales de interés,
acciones reales y comportamiento anónimo de los usuarios en MiPlaza.

El objetivo fue:
- permitir a los publicadores medir interés en tiempo real,
- registrar interacciones sin exponer identidades,
- sentar las bases para métricas, ranking y confianza,
- y mantener coherencia con la arquitectura por capas.

---

### Endpoints de Historias

Se definieron los siguientes endpoints:

1. **POST /api/v1/comercios/{comercio_id}/historias**
   - Creación de historias temporales
   - Imagen obligatoria
   - Expiración configurable (horas)

2. **GET /api/v1/comercios/{comercio_id}/historias**
   - Listado público de historias activas
   - Excluye historias expiradas

3. **POST /api/v1/historias/{historia_id}/desactivar**
   - Desactivación manual de historias
   - Restringido al dueño del comercio

4. **POST /api/v1/historias/{historia_id}/like**
   - Registro de like como señal de interés
   - No expone identidad del usuario

---

### Endpoints de Interacciones

Se definieron los siguientes endpoints:

1. **POST /api/v1/interacciones/whatsapp**
   - Registro de click a WhatsApp
   - Base para métricas y bloqueos

2. **POST /api/v1/interacciones/maps**
   - Registro de click a Maps

3. **POST /api/v1/interacciones/favorito**
   - Registro de favorito
   - Señal de interés persistente

4. **POST /api/v1/interacciones/comentario**
   - Registro de comentario
   - Texto moderable
   - Base para anti-toxicidad

---

### Estado del sistema tras esta etapa

- Los endpoints de Historias e Interacciones quedaron
  **definidos a nivel contractual**.
- No se implementó código aún.
- No se afectó la base técnica de MiTienda.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de endpoints REST — Métricas y Bloqueo**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 16 — Diseño de endpoints REST (Métricas y Bloqueo)

En esta etapa se diseñaron los **endpoints REST correspondientes a los módulos
Métricas y Bloqueo & Confianza**, orientados a ofrecer información útil al
publicador sin comprometer la privacidad de los usuarios.

El objetivo fue:
- permitir medir rendimiento real del comercio,
- ofrecer métricas agregadas y anónimas,
- habilitar herramientas de control al publicador,
- y mantener confianza y equilibrio en el ecosistema.

---

### Endpoints de Métricas

Se definieron endpoints privados para el publicador:

1. **GET /api/v1/comercios/{comercio_id}/metricas**
   - Métricas generales mensuales del comercio
   - Visitas, favoritos, clics y apariciones
   - Sin exposición de datos personales

2. **GET /api/v1/comercios/{comercio_id}/metricas/secciones**
   - Métricas por secciones internas
   - Ayuda a decisiones comerciales

3. **GET /api/v1/comercios/{comercio_id}/metricas/score**
   - Score interno de rendimiento
   - Representación visual (barra de nivel)
   - No visible para otros comercios

---

### Endpoints de Bloqueo & Confianza

Se definieron endpoints para control del publicador:

1. **GET /api/v1/comercios/{comercio_id}/interacciones**
   - Listado de interacciones habilitantes para bloqueo
   - No expone identidad de usuarios

2. **POST /api/v1/bloqueos**
   - Creación de bloqueo por interacción
   - Requiere motivo
   - Bloqueo anónimo y auditable

3. **GET /api/v1/comercios/{comercio_id}/bloqueos**
   - Listado de bloqueos del comercio
   - Visible solo para el dueño

4. **POST /api/v1/bloqueos/{bloqueo_id}/desbloquear**
   - Desbloqueo manual
   - No restaura historial previo

---

### Estado del sistema tras esta etapa

- Los endpoints de Métricas y Bloqueo quedaron
  **definidos a nivel contractual**.
- No se implementó código aún.
- No se afectó la base técnica existente.
- El diseño se considera **cerrado como base**.

---

### Próximo bloque habilitado

A partir de este punto, el proyecto puede avanzar a:

👉 **Diseño de endpoints REST — Planes & Monetización**

Estado del proyecto: **ESTADO B — Bloque cerrado y documentado**.


---

## Etapa 17 — Diseño de endpoints REST (Planes y Monetización)

En esta etapa se diseñaron los **endpoints REST correspondientes al módulo
Planes & Monetización**, completando el diseño integral de la API de MiPlaza.

El objetivo fue:
- definir cómo los comercios contratan visibilidad,
- permitir múltiples medios de pago sin complejidad técnica,
- preparar la integración con proveedores de pago,
- y mantener un sistema justo, transparente y escalable.

---

### Modelo conceptual de planes

- Los planes tienen **vigencia temporal**
- En la versión inicial se comercializan como **mensuales**
- La arquitectura **no queda limitada** a una duración fija
- La vigencia se maneja por:
  - `fecha_inicio`
  - `fecha_fin`

Esto permite:
- planes mensuales
- pruebas gratuitas
- promociones
- planes especiales futuros  
sin modificar la base del sistema.

---

### Proveedor de pago vs Medio de pago

Se definió una separación conceptual clara:

- **Proveedor de pago**
  - Ejemplo actual: MercadoPago
  - Responsable del checkout y la confirmación

- **Medios de pago**
  - Tarjeta de crédito
  - Tarjeta de débito
  - Dinero en cuenta
  - Efectivo (PagoFácil / Rapipago)
  - Transferencias

El sistema integra **un proveedor** que ofrece **múltiples medios**,
evitando integraciones duplicadas.

---

### Endpoints de Planes

Se definieron los siguientes endpoints:

1. **GET /api/v1/planes**
   - Listado público de planes disponibles
   - Incluye planes gratuitos y pagos
   - Describe beneficios y vigencia

2. **GET /api/v1/comercios/{comercio_id}/plan**
   - Obtención del plan activo del comercio
   - Incluye estado y período de vigencia

3. **POST /api/v1/comercios/{comercio_id}/planes/checkout**
   - Inicio del proceso de contratación
   - Genera checkout con proveedor de pago
   - No activa el plan aún

4. **POST /api/v1/pagos/webhook**
   - Recepción de confirmaciones del proveedor
   - Valida firma y estado del pago
   - Activa el plan solo cuando el pago es aprobado

5. **GET /api/v1/comercios/{comercio_id}/pagos**
   - Historial de pagos del comercio
   - Visible solo para el dueño

---

### Principios de monetización definidos

- Todos los comercios aparecen en la plataforma
- Los planes **mejoran visibilidad**, no eliminan competencia
- El ranking combina:
  - relevancia
  - cercanía
  - interés
  - plan (con peso limitado)
- El pago no reemplaza calidad ni interés real
- No existe publicidad engañosa

---

### Estado del sistema tras esta etapa

- El diseño de endpoints REST de MiPlaza quedó
  **completamente definido y ajustado**.
- No se escribió código aún.
- No se afectó la estabilidad de MiTienda.
- El diseño se considera **cerrado y validado**.

---

### Diseño de API — COMPLETADO

A partir de este punto:
- Todos los módulos tienen endpoints definidos
- La arquitectura está lista para implementación
- El proyecto puede pasar a fase de desarrollo

Estado del proyecto: **ESTADO B — Diseño de API cerrado**.


## Etapa 18 — Backend: Usuarios / Onboarding (COMPLETADA)
---


En esta etapa se implementó el **primer bloque funcional de MiPlaza**
sobre la base estable de MiTienda, sin romper compatibilidad.

---

### Objetivo de la etapa

Preparar la entidad **Usuario** para el modelo de MiPlaza, incorporando:

- Onboarding inicial (ubicación)
- Estado base del usuario
- Fundamentos para descubrimiento local
- Base para alternar modos Usuario / Publicador

Todo respetando:
- arquitectura por capas
- separación estricta de responsabilidades
- estabilidad del sistema existente

---

### Trabajo realizado

#### 1. Modelo (`usuarios_models.py`)
Se agregaron los siguientes campos:

- `modo_activo` (default: `"usuario"`)
- `onboarding_completo` (boolean)
- `provincia` (nullable)
- `ciudad` (nullable)

Con defaults seguros para no afectar usuarios existentes.

---

#### 2. Base de datos (Migración SQL)
Se aplicó una migración manual en MySQL para reflejar
los nuevos campos en la tabla `usuarios`.

La migración fue validada mediante:
- `SHOW COLUMNS`
- verificación de duplicados
- pruebas posteriores en la API

---

#### 3. Schemas (`usuarios_schemas.py`)
Se amplió `UsuarioResponse` para incluir:

- modo_activo
- onboarding_completo
- provincia
- ciudad

Sin modificar schemas de entrada existentes (`UsuarioCreate`, `UsuarioLogin`).

---

#### 4. Service (`usuarios_services.py`)
Se agregó la función:

- `completar_onboarding_usuario`

Responsabilidades:
- guardar provincia y ciudad
- marcar onboarding como completo
- reutilizar usuario autenticado
- sin tocar autenticación ni tokens

---

#### 5. Router (`usuarios_routers.py`)
Se implementó el endpoint:

- `POST /usuarios/onboarding`

Características:
- protegido por JWT existente
- usa el service de onboarding
- devuelve `UsuarioResponse`
- no expone IDs ni datos sensibles
- mantiene UX simple y segura

---

### Validaciones realizadas

- Backend levanta sin errores
- `/usuarios/me` sigue funcionando
- `/usuarios/onboarding` responde correctamente
- Datos persistidos correctamente en DB
- Compatibilidad total con MiTienda

---

### Decisiones de arquitectura confirmadas

- Un solo token JWT por sesión
- El token no se solicita manualmente al usuario
- El frontend gestiona el token automáticamente
- El backend controla permisos según `modo_activo`
- Cambiar de modo no implica nuevo login

---

### Estado tras esta etapa

- Bloque **Usuarios / Onboarding** cerrado y estable
- Base lista para:
  - cambio de modo
  - creación de comercios
  - búsquedas locales
- Proyecto continúa en **ESTADO B — Bloque cerrado**

---

### Próximo paso sugerido

👉 **Backend — Cambio de modo (usuario ↔ publicador)**  
Permitirá alternar permisos sin crear nuevas cuentas.


---

---

## Etapa 19 — Backend: Cambio de modo Usuario / Publicador (COMPLETADA Y VALIDADA)

En esta etapa se implementó y validó el mecanismo que permite alternar
el modo activo de una cuenta entre Usuario y Publicador, sin crear
nuevos usuarios ni generar nuevos tokens.

Esta funcionalidad es clave para el modelo de MiPlaza, donde una misma
persona puede consumir y publicar desde una única cuenta.

---

### Objetivo de la etapa

- Permitir que una misma cuenta funcione como:
  - Usuario (consumidor)
  - Publicador (comerciante / servicio)
- Mantener una experiencia fluida y sin fricción
- Reutilizar el sistema de autenticación existente
- Confirmar que el cambio de modo funcione en un flujo real end-to-end

---

### Trabajo realizado

#### 1. Service (`usuarios_services.py`)
Se agregó la función:

- `cambiar_modo_usuario`

Responsabilidades:
- Validar modos permitidos (`usuario`, `publicador`)
- Actualizar el campo `modo_activo`
- Persistir cambios en base de datos
- No generar nuevos tokens
- No crear cuentas nuevas

---

#### 2. Schema (`usuarios_schemas.py`)
Se agregó:

- `UsuarioCambioModo`

Usado exclusivamente como payload de entrada
para el endpoint de cambio de modo.

---

#### 3. Router (`usuarios_routers.py`)
Se implementó el endpoint:

- `POST /usuarios/modo`

Características:
- Protegido por JWT existente
- Usa el usuario autenticado
- No genera nuevo token
- Devuelve `UsuarioResponse`
- Maneja errores de validación correctamente

---

### Validaciones realizadas (prueba real)

Se ejecutó una prueba completa y manual del flujo de usuario,
utilizando credenciales reales en entorno local.

Flujo validado:
1. Login de usuario
2. Obtención de perfil (`/usuarios/me`)
3. Onboarding real (provincia y ciudad)
4. Cambio de modo Usuario → Publicador
5. Verificación del estado final con `/usuarios/me`

Resultados:
- Autenticación JWT correcta
- Token único mantenido durante toda la sesión
- Cambio de modo persistido correctamente
- Estado reflejado inmediatamente en el backend
- Ningún error de autorización
- Ninguna regresión detectada

---

### Decisiones de arquitectura confirmadas

- Un solo token JWT por sesión
- El token no se solicita manualmente al usuario
- El frontend gestiona el token automáticamente
- El modo activo controla permisos y vistas
- Cambiar de modo no implica nuevo login
- UX limpia, sin fricción
- Arquitectura lista para módulos de Publicador

---

### Estado tras esta etapa

- Bloque **Cambio de modo** cerrado, estable y validado
- Módulo Usuarios completamente funcional para MiPlaza
- Base lista para:
  - creación de comercios
  - publicaciones
  - historias
  - métricas
- Proyecto continúa en **ESTADO B — Bloque cerrado**


---

## Etapa 20 — Backend: Comercios (COMPLETADA)

En esta etapa se implementó el módulo completo de Comercios, que representa
la unidad principal de descubrimiento en MiPlaza.

El módulo se desarrolló respetando estrictamente la arquitectura por capas
y sin modificar ni romper la base existente de MiTienda.

---

### Objetivo de la etapa

- Introducir la entidad Comercio como negocio o servicio publicable
- Asociar comercios a usuarios en modo Publicador
- Permitir creación, edición, consulta y desactivación
- Dejar el sistema listo para Secciones, Publicaciones y Métricas

---

### Trabajo realizado

#### 1. Modelo (`comercios_models.py`)
Se creó la entidad `Comercio` con:
- Relación con `usuarios`
- Datos principales (nombre, descripción, portada)
- Ubicación (provincia, ciudad, dirección)
- Contacto (WhatsApp, Instagram, Maps)
- Estado (`activo`)
- Timestamps (`created_at`, `updated_at`)

Entidad independiente de `Producto`, sin lógica de ventas ni stock.

---

#### 2. Migración SQL
Se creó la tabla `comercios` en MySQL con:
- Clave primaria
- Clave foránea a `usuarios`
- Índices por usuario, rubro y ciudad
- Soft delete mediante campo `activo`
- Integridad referencial protegida

---

#### 3. Schemas (`comercios_schemas.py`)
Se implementaron schemas Pydantic para:
- Creación
- Actualización
- Respuesta

Separación clara entre entrada, actualización parcial y salida.

---

#### 4. Services (`comercios_services.py`)
Se implementó la lógica de negocio:
- Crear comercio (solo modo publicador)
- Listar comercios activos
- Obtener comercio por ID
- Actualizar comercio (solo dueño)
- Desactivar comercio (soft delete)

Sin manejo de HTTP ni JWT.

---

#### 5. Routers (`comercios_routers.py`)
Se expusieron endpoints REST:
- `POST   /comercios`
- `GET    /comercios`
- `GET    /comercios/{id}`
- `PUT    /comercios/{id}`
- `DELETE /comercios/{id}`

Protegidos con JWT existente y validados en Swagger.

---

### Validaciones realizadas

- Backend levanta correctamente
- Endpoints visibles en Swagger
- Separación por capas respetada
- No se rompe funcionalidad existente
- MiTienda permanece intacto

---

### Decisiones de arquitectura confirmadas

- Comercios es una entidad nueva (no reutiliza productos)
- MiPlaza y MiTienda conviven en el mismo backend
- Soft delete en lugar de borrado físico
- Base lista para módulos dependientes

---

### Estado tras esta etapa

- Módulo Comercios cerrado y estable
- Proyecto en **ESTADO B — Bloque cerrado**
- Sistema listo para:
  - Rubros
  - Secciones
  - Publicaciones

## Etapa 21 — Backend: Rubros (COMPLETADA)

En esta etapa se implementó el módulo base de Rubros, que define
la clasificación principal de comercios dentro de MiPlaza.

---

### Objetivo de la etapa

- Crear una clasificación controlada y curada de rubros
- Evitar categorías libres que generen ruido
- Preparar la base para búsqueda, filtrado y ranking

---

### Trabajo realizado

#### 1. Modelo (`rubros_models.py`)
- Definición del modelo `Rubro`
- Campos:
  - `id`
  - `nombre` (único)
  - `descripcion`
  - `activo`

#### 2. Base de datos
- Creación de la tabla `rubros`
- Verificación de existencia y estructura
- Índice de unicidad sobre `nombre`

#### 3. Schemas (`rubros_schemas.py`)
- Schema de lectura
- Schema de creación (preparado para admin)
- Respuesta serializable para API

#### 4. Services (`rubros_services.py`)
- Lógica pura desacoplada de HTTP
- Funciones para:
  - listar rubros activos
  - obtener rubro por id

#### 5. Routers (`rubros_routers.py`)
- Endpoints visibles y operativos en Swagger
- Arquitectura por capas respetada
- Sin lógica de negocio en rutas

---

### Validaciones realizadas

- Tabla `rubros` creada correctamente
- Endpoints visibles en `/docs`
- Backend inicia sin errores
- Arquitectura MiTienda respetada

---

### Decisiones de arquitectura confirmadas

- Rubros son **curados**, no creados por usuarios
- Son base para:
  - comercios
  - búsqueda
  - ranking
- El módulo es reutilizable y extensible

---

### Pendientes técnicos registrados

- Migración futura de schemas a **Pydantic v2**
  - Reemplazar `orm_mode` por `from_attributes`
  - Se hará en un bloque exclusivo y documentado

---

### Estado tras esta etapa

- Módulo Rubros cerrado y estable
- Proyecto continúa en **ESTADO B — Bloque cerrado**
- Próxima etapa: **ETAPA 22 — Secciones**


## Etapa 22 — Backend: Secciones (COMPLETADA)

En esta etapa se implementó el módulo de **Secciones**, que permite a cada
comercio organizar sus publicaciones internas de forma ordenada y configurable.

---

### Objetivo de la etapa

- Permitir a los comercios organizar su contenido
- Facilitar la exploración dentro del perfil del comercio
- Preparar la base para publicaciones, métricas y búsqueda

---

### Trabajo realizado

#### 1. Modelo (`secciones_models.py`)
- Creación del modelo `Seccion`
- Relación exclusiva con `Comercio`
- Campos:
  - `nombre`
  - `descripcion`
  - `orden`
  - `activo`
- Inclusión de timestamps:
  - `created_at`
  - `updated_at`

---

#### 2. Base de datos
- Creación de la tabla `secciones`
- Clave foránea `comercio_id → comercios.id`
- Índices por comercio y estado
- Verificación manual de estructura

---

#### 3. Schemas (`secciones_schemas.py`)
- `SeccionCreate`
- `SeccionUpdate`
- `SeccionResponse`
- Compatibles con arquitectura actual
- Pendiente futura migración a Pydantic v2

---

#### 4. Services (`secciones_services.py`)
- Lógica pura desacoplada de HTTP
- Funciones implementadas:
  - crear sección
  - listar secciones por comercio
  - obtener sección por id
  - actualizar sección

---

#### 5. Routers (`secciones_routers.py`)
- Endpoints implementados:
  - `POST /secciones`
  - `GET /secciones/comercio/{comercio_id}`
  - `PUT /secciones/{seccion_id}`
- Separación estricta de responsabilidades
- Protección por autenticación donde corresponde

---

#### 6. Integración en `main.py`
- Router de Secciones registrado correctamente
- Swagger muestra endpoints sin errores
- Backend levanta sin fallos

---

### Validaciones realizadas

- Tabla `secciones` creada y verificada
- Endpoints visibles en Swagger
- Arquitectura por capas respetada
- No se rompió funcionalidad existente

---

### Estado tras esta etapa

- Módulo **Secciones cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para implementar **Publicaciones**

## Mini-bloque — Normalización de imports de Routers (COMPLETADO)

Se realizó un bloque corto de limpieza para mejorar la consistencia del código.

---

### Objetivo

- Unificar el patrón de imports de routers
- Mejorar prolijidad y mantenibilidad
- Eliminar inconsistencias de estilo

---

### Trabajo realizado

- Normalización del import del router de Rubros:
  - Se adoptó el patrón:
    `from app.routers.xxx_routers import router as xxx_router`
- Ajuste correspondiente en `app.include_router(...)`

---

### Resultado

- Código más consistente y legible
- No se modificó lógica, DB ni endpoints
- Swagger y backend continúan funcionando correctamente

---

### Regla reafirmada

> El código no solo debe funcionar,  
> debe estar bien construido, consistente y prolijo.


## Etapa 23 — Backend: Publicaciones (COMPLETADA)

En esta etapa se implementó el módulo de **Publicaciones**, que permite a los
comercios crear y gestionar contenido publicitario dentro de la plataforma,
sirviendo como eje central del sistema de descubrimiento de MiPlaza.

---

### Objetivo de la etapa

- Permitir a los comercios publicar contenido visible a usuarios
- Asociar publicaciones a comercios y opcionalmente a secciones
- Establecer la base para métricas, likes como señal e historias
- Mantener la separación estricta por capas

---

### Trabajo realizado

#### 1. Modelo (`publicaciones_models.py`)
- Creación del modelo `Publicacion`
- Relación obligatoria con `Comercio`
- Relación opcional con `Seccion`
- Campos implementados:
  - `titulo`
  - `descripcion`
  - `is_activa`
- Inclusión de timestamps:
  - `created_at`
  - `updated_at`
- Definición de relaciones ORM con carga `selectin`

---

#### 2. Relaciones ORM
- Se agregó la relación:
  - `Comercio.publicaciones`
  - `Seccion.publicaciones`
- Configuración de `cascade` correcta:
  - Eliminación en cascada desde Comercio
  - Publicaciones independientes de Sección
- Sin romper modelos existentes

---

#### 3. Schemas (`publicaciones_schemas.py`)
- Creación de schemas Pydantic:
  - `PublicacionBase`
  - `PublicacionCreate`
  - `PublicacionRead`
- Separación clara entre input y output
- Uso de `orm_mode`
- Compatibles con arquitectura actual
- Pendiente futura migración a Pydantic v2

---

#### 4. Services (`publicaciones_services.py`)
- Implementación de lógica de negocio desacoplada de HTTP
- Funciones implementadas:
  - crear publicación
  - listar publicaciones por comercio
- Uso explícito de sesión de base de datos
- Sin validaciones de permisos en esta etapa

---

#### 5. Routers (`publicaciones_routers.py`)
- Endpoints implementados:
  - `POST /publicaciones/comercios/{comercio_id}`
  - `GET /publicaciones/comercios/{comercio_id}`
- Uso exclusivo de services
- Respuestas tipadas con schemas
- Swagger compatible sin errores

---

#### 6. Integración en `main.py`
- Router de Publicaciones registrado correctamente
- Endpoints visibles en Swagger
- Backend levanta sin fallos
- Arquitectura por capas respetada

---

### Validaciones realizadas

- Modelo `publicaciones` creado correctamente
- Relaciones ORM funcionales
- Endpoints visibles y tipados en Swagger
- No se rompió funcionalidad existente
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Publicaciones cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para implementar:
  - **Historias**
  - **Likes como señal de interés**
  - Métricas y visibilidad


## Etapa 24 — Backend: Historias (COMPLETADA)

En esta etapa se implementó el módulo de **Historias**, que permite a los
comercios publicar contenido efímero visible por tiempo limitado, reforzando
el sistema de descubrimiento sin componentes sociales.

---

### Objetivo de la etapa

- Incorporar contenido efímero para comercios
- Controlar visibilidad mediante expiración
- Asociar historias a publicaciones de forma opcional
- Mantener arquitectura por capas estricta

---

### Trabajo realizado

#### 1. Modelo (`historias_models.py`)
- Creación del modelo `Historia`
- Relación obligatoria con `Comercio`
- Relación opcional con `Publicacion`
- Campos implementados:
  - `media_url`
  - `expira_en`
  - `is_activa`
- Inclusión de timestamps:
  - `created_at`
  - `updated_at`

---

#### 2. Relaciones ORM
- Se agregó la relación:
  - `Comercio.historias`
  - `Publicacion.historias`
- Eliminación en cascada desde Comercio
- Asociación opcional a Publicaciones
- Sin romper modelos existentes

---

#### 3. Schemas (`historias_schemas.py`)
- Creación de schemas Pydantic:
  - `HistoriaBase`
  - `HistoriaCreate`
  - `HistoriaRead`
- Separación clara entre input y output
- Uso de `orm_mode`
- Compatibles con arquitectura actual
- Pendiente futura migración a Pydantic v2

---

#### 4. Services (`historias_services.py`)
- Implementación de lógica de negocio desacoplada de HTTP
- Funciones implementadas:
  - crear historia
  - listar historias activas por comercio
- Filtro por expiración aplicado
- Sin validaciones de permisos en esta etapa

---

#### 5. Routers (`historias_routers.py`)
- Endpoints implementados:
  - `POST /historias/comercios/{comercio_id}`
  - `GET /historias/comercios/{comercio_id}`
- Uso exclusivo de services
- Respuestas tipadas con schemas
- Swagger compatible sin errores

---

#### 6. Integración en `main.py`
- Router de Historias registrado correctamente
- Endpoints visibles en Swagger
- Backend levanta sin fallos
- Arquitectura por capas respetada

---

### Validaciones realizadas

- Modelo `historias` creado correctamente
- Expiración funcionando según reglas
- Endpoints visibles y tipados en Swagger
- No se rompió funcionalidad existente
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Historias cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para implementar:
  - **Likes como señal de interés**
  - Métricas y ranking
  - Visibilidad avanzada


## Etapa 25 — Backend: Likes como señal de interés (COMPLETADA)

En esta etapa se implementó el sistema de **Likes** como señal de interés sobre
publicaciones, diseñado como un mecanismo no social, orientado a métricas,
ranking y visibilidad dentro de MiPlaza.

---

### Objetivo de la etapa

- Incorporar una señal de interés no social
- Permitir identificar publicaciones relevantes
- Evitar fraude o inflación artificial de métricas
- Preparar la base para ranking y recomendaciones

---

### Trabajo realizado

#### 1. Modelo (`likes_publicaciones_models.py`)
- Creación del modelo `LikePublicacion`
- Relación entre:
  - `Usuario`
  - `Publicacion`
- Implementación de constraint único:
  - un like por usuario y publicación
- Inclusión de timestamp `created_at`

---

#### 2. Relaciones ORM
- Se agregaron relaciones:
  - `Usuario.likes_publicaciones`
  - `Publicacion.likes`
- Eliminación en cascada configurada correctamente
- Consistencia con modelos existentes

---

#### 3. Schemas (`likes_publicaciones_schemas.py`)
- Creación de schemas Pydantic:
  - `LikePublicacionCreate`
  - `LikePublicacionRead`
- Input mínimo sin exposición de IDs sensibles
- Uso de `orm_mode`
- Pendiente futura migración a Pydantic v2

---

#### 4. Services (`likes_publicaciones_services.py`)
- Implementación de lógica de negocio desacoplada de HTTP
- Función principal:
  - toggle like (crear / eliminar)
- Uso del constraint único como respaldo de integridad

---

#### 5. Routers (`likes_publicaciones_routers.py`)
- Endpoint implementado:
  - `POST /likes/publicaciones/{publicacion_id}`
- Requiere usuario autenticado
- Respuesta clara indicando estado del like
- Swagger compatible sin errores

---

#### 6. Integración en `main.py`
- Router de Likes registrado correctamente
- Endpoints visibles en Swagger
- Backend levanta sin fallos
- Arquitectura por capas respetada

---

### Validaciones realizadas

- Like único garantizado por base de datos
- Toggle funcionando correctamente
- Endpoints protegidos por autenticación
- No se rompió funcionalidad existente
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Likes cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - ranking de publicaciones
  - visibilidad inteligente
  - métricas y recomendaciones


## Etapa 26 — Backend: Ranking y Visibilidad de Publicaciones (COMPLETADA)

En esta etapa se implementó el sistema de **ranking de publicaciones**, orientado
a ordenar el contenido según señales de interés y recencia, manteniendo a
MiPlaza como una plataforma de descubrimiento no social.

---

### Objetivo de la etapa

- Ordenar publicaciones por relevancia
- Priorizar contenido con interés real (likes)
- Evitar que publicaciones nuevas queden invisibles
- Preparar la base para feeds inteligentes

---

### Trabajo realizado

#### 1. Definición de criterio de ranking
- Ranking basado en **score compuesto**
- Fórmula conceptual:
  - `score = likes + bonus_recencia`
- Bonus por recencia:
  - +3 → creada hoy
  - +2 → ≤ 3 días
  - +1 → ≤ 7 días
  - +0 → más antigua
- Solo se consideran publicaciones activas

---

#### 2. Service de Ranking (`ranking_publicaciones_services.py`)
- Implementación de lógica de ranking desacoplada de HTTP
- Uso de:
  - conteo real de likes
  - bonus dinámico por recencia
- Ordenamiento por:
  - score descendente
  - fecha de creación
- Sin modificar services existentes

---

#### 3. Router de Ranking (`ranking_publicaciones_routers.py`)
- Endpoint implementado:
  - `GET /ranking/publicaciones`
- Endpoint de solo lectura
- Usa exclusivamente el service de ranking
- No interfiere con otros listados

---

#### 4. Integración en `main.py`
- Router de ranking registrado correctamente
- Endpoint visible en Swagger
- Backend levanta sin fallos
- Arquitectura por capas respetada

---

### Validaciones realizadas

- Ranking devuelve publicaciones ordenadas correctamente
- Likes influyen en el orden
- Publicaciones nuevas reciben empuje inicial
- No se rompió funcionalidad existente
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Ranking / Visibilidad cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - feeds personalizados
  - métricas avanzadas
  - visibilidad por zona / rubro


## Etapa 27 — Backend: Métricas básicas (COMPLETADA)

En esta etapa se incorporaron **métricas básicas** para publicaciones y
comercios, con foco en visibilidad e interés, manteniendo simplicidad y
dejando abierta la evolución hacia análisis históricos.

---

### Objetivo de la etapa

- Medir alcance e interés de publicaciones
- Incorporar vistas como métrica básica
- Mantener likes como señal de interés
- Evitar complejidad prematura en analytics

---

### Trabajo realizado

#### 1. Modelo (`publicaciones_models.py`)
- Se agregó el campo:
  - `views_count`
- Tipo entero, default 0
- Métrica acumulativa simple
- No se implementa historial en esta etapa

---

#### 2. Services (`publicaciones_services.py`)
- Se agregó la función:
  - `obtener_publicacion_por_id_y_sumar_view`
- Incrementa `views_count` únicamente al consultar el detalle
- No afecta listados ni ranking
- Lógica desacoplada de HTTP

---

#### 3. Routers (`publicaciones_routers.py`)
- Se agregó endpoint:
  - `GET /publicaciones/{publicacion_id}`
- Devuelve detalle de publicación
- Incrementa contador de vistas por request
- Manejo correcto de publicación inexistente

---

### Validaciones realizadas

- `views_count` incrementa solo en endpoint de detalle
- Listados no modifican métricas
- Likes continúan funcionando correctamente
- Ranking no se ve afectado
- No se rompió funcionalidad existente

---

### Estado tras esta etapa

- Módulo **Métricas básicas cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - métricas históricas futuras
  - dashboards para publicadores
  - análisis de crecimiento


## Etapa 28 — Backend: Feed personalizado de Publicaciones (COMPLETADA)

En esta etapa se implementó el **Feed personalizado de publicaciones**, orientado
al descubrimiento de contenido relevante para cada usuario, reutilizando el
ranking existente y respetando el diseño no social de MiPlaza.

---

### Objetivo de la etapa

- Proveer un feed ordenado de publicaciones
- Reutilizar ranking por likes + recencia
- Indicar si el usuario actual dio like (`liked_by_me`)
- Mantener separación estricta entre HTTP y lógica de negocio

---

### Trabajo realizado

#### 1. Service de Feed (`feed_publicaciones_services.py`)
- Creación del service dedicado al feed
- Reutiliza:
  - ranking por likes + recencia
  - conteo de likes
- Cálculo de:
  - `liked_by_me` según usuario autenticado
- Solo devuelve publicaciones activas
- Preparado para futuros filtros (rubro, ubicación)

---

#### 2. Router de Feed (`feed_publicaciones_routers.py`)
- Endpoint implementado:
  - `GET /feed/publicaciones`
- Requiere usuario autenticado
- Endpoint de solo lectura
- No interfiere con otros listados existentes

---

#### 3. Integración en `main.py`
- Router del feed registrado correctamente
- Endpoint visible en Swagger
- Backend levanta sin fallos
- Arquitectura por capas respetada

---

### Validaciones realizadas

- Feed devuelve publicaciones ordenadas correctamente
- `liked_by_me` refleja el estado real del usuario
- Likes y ranking continúan funcionando
- No se rompió funcionalidad existente
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Feed personalizado cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - filtros por rubro y ubicación
  - feeds más inteligentes
  - evolución futura del descubrimiento


## Etapa 29 — Backend: Publicaciones Guardadas / Favoritos (COMPLETADA)

En esta etapa se implementó la funcionalidad de **publicaciones guardadas por usuario**,
orientada al uso personal (guardar para ver más tarde), manteniendo el diseño
**no social** de MiPlaza y sin impacto en ranking ni feed principal.

---

### Objetivo de la etapa

- Permitir que un usuario guarde publicaciones
- Mantener el guardado como acción privada
- No interferir con likes, ranking ni feed
- Respetar estrictamente la arquitectura por capas

---

### Trabajo realizado

#### 1. Model de Publicaciones Guardadas (`publicaciones_guardadas_models.py`)
- Creación de tabla intermedia usuario ↔ publicación
- Campos:
  - usuario_id
  - publicacion_id
  - created_at
- Constraint único:
  - un usuario no puede guardar la misma publicación dos veces
- Eliminación en cascada ante borrado de usuario o publicación

---

#### 2. Schemas (`publicaciones_guardadas_schemas.py`)
- Schema de creación (`PublicacionGuardadaCreate`)
- Schema de respuesta
- Schema de listado
- Sin lógica de negocio
- Preparados para futura ampliación

---

#### 3. Service (`publicaciones_guardadas_services.py`)
- Lógica centralizada:
  - guardar publicación
  - evitar duplicados
  - quitar guardado
  - listar guardados del usuario
- Validación de existencia de publicación
- Manejo de errores de integridad
- Sin dependencias HTTP

---

#### 4. Router (`publicaciones_guardadas_routers.py`)
- Endpoints implementados:
  - `POST /publicaciones/guardadas`
  - `GET /publicaciones/guardadas`
  - `DELETE /publicaciones/guardadas/{publicacion_id}`
- Requiere usuario autenticado
- Uso de auth existente (`obtener_usuario_actual`)
- Router liviano, delega toda la lógica al service

---

#### 5. Integración y limpieza
- Model integrado en `create_tables.py`
- Router registrado en `main.py`
- Eliminación de archivo duplicado `app/create_tables.py`
- Backend levanta correctamente
- Tabla creada sin errores

---

### Validaciones realizadas

- Un usuario puede guardar una publicación válida
- No se permiten duplicados
- El listado devuelve solo publicaciones del usuario
- El borrado funciona correctamente
- Likes, ranking y feed no se vieron afectados
- Arquitectura por capas respetada
- Código consistente con módulos previos

---

### Estado tras esta etapa

- Módulo **Publicaciones Guardadas cerrado y estable**
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - métricas de guardados
  - mejoras de descubrimiento
  - features de organización personal


## Etapa 30 — Backend: Métricas avanzadas de interacción (COMPLETADA)

En esta etapa se incorporaron métricas avanzadas de interacción para publicaciones,
con el objetivo de enriquecer el análisis de contenido y preparar el sistema para
rankings y descubrimiento más inteligentes, sin modificar el diseño no social de MiPlaza.

---

### Objetivo de la etapa

- Incorporar métricas de interacción adicionales
- Reutilizar datos existentes (likes y guardados)
- No agregar columnas ni tablas nuevas
- No romper ranking, feed ni endpoints existentes

---

### Trabajo realizado

#### 1. Helpers de métricas en `publicaciones_services.py`
- Se agregaron funciones reutilizables:
  - `obtener_guardados_count`
  - `obtener_interacciones_count`
- Métricas calculadas on-the-fly
- Sin persistencia en base de datos
- Sin modificar firmas existentes

---

#### 2. Ampliación de schemas (`PublicacionRead`)
- Nuevos campos:
  - `guardados_count`
  - `interacciones_count`
- Valores por defecto seguros (`0`)
- Backwards compatible
- Preparado para futura migración a Pydantic v2

---

#### 3. Integración en Feed personalizado
- Reutilización de helpers de métricas
- Feed mantiene ranking por likes + recencia
- No se rompe `liked_by_me`
- Métricas inyectadas en runtime

---

#### 4. Correcciones de ORM y consistencia
- Relaciones bidireccionales completas:
  - Usuario ↔ PublicacionGuardada
  - Publicacion ↔ PublicacionGuardada
- Resolución de error de mapper SQLAlchemy
- Login y auth funcionando correctamente

---

### Validaciones realizadas

- Login exitoso
- Feed operativo
- Métricas visibles en respuestas:
  - `guardados_count`
  - `interacciones_count`
- Guardados impactan correctamente en métricas
- Ranking y likes continúan funcionando
- Backend estable

---

### Estado tras esta etapa

- Módulo de métricas avanzado cerrado y estable
- Proyecto en **ESTADO B — Bloque cerrado**
- Base lista para:
  - ranking avanzado
  - métricas por comercio / rubro
  - dashboards futuros


## 🟢 ETAPA 31 — Feed personalizado, Guardados, Likes, Ranking e Historias (BACKEND)

### 📌 Objetivo de la etapa
Cerrar y validar completamente la lógica social del backend de **MiPlaza**, asegurando que:
- El feed funcione correctamente
- Guardados y likes se comporten de forma consistente
- El ranking refleje interacciones reales
- Las historias funcionen como contenido efímero por comercio
- Todo quede estable y listo para consumo desde frontend

---

## ✅ Funcionalidades implementadas y verificadas

### 1️⃣ Autenticación y contexto de usuario
- Login funcional con JWT
- Todos los endpoints sociales dependen del usuario autenticado
- Se verificó funcionamiento con **múltiples usuarios distintos**
- Cada acción (guardar, like) queda correctamente asociada al usuario

---

### 2️⃣ Publicaciones
- Creación de publicaciones por comercio
- Campos verificados:
  - `titulo`
  - `descripcion`
  - `is_activa`
  - timestamps automáticos
- Publicaciones activas visibles en feed y ranking

---

### 3️⃣ Guardado de publicaciones
**Endpoints**
- `POST /publicaciones/guardadas`
- `GET /publicaciones/guardadas`
- `DELETE /publicaciones/guardadas/{publicacion_id}`

**Comportamiento validado**
- Un usuario puede guardar una publicación
- El mismo usuario **no puede guardar dos veces la misma publicación**
  - Devuelve `400 Bad Request` → `"La publicación ya está guardada"`
- Distintos usuarios pueden guardar la misma publicación
- Al borrar un guardado:
  - `204 No Content`
  - Se actualizan correctamente los contadores

**Impacto en métricas**
- `guardados_count` se incrementa/decrementa correctamente
- `interacciones_count` refleja la suma de interacciones

---

### 4️⃣ Likes en publicaciones
**Endpoint**
- `POST /likes/publicaciones/{publicacion_id}` (toggle)

**Comportamiento validado**
- Like funciona como toggle:
  - Primera llamada → `liked: true`
  - Segunda llamada → `liked: false`
- El estado es **por usuario**
- Likes afectan métricas globales

**Impacto en métricas**
- `likes_count` se actualiza correctamente
- `interacciones_count` se incrementa/decrementa en consecuencia
- `liked_by_me` refleja correctamente el estado del usuario actual

---

### 5️⃣ Feed personalizado
**Endpoint**
- `GET /feed/publicaciones`

**Características**
- Devuelve publicaciones ordenadas por score (ranking)
- Incluye métricas calculadas:
  - `guardados_count`
  - `interacciones_count`
  - `likes_count`
  - `liked_by_me`
- El feed cambia dinámicamente según:
  - Usuario autenticado
  - Likes y guardados realizados

**Estado**
- Funciona correctamente
- Sin errores SQL
- Datos consistentes entre requests

---

### 6️⃣ Ranking de publicaciones
**Endpoint**
- `GET /ranking/publicaciones`

**Lógica del ranking**
- Basado en:
  - Cantidad de interacciones (guardados + likes)
  - Orden secundario por fecha de creación
- Solo publicaciones activas

**Validaciones realizadas**
- Ranking se reordena al:
  - Guardar/desguardar publicaciones
  - Agregar/quitar likes
- Cambios hechos por distintos usuarios impactan el ranking global
- Se verificó que:
  - Dos usuarios guardando la misma publicación suman correctamente
  - Al quitar un guardado, la publicación baja en ranking

---

### 7️⃣ Historias por comercio
**Endpoints**
- `POST /historias/comercios/{comercio_id}`
- `GET /historias/comercios/{comercio_id}`

**Campos requeridos**
- `media_url`
- `expira_en`
- `is_activa`

**Validaciones**
- Error 422 cuando faltan campos obligatorios
- Creación exitosa con datos completos
- Listado correcto por comercio
- Historias asociadas correctamente al comercio
- Preparado para lógica de expiración futura

---

## 🧠 Decisiones técnicas importantes
- Likes y guardados son **interacciones, no contenido social**
- No hay comentarios (postergado para etapa futura)
- El feed y ranking reutilizan lógica común
- Las métricas son calculadas (no duplicadas innecesariamente)
- Arquitectura respetada:
  - Routers → HTTP
  - Services → lógica de negocio
  - Models → persistencia
  - Schemas → serialización

---

## 🟢 Estado final de la etapa
- ✅ Feed estable
- ✅ Guardados correctos
- ✅ Likes correctos
- ✅ Ranking coherente y dinámico
- ✅ Historias funcionando
- ✅ Probado con múltiples usuarios
- ✅ Backend listo para integración frontend

---

## ➡️ Próximo paso (ETAPA 32)
Integración frontend del feed:
- Consumo de `/feed/publicaciones`
- Render dinámico
- Estados de liked/guardado
- Preparación UI para historias


## 🟢 ETAPA 32 — Integración Frontend: Feed, Autenticación y UI App-like

### 📌 Objetivo de la etapa
Integrar el **frontend** con el backend ya estable (ETAPA 31), asegurando que:
- El feed pueda consumirse correctamente desde la UI
- El usuario pueda autenticarse desde el frontend sin pasos manuales
- La interfaz tenga un diseño consistente y nivel “app”
- No se modifique ninguna lógica existente del backend

---

## ✅ Funcionalidades implementadas y verificadas

### 1️⃣ Infraestructura base del frontend
- Se confirmó que el entrypoint real del frontend es `src/main.jsx`
- La aplicación se monta utilizando:
  - `AuthProvider`
  - `AppRouter`
- Se respetó la arquitectura existente:
  - `pages`
  - `layouts`
  - `services`
  - `context`
- No se recreó ni duplicó ninguna estructura existente

---

### 2️⃣ Configuración de Tailwind CSS (v4)
- Se detectó que Tailwind no estaba aplicando estilos
- Se corrigió la infraestructura necesaria:
  - Creación de `postcss.config.js`
  - Instalación y configuración correcta de `@tailwindcss/postcss`
  - Uso de `@import "tailwindcss";` en `src/index.css`
- Se verificó que Tailwind aplique correctamente en:
  - `/`
  - `/login`
  - `/feed`

---

### 3️⃣ Consumo del Feed desde el frontend
- Se creó una capa de servicios HTTP:
  - `http_service.js` para requests autenticados
  - `feed_service.js` para consumir `/feed/publicaciones`
- El frontend envía correctamente:
  - `Authorization: Bearer <token>`
- Se integró el endpoint:
  - `GET /feed/publicaciones`
- Se renderizan correctamente los datos:
  - `titulo`
  - `descripcion`
  - `likes_count`
  - `guardados_count`
  - `liked_by_me`
- Se manejan correctamente los estados:
  - Loading
  - Error (401 / token inválido o expirado)
  - Empty
  - OK

---

### 4️⃣ Feed UI (nivel app)
- Se implementó un feed visualmente consistente:
  - Cards con jerarquía tipográfica clara
  - Badges métricos (Likes, Guardados, Liked)
  - Layout centrado (`max-w-3xl`)
- Se evitó duplicación de headers:
  - El feed utiliza únicamente el header global del layout
- El diseño respeta la filosofía de MiPlaza:
  - Descubrimiento de contenido
  - No red social

---

### 5️⃣ Home Page
- Se refactorizó la página de inicio:
  - Fondo oscuro
  - Card central
  - Call-to-Action hacia el Feed
- Se unificó el look & feel con el resto del frontend

---

### 6️⃣ MainLayout (barra superior global)
- Se eliminaron estilos inline
- Se implementó una barra superior app-like con Tailwind:
  - Navegación: Inicio / Feed / Login
  - Header sticky con blur
- Se agregó indicador visual de estado de sesión:
  - “Sesión activa”
  - “No autenticado”
- Se mantuvo intacta la lógica existente de:
  - `AuthContext`
  - `logout`

---

### 7️⃣ Login desde frontend (UX completo)
- Se refactorizó `Login.jsx`:
  - UI con Tailwind
  - Card centrada
  - Inputs y mensajes de error claros
- Flujo verificado:
  - Login → `/usuarios/login`
  - Token gestionado por `AuthContext`
  - Redirección automática a `/feed`
- Ya no es necesario pegar tokens manualmente en consola

---

## 🧪 Pruebas realizadas y confirmadas

- `npm run dev` ejecuta sin errores
- `/` renderiza correctamente (Home)
- `/login`:
  - Permite autenticarse
  - Redirige automáticamente al Feed
- `/feed`:
  - Consume el backend correctamente
  - Renderiza publicaciones con métricas correctas
- Logout:
  - Revoca el token
  - Actualiza el estado visual
  - Fuerza re-login cuando corresponde

---

## 🔒 Reglas respetadas
- No se modificó ninguna lógica del backend
- No se tocaron:
  - Ranking
  - Likes
  - Guardados
  - Feed
  - Historias
- No se mezcló frontend con backend
- Se avanzó por etapas, validando cada paso

---

## 📌 Estado final de la etapa
- Backend estable (ETAPA 31 intacta)
- Frontend integrado y usable
- Feed funcionando end-to-end
- Autenticación completa desde UI
- Base sólida para interacciones futuras

---

### ▶ Próximo paso sugerido
**ETAPA 33 — Interacciones desde el Feed (Frontend)**
- Like y Guardar desde la UI
- Optimistic UI
- Reutilizando endpoints existentes
- Sin modificar lógica de backend


## ETAPA 33 — Interacciones desde el Feed (FRONTEND) ✅ (CERRADA + SUBIDA)

**Objetivo:** permitir interacciones desde la UI del feed sin modificar backend: Like (toggle) y Guardar/Quitar guardado, con Optimistic UI y rollback ante error.

### Cambios realizados (Frontend)
- Se agregaron acciones en el Feed:
  - **Like** (toggle) usando `POST /likes/publicaciones/{publicacion_id}`
  - **Guardar** usando `POST /publicaciones/guardadas` con body `{ publicacion_id }`
  - **Quitar guardado** usando `DELETE /publicaciones/guardadas/{publicacion_id}`
- Se incorporó carga de guardados del usuario:
  - `GET /publicaciones/guardadas`
  - Se construye un `Set` de `publicacion_id` para marcar cada item del feed con `guardada_by_me`.
- **Optimistic UI**:
  - Like: actualiza instantáneamente `liked_by_me` + `likes_count`
  - Guardado: actualiza instantáneamente `guardada_by_me` + `guardados_count`
  - Si el backend falla: **rollback** al estado anterior (snapshot).
- Se agregaron **locks por publicación** para evitar doble click mientras se procesa.

### Infraestructura HTTP (Frontend)
- Se completó la capa `http_service` para soportar las operaciones necesarias:
  - Se agregaron `httpPost` y `httpDelete` (antes existía solo `httpGet`).
  - `httpPost` detecta si la respuesta es JSON o texto.

### Archivos impactados
- `frontend/src/services/http_service.js` (AGREGADO: `httpPost`, `httpDelete`)
- `frontend/src/services/feed_service.js` (AGREGADO: funciones de like/guardado + `fetchPublicacionesGuardadas`)
- `frontend/src/pages/FeedPage.jsx` (REEMPLAZADO/ACTUALIZADO: UI + handlers + optimistic UI)

### Pruebas realizadas
- Feed carga correctamente.
- Se visualiza el estado de cada publicación:
  - `liked_by_me` desde el feed
  - `guardada_by_me` mergeando `GET /publicaciones/guardadas`
- Like:
  - cambia instantáneamente y ajusta contador
  - revierte si falla backend
- Guardar/Quitar:
  - cambia instantáneamente y ajusta contador
  - revierte si falla backend
- Se verificó bloqueo de acciones mientras “Procesando...”.

### Regla de sincronización (Docs + Repo)
Al cerrar esta etapa se actualiza `NUEVOHISTORY.md` y se sube al repositorio con su commit correspondiente.


## ETAPA 34 — Ranking (FRONTEND) ✅ (CERRADA + SUBIDA)

**Objetivo:** mostrar el ranking de publicaciones ordenadas por score (likes + recencia) desde el frontend, reutilizando backend existente, sin modificar lógica de negocio.

### Cambios realizados
- Se creó la pantalla `RankingPage.jsx` consumiendo:
  - `GET /ranking/publicaciones`
- Se renderizan publicaciones ordenadas con:
  - posición en ranking (#1, #2, #3…)
  - métricas: likes, guardados, interacciones
- Se agregó la ruta `/ranking` en el router principal.
- Se incorporó el link **Ranking** en el menú de navegación (`MainLayout`).
- Se reutilizó el estilo visual del feed para mantener consistencia UI.

### Archivos impactados
- `frontend/src/services/feed_service.js` (AGREGADO: `fetchRankingPublicaciones`)
- `frontend/src/pages/RankingPage.jsx` (NUEVO)
- `frontend/src/router/AppRouter.jsx` (AGREGADO: ruta `/ranking`)
- `frontend/src/layouts/MainLayout.jsx` (AGREGADO: link Ranking)

### Pruebas realizadas
- Endpoint `/ranking/publicaciones` responde 200.
- Ranking se visualiza correctamente desde UI.
- Navegación desde menú funciona.
- No se afectó Feed, Login ni Auth.

### Regla de sincronización
Al cerrar esta etapa:
- se actualiza `NUEVOHISTORY.md`
- se sube al repositorio con commit correspondiente


## ETAPA 35 — Ranking interactivo (FRONTEND) ✅ (CERRADA + SUBIDA)

**Objetivo:** permitir interacciones desde la pantalla Ranking sin modificar backend: Like (toggle) y Guardar/Quitar guardado con Optimistic UI y rollback ante error.

### Cambios realizados
- Se extendió `RankingPage` para incluir:
  - Botón **Like** (toggle) consumiendo `POST /likes/publicaciones/{publicacion_id}`
  - Botón **Guardar/Quitar** consumiendo:
    - `POST /publicaciones/guardadas` con body `{ publicacion_id }`
    - `DELETE /publicaciones/guardadas/{publicacion_id}`
- Se incorporó carga de guardados del usuario:
  - `GET /publicaciones/guardadas`
  - Se construye un `Set` de `publicacion_id` y se mergea en el ranking con `guardada_by_me`.
- **Optimistic UI**:
  - Like: actualiza instantáneamente `liked_by_me` + `likes_count`
  - Guardado: actualiza instantáneamente `guardada_by_me` + `guardados_count`
  - Si falla backend: rollback al estado anterior (snapshot).
- Locks por publicación para evitar múltiples clicks mientras se procesa.

### Archivos impactados
- `frontend/src/pages/RankingPage.jsx` (ACTUALIZADO: acciones Like/Guardar + optimistic UI)

### Pruebas realizadas
- Ranking carga correctamente.
- Like funciona desde Ranking (cambio inmediato + contador + rollback si falla).
- Guardar/Quitar funciona desde Ranking (cambio inmediato + contador + rollback si falla).
- No se afectó Feed, Login, Auth ni navegación.

### Regla de sincronización
Al cerrar esta etapa:
- se actualiza `NUEVOHISTORY.md`
- se sube al repositorio con commit correspondiente


## ETAPA 36 — Login real desde UI + Auth estable (FRONTEND) ✅ (CERRADA + SUBIDA)

**Objetivo:** eliminar dependencia de Swagger para autenticación, dejando login/logout funcional desde la UI, sesión persistida y estado global coherente.

### Cambios realizados
- Login desde `http://localhost:5173/login` ahora funciona end-to-end:
  - El token se obtiene del backend y se persiste en `localStorage` como `access_token`.
  - El estado UI se sincroniza (“Sesión activa” / “No autenticado”).
- Se envolvió la app con `AuthProvider` en `main.jsx` renderizando `AppRouter` (estructura correcta).
- `authService` se volvió robusto aceptando respuesta del backend como:
  - `{ access_token }` o `{ token }`.
- Se corrigió warning de Vite Fast Refresh separando `useAuth` en un archivo dedicado.

### Archivos impactados
- `frontend/src/services/authService.js` (FIX: lectura token robusta)
- `frontend/src/context/AuthContext.jsx` (ACTUALIZADO: persistencia + estado auth)
- `frontend/src/context/useAuth.js` (NUEVO: hook separado)
- `frontend/src/main.jsx` (ACTUALIZADO: AuthProvider envolviendo AppRouter)
- `frontend/src/layouts/MainLayout.jsx` (ACTUALIZADO: import de useAuth)
- `frontend/src/pages/Login.jsx` (ACTUALIZADO: import de useAuth)

### Pruebas realizadas
- Login desde UI → redirige a `/feed`, crea `access_token` en localStorage.
- Feed/Guardados/Ranking funcionan con sesión activa (200 OK).
- Logout revoca token y limpia localStorage; endpoints protegidos devuelven 401 (esperado).
- Re-login vuelve a habilitar acceso.
- Vite deja de mostrar warning de Fast Refresh.

### Regla de sincronización
Al cerrar esta etapa:
- se actualiza `NUEVOHISTORY.md`
- se sube al repositorio con commit correspondiente
