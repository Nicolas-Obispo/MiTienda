# Inventario Visual del Frontend

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento tecnico de auditoria.
Nivel de autoridad: Tecnico subordinado a `docs/05_SEARCH_ROADMAP.md` para
ETAPA 95.
Documento dueno: `docs/20_FRONTEND_VISUAL_INVENTORY.md`.
Responsable funcional: Arquitectura frontend y experiencia visual.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `18_PWA_ENTERPRISE.md`,
`21_THEME_CONTRACT.md`, `22_SEMANTIC_TOKENS_CONTRACT.md`.
Cuando debe consultarse: antes de disenar infraestructura global de tema,
tokens semanticos, migraciones visuales, modo claro/oscuro o cambios
transversales de superficies, estados y componentes compartidos en ETAPA 95.

## 1. Alcance y metodo

Este documento registra la evidencia de 95.3-A. Es un inventario del frontend
vigente y no define todavia tokens, valores finales ni implementacion de tema.

Se auditaron los 33 archivos JSX, el CSS global, `main.jsx`, `index.html`, el
manifest, configuracion Vite/PostCSS, assets y servicios/contextos con
persistencia o inicializacion relevante. Los conteos son aproximaciones
reproducibles sobre ocurrencias textuales: permiten dimensionar repeticion,
pero no equivalen a componentes visuales unicos.

Superficies incluidas: layout y navegacion, Home, Feed, Explorar/buscador,
Ranking, publicaciones, historias, perfiles, alta/edicion de espacios,
Seguidos, autenticacion/registro, documentos legales, Agenda, Availability,
moderacion, selector de ubicacion, contexto geografico, cards, modales,
loaders, errores y estados vacios.

## 2. Infraestructura actual

- Tailwind CSS v4.1 se integra mediante `@import "tailwindcss"` y
  `@tailwindcss/postcss`; no existe ni resulta requerido hoy un
  `tailwind.config.js`.
- Existe un unico CSS propio: `frontend/src/index.css`. Contiene animaciones y
  la familia reutilizable `interactive-bubble`, con variables locales
  `--bubble-*`; no contiene variables globales de tema.
- No existe `ThemeProvider`, preferencia de tema, tema resuelto, atributo
  `data-theme`, clase `dark`, aplicacion central al documento ni persistencia
  de apariencia.
- No existen utilidades `dark:` ni consulta JavaScript a
  `prefers-color-scheme`. La unica media query visual es
  `prefers-reduced-motion` para `interactive-bubble`.
- `main.jsx` monta Query, autenticacion y contexto geografico. Ninguno es owner
  de apariencia.
- `index.html` no aplica color al `html`, `body` o `#root` antes de React. Su
  `theme-color` es `#111827`; el manifest usa fondo `#030712` y tema `#111827`.
- `localStorage` se usa para sesion y preferencias de Explorar, pero no para
  tema. Las coordenadas precisas no forman parte de este inventario visual.
- La paleta `color_fondo` de un espacio en `ProfilePage` es contenido/branding
  del comercio, no preferencia global de apariencia y no debe convertirse en
  owner del tema de la aplicacion.

## 3. Evidencia cuantitativa

En 29 archivos JSX se detectaron aproximadamente 1.079 utilidades de color:

| Familia | Ocurrencias | Variantes | Valores dominantes |
| --- | ---: | ---: | --- |
| fondos/gradientes | 358 | 63 | `bg-gray-900` 76, `bg-gray-950` 71, `bg-gray-800` 38, `bg-white` 23 |
| texto | 471 | 47 | `text-white` 130, `text-gray-400` 87, `text-gray-300` 57, `text-gray-500` 34 |
| bordes | 216 | 32 | `border-gray-800` 106, `border-gray-700` 34, `border-red-900` 14 |
| ring/outline/accent | 34 | 9 | `outline-orange-400` 11, `ring-white/10` 9, `ring-orange-500` 7 |

Archivos con mayor concentracion aproximada: `ProfilePage` 155,
`PerfilComercioPage` 152, `AgendaPrivadaModal` 108,
`HorariosAtencionEditor` 85, `AgendaGeneralModal` 63 y `Registro` 52.

Estados detectados: `hover:` 112, `focus:` 84, `focus-visible:` 46,
`disabled:` 39 y `active:` 3. Existen 14 skeletons `animate-pulse`; no se
detecto un loader compartido ni `animate-spin`.

## 4. Matriz visual trazable

| Familia actual | Uso y superficies principales | Valores/patrones actuales | Repeticion | Owner natural | Riesgo | Categoria semantica futura posible |
| --- | --- | --- | ---: | --- | --- | --- |
| canvas oscuro | layout, Feed, perfiles, detalle, ranking | `bg-gray-950`, `bg-gray-900` | muy alta | tema global | alto: dos canvases compiten | canvas/background |
| superficie base | cards, formularios, paneles, modales | `bg-gray-950`, `bg-gray-900`, `bg-gray-800` | muy alta | componentes compartidos + tema | alto | surface |
| superficie elevada | modales, dropdowns, cards destacadas | fondos anteriores + `shadow-xl/2xl`, bordes | alta | ActiveLayer/modal/card | alto | elevated surface |
| superficie clara deliberada | CTA, selector, dropdown de Explorar, contenido de historias | `bg-white`, `bg-gray-100`, `text-black/gray-950` | media | componente consumidor | alto: puede ser CTA o superficie accidental | inverse/primary action/surface |
| texto principal | todas las pantallas | `text-white`, `text-gray-100/200` | muy alta | tema global | medio | primary text |
| texto secundario | metadatos, ayudas, labels | `text-gray-300/400` | muy alta | tema global | medio | secondary text |
| texto atenuado | placeholders, notas, estados | `text-gray-500/600/700` | alta | tema global | alto en modo claro/contraste | muted text |
| bordes/divisores | cards, inputs, headers, modales | `border-gray-800/700/600` | muy alta | tema + primitives | alto | border/subtle border |
| marca/accion | botones, seleccion, focus, headings | orange 300-600 y gradiente orange/amber | alta | tema de producto | medio | brand/primary/selected |
| seleccion/navegacion | header, tabs, modos de Explorar/Seguidos | purple 300 y combinaciones white/inverse | media | navegacion/tabs compartidos | alto por patrones distintos | selected/navigation active |
| danger/error | errores, denuncias, eliminacion | red 100-500, fondos red 900/950, bordes red | alta | feedback/accion destructiva | medio | danger/error |
| success | disponibilidad y confirmaciones | green/emerald con fondo, borde, texto y dot | baja-media | badge/feedback | medio | success |
| warning | avisos legales, disponibilidad, agenda | amber/yellow 100-950 | media | feedback | medio | warning |
| overlay | modales, viewer, sesion, formularios | `bg-black/70`, `/75`, `/80`, `/40`, blur variable | media | `ActiveLayer` | alto: owners paralelos | overlay/backdrop |
| skeleton | perfiles, cards y listas | `bg-gray-900/950` + `animate-pulse` | 14 | primitive futuro de carga | medio | skeleton |
| focus | inputs/botones/burbuja | orange ring/outline; white/purple/red aislados | alta pero inconsistente | primitive interactivo | alto accesibilidad | focus |
| disabled | botones y controles | `opacity-60`, cursor, colores sin centralizar | 39 | primitive interactivo | medio | disabled |
| sombra/elevacion | cards, dropdowns y modales | `shadow-sm/md/lg/xl/2xl`, arbitrary shadows | 27+ | tema/primitives | medio | elevation |
| branding de espacio | portada/perfil del comercio | `#111827`, `#1F2937`, `backgroundColor` dinamico | localizado | dominio Spaces | alto si se confunde con tema | content/tenant accent |
| efecto burbuja | interacciones, nav, historias | variables `--bubble-*`, gradientes RGB/RGBA | compartido | `interactive-bubble` | medio-alto | interactive effect/brand |

## 5. Componentes y reutilizacion

Patrones compartidos existentes que deben preservarse y evaluarse antes de
crear equivalentes:

- `MainLayout`: canvas, header y navegacion principal;
- `ActiveLayer`: portal, backdrop configurable, bloqueo de scroll, foco,
  Escape y semantica dialog;
- `InteraccionButton` + `interactive-bubble`: like/guardar y efecto de marca;
- `PublicacionCard`: card publica reutilizada en tres superficies;
- `EstadoHorarioBadge` y `HoraInput`: estados y controles de Availability;
- `LegalDocumentLayout`: superficie comun de documentos publicos;
- `LocationPicker`: selector y mapa, cuyo contrato funcional no se reabre;
- `GeographicContextControls`: contexto territorial compartido.

La reutilizacion es parcial: se contabilizaron 105 botones, 37 inputs, 9
selects y 4 textareas nativos. No existe un primitive comun de Button, Input,
Select, Textarea, Card, Alert, EmptyState, Skeleton o Loader.

## 6. Duplicaciones y variantes equivalentes

- Cards y formularios repiten combinaciones de `rounded-*`,
  `border-gray-800`, `bg-gray-900/950` y textos grises en cada feature.
- Botones primarios alternan blanco/inverse, naranja solido, gradiente
  naranja-amber e `interactive-bubble`.
- Inputs alternan fondos `gray-900/950`, bordes `gray-700/800` y focus
  orange/white sin contrato comun.
- Navegacion seleccionada usa purple en el header y white/inverse en tabs de
  Explorar y Seguidos.
- Errores repiten paneles red con distintas opacidades y combinaciones de
  borde/texto.
- Los overlays tienen al menos cuatro opacidades y varios z-index; solo Agenda
  y Availability reutilizan consistentemente `ActiveLayer`.
- Skeletons repiten bloques locales sin primitive ni contraste de tema.
- Estados vacios y mensajes de carga/error se construyen por pantalla.

## 7. Hardcodes y estilos propios

- Existen hexadecimales en metadata PWA y en la paleta de fondo del comercio.
- `index.css` concentra RGB/RGBA, gradientes, sombras y variables locales del
  efecto burbuja. Es comportamiento visual de marca, no un sistema de tema.
- Hay cinco usos de `style`: z-index de `ActiveLayer`, tipografia Nunito en dos
  headings de Feed, ancho de progreso de historias y color de branding del
  espacio. Solo el color de branding es cromatico y es dato dinamico legitimo.
- Historias incluye un `stroke` RGBA y `interactive-bubble` agrega variables
  RGBA inline para like/guardar.
- Se detecto una clase arbitraria sospechosa `rounded-[px]` en
  `PerfilComercioPage`; debe auditarse en la migracion de esa pantalla, no
  corregirse en 95.3-A.

## 8. Owner recomendado para el tema

No existe owner actual. El owner natural recomendado es una capacidad
transversal de frontend bajo `frontend/src/core/theme/`, porque aplica antes y
por encima de features, layouts y rutas.

Responsabilidades conceptuales para 95.3-B:

- contrato de preferencia: `system`, `light`, `dark`;
- resolucion efectiva separada de la preferencia;
- aplicacion unica al elemento raiz del documento;
- persistencia versionada de la preferencia, no del tema resuelto;
- suscripcion a cambios del sistema solo cuando la preferencia sea `system`;
- bootstrap previo al primer render para evitar flash;
- sincronizacion futura de `theme-color`/superficie instalada compatible con
  ETAPA 96.

Auth, GeographicContext, Spaces y `MainLayout` no deben convertirse en owners
del tema. Un provider React podra exponer interaccion, pero no alcanza por si
solo para la inicializacion previa al render.

## 9. Persistencia, inicializacion y flash

Estado actual:

- no hay preferencia ni clave de apariencia;
- la aplicacion renderiza directamente superficies oscuras;
- `body` carece de fondo inicial;
- el navegador puede pintar su canvas claro antes de cargar CSS/React;
- el manifest (`#030712`) y el meta theme-color (`#111827`) tampoco usan el
  mismo valor.

Por eso existe riesgo real de flash claro al inicio, especialmente con carga
fria, red lenta, standalone/PWA o restauracion del proceso. Implementar solo un
provider React dejaria abierta esa ventana.

## 10. Compatibilidad PWA

La futura solucion debe preservar la arquitectura PWA y coordinar:

- color inicial del documento;
- `theme-color` del navegador/standalone;
- fondo del manifest como fallback estatico;
- safe areas y overlays en superficies instaladas;
- bootstrap disponible aun cuando el app shell provenga de cache;
- ausencia de dependencia de red para resolver preferencia;
- cambios de sesion sin mezclar preferencia con datos sensibles.

ETAPA 95 no implementa service worker, offline ni instalacion: solo debe evitar
que el sistema de tema dificulte ETAPA 96.

## 11. Riesgos de migracion

1. Reemplazar por nombre de color confundiria roles diferentes que hoy usan el
   mismo valor, por ejemplo blanco como texto, superficie inverse y CTA.
2. Mapear `gray-900` o `gray-950` uno a uno conservaria la duplicacion en vez
   de definir canvas/surface/elevation.
3. Alterar `color_fondo` de espacios cambiaria contenido del propietario, no
   tema global.
4. Migrar overlays fuera de `ActiveLayer` podria romper scroll, foco y Escape.
5. Cambiar colores funcionales sin validar contraste puede degradar estados.
6. Aplicar modo claro pantalla por pantalla puede producir superficies mixtas.
7. Crear tokens antes de clasificar primitives produciria aliases redundantes.
8. Cambiar gradientes/efecto burbuja junto con tema mezclaria identidad visual
   y semantica.
9. Las clases construidas dinamicamente requieren migracion controlada para no
   perder generacion de Tailwind.
10. Los documentos legales, mapas/Leaflet e historias fullscreen requieren
    validacion especifica, no sustitucion mecanica.

## 12. Gate aplicado en 95.3-B

95.3-A quedo cerrado con este inventario y habilito exclusivamente el diseno
del contrato global del tema y su bootstrap:

1. fijar estados de preferencia y tema resuelto;
2. fijar owner, API publica y limite con `index.html`/React;
3. definir persistencia, valor inicial oscuro y modo sistema;
4. definir estrategia anti-flash y actualizacion de `theme-color`;
5. definir validaciones automatizadas y compatibilidad PWA;
6. mantener fuera tokens semanticos, primitives y migracion de pantallas, que
   pertenecen a 95.4/95.5.

No se modifico UI, CSS, componentes ni infraestructura de tema durante 95.3-A.

El contrato resultante de 95.3-B y su owner runtime se registran en
`docs/21_THEME_CONTRACT.md`. Este inventario permanece como evidencia y no
duplica ni reemplaza ese contrato.
