# Frontend Ownership Audit - ETAPA 95.7-A

Estado: completado. Este documento registra evidencia de ownership; no ejecuta
la auditoria integral de residuos de 95.7-B ni autoriza refactors masivos.

## 1. Owners confirmados

| Responsabilidad | Owner | Veredicto |
| --- | --- | --- |
| Tema, preferencia y tema resuelto | `frontend/src/core/theme/` | OK |
| Valores fisicos y aliases semanticos | `public/theme-tokens.css` + `core/theme/tokens.css` | OK |
| Botones normales | `shared/components/primitives/Button.jsx` | OK |
| Efecto FeedGo de botones | `src/index.css` (`interactive-bubble`) | OK, implementacion unica |
| Formularios visuales | `shared/components/primitives/FormControls.jsx` | OK |
| Superficies, mensajes y skeleton | primitives `Surface`, `Alert`, `Skeleton` | OK |
| Portal y comportamiento modal | `core/components/ActiveLayer.jsx` | OK, implementacion unica |
| Shell global | `shared/layouts/MainLayout.jsx` | OK con deuda de capa documentada |
| Contexto geografico efimero | `shared/location/GeographicContext.jsx` | OK |
| Geocoding frontend | `shared/services/geocoding_service.js` | OK: solo backend FeedGo |
| Like/guardar visual y funcional | `InteraccionButton` + feature `social` | OK |
| Viewer multimedia fijo | `HistoriasViewer.jsx/.css` | OK, contrato local justificado |

Los contexts reales son tres: Auth, Theme y Geographic. No duplican stores ni
persisten datos de negocio. Theme delega en el bridge; Geographic conserva solo
estado efimero de sesion y revision de posicion; Auth conserva sesion/usuario y
limpia TanStack Query al cambiar de identidad.

## 2. Hallazgos clasificados

### Duplicacion real

- La lectura del token aparece en `AuthContext`, `AppRouter`, services, hooks y
  algunas pages, con aliases historicos diferentes (`access_token`, `token`,
  `accessToken` y otros). El owner deseado es Auth/infraestructura HTTP. No se
  consolida en 95.7-A porque cambia el contrato de autenticacion de numerosos
  requests.
- Existen query keys literales fuera de `core/constants/queryKeys.js`: legal,
  availability y prefijos de Explore/Seguidos usados en invalidaciones. Son
  compatibles hoy, pero debilitan la fuente unica y deben consolidarse con
  tests de invalidacion.

### Ownership incorrecto

- `ProfilePage` ejecuta directamente el PUT de avatar pese a existir capa de
  services de usuario/auth.
- `PublicacionDetallePage` ejecuta directamente DELETE de publicacion; el
  transporte debe vivir en un service/hook de posts.
- `usePublicacionDetalle` contiene su propio `httpGet` en vez de delegar el
  transporte al service de posts.
- `AppRouter` inspecciona multiples keys de storage como fallback paralelo a
  `useAuth`. Es una compatibilidad historica con riesgo de divergencia.
- `MainLayout`, ubicado en `shared`, conoce Auth y monta la guardia de
  inactividad. Su responsabilidad real es composicion global/core; moverlo es
  un refactor de imports/routing y se difiere.

### Deuda tolerable

- Feed, Ranking y Perfil de espacio mantienen copias locales derivadas de datos
  TanStack Query para merges optimistas/compatibilidad. Cache-First se preserva,
  pero el doble estado aumenta complejidad.
- `socialCacheUtils` descubre caches de publicaciones mediante coincidencias de
  texto en query keys. Funciona con las keys actuales, pero es mas amplio y
  fragil que predicates basados en el owner canonico.
- Services historicos normalizan varias formas de respuesta y algunos aceptan
  aliases legacy de token. No se retiran sin confirmar compatibilidad real.
- `GeographicContextControls` es transversal pero conoce Auth para ofrecer el
  fallback visible de perfil. La dependencia responde al contrato de producto;
  conviene revisar su ubicacion, no su comportamiento.

### Riesgo funcional

- El merge de Ranking consulta Feed para completar `liked_by_me` y combina
  guardados sin recalcular ni reordenar ranking. El ownership del scoring sigue
  en backend, pero simplificar ese merge sin un contrato backend equivalente
  puede romper estados sociales.
- Cambiar dependencias de effects advertidas por lint puede alterar ciclos de
  carga, merges optimistas o requests. Requiere pruebas de comportamiento antes
  de aplicar fixes mecanicos.
- Unificar lectura de credenciales o retirar aliases puede invalidar sesiones
  historicas; requiere una decision de migracion de sesion.

### Residuo candidato para 95.7-B

- aliases legacy de token y comentarios/nombres historicos `MiPlaza`;
- `console.log` de registro del service worker;
- export publico `horariosAtencionQueryKeys`, si no tiene consumidor real;
- ramas de normalizacion/compatibilidad de respuestas sin evidencia vigente;
- barrels con `export *` potencialmente mas amplios que sus consumidores;
- helpers, comentarios y disables historicos identificados por la auditoria;
- CSS fisico del bubble y HistoriasViewer debe clasificarse como contrato
  permanente, no eliminarse automaticamente.

## 3. Negocio y contratos backend

No se encontro calculo frontend de scoring, seleccion territorial, privacidad
privada, geocoding directo a Geoapify/Nominatim ni Haversine para distancia
publica. El calculo entre lecturas del dispositivo pertenece al criterio
frontend aprobado de `positionRevision`; el formato m/km es presentacion. Los
sorts de Agenda/Horarios/Historias ordenan representacion cronologica o visual,
no sustituyen ranking o disponibilidad backend.

Los requests se concentran mayormente en services y hooks. Los `fetch` directos
restantes viven en infraestructura HTTP o services de upload multipart. Las
excepciones de pages/hooks quedan listadas como ownership incorrecto.

## 4. Warnings historicos

| Owner | Causa | Riesgo / recomendacion |
| --- | --- | --- |
| `AuthContext` | `useMemo` omite `logout` y `refrescarUsuario` | Riesgo de closures; estabilizar callbacks con tests de sesion |
| `ProfilePage` | effect omite `loadUsuarioMe` | Puede repetir carga o capturar estado; aislar owner de query antes de corregir |
| `FeedPage` | disable de lint sin warning asociado | Corregido en 95.7-A; solo se retiro el comentario inerte |
| `RankingPage` | effect omite `loadRanking` y longitud local | Riesgo alto de ciclos/refetch; tratar junto con doble estado Query/local |
| `PerfilComercioPage` | effect omite merge de publicaciones/guardadas | Riesgo de recarga o merge stale; requiere test de Cache-First/social |

## 5. Correcciones seguras de 95.7-A

- `CrearHistoriaModal` consume ahora `useAuth`, no el `AuthContext` interno.
- El barrel Auth dejo de exportar accidentalmente `AuthContext`.
- Se retiro el disable de lint inerte de Feed.
- Un test contractual permanente protege owners de Auth, Theme, Geography,
  Geocoding y ActiveLayer.

No se modificaron endpoints, payloads, query keys, cache, negocio ni backend.

## 6. Veredicto y siguiente alcance

El frontend tiene owners principales claros y la arquitectura
Frontend -> Services -> Backend Routes -> Backend Services -> DB se cumple en
la mayoria de los flujos. La auditoria se aprueba con deuda historica trazada;
ningun hallazgo exige reabrir 95.5/95.6.

95.7-B ejecuto la auditoria integral de residuos registrada, verificando uso
real antes de conservar, documentar o eliminar. 95.7-C confronto esta evidencia
sin repetir la auditoria y confirmo que la deuda de token, query keys, doble
estado y transporte directo no constituye un bloqueante del cierre tecnico de
ETAPA 95 ni autoriza una limpieza automatica.
