# Cobertura visual de frontend — ETAPA 95.5

## 1. Ownership y alcance

Este documento es la matriz trazable exigida por el gate de cobertura de
`22_SEMANTIC_TOKENS_CONTRACT.md`. Registra adopcion, excepciones y pendientes;
no redefine el contrato de tema ni los tokens.

Un estado `pendiente` bloquea el cierre de 95.5. Desde 95.5-M, `Migrado`
describe adopcion tecnica y no basta por si solo: el cierre exige tambien
`Validado light/dark` en la matriz visual. Las excepciones se limitan a
contenido o integraciones que no son apariencia global de FeedGo.

## 2. Matriz acumulada

| Superficie / owner | Estado | Evidencia | Excepcion o pendiente |
| --- | --- | --- | --- |
| Bootstrap, tema global y canvas | Migrado | 95.3; `core/theme`, assets locales y tests de tema | Ninguna |
| Tokens y primitives compartidas | Migrado | 95.4; 38 roles, Button, Surface, controles, Alert y Skeleton | Ninguna |
| Perfil / Editar perfil / selector de apariencia | Migrado | 95.5-A y tests de perfil | Ninguna |
| Registro y Login | Migrado | 95.5-B y tests de Auth | Ninguna |
| MainLayout y navegacion principal | Migrado | 95.5-C; canvas, header, estados de navegacion y acceso usan roles semanticos | Otras navegaciones especificas se auditan con su superficie |
| Explorar: buscador, resultados y estados | Migrado | 95.5-C; primitives/tokens y test contractual de Explorar | Branding, imagenes y videos de espacios/publicaciones son contenido |
| Contexto geografico visible | Migrado | 95.5-C; controles GPS/manual/profile fallback y errores | Ninguna; la logica geografica permanece en su owner funcional |
| Estado horario y editor de horarios | Migrado | 95.5-C/95.5-H; badge, ActiveLayer, editor, HoraInput y estados semanticos | Ninguna; logica y contratos de Availability permanecen en su owner |
| Guardia de inactividad | Migrado | 95.5-C/95.6-A; overlay, superficie y acciones semanticas sobre ActiveLayer | Ninguna; temporizador y acciones permanecen en Auth |
| Feed y cards de publicaciones | Migrado | 95.5-D; FeedPage, PublicacionCard, estados y tests contractuales | Media y overlays sobre imagen/video son contenido |
| Ranking / Tendencias | Migrado | 95.5-E; RankingPage reutiliza PublicacionCard y migra shell/estados | Media de PublicacionCard conserva la excepcion documentada de contenido |
| Seguidos | Migrado | 95.5-F; VerSeguidosPage, tabs, cards, estados y contexto geografico compartido | Media y overlay informativo sobre miniaturas guardadas son contenido |
| Perfil / identidad visible de usuario | Migrado | 95.5-G; shell, cabecera, avatar, metadata, acciones y estados de `/perfil` | No existe actualmente perfil público de terceros; no se inventó ruta, endpoint, publicaciones ni acciones sociales |
| Alta/edicion/administracion de espacios | Migrado | 95.5-H; formulario compartido, listado, acciones, uploads, privacidad y horarios | Branding, portadas e imagenes permanecen contenido |
| Perfil publico de espacio | Migrado | 95.5-I; shell, identidad, geografia publica, acciones, publicaciones, estados y overlays propios usan roles/primitives | Avatar, branding y media son contenido; modales con owner independiente conservan su fila de cobertura |
| LocationPicker y selector cartografico | Migrado | 95.5-H; shell, busqueda, alternativas, estados y acciones usan tokens/primitives | Tiles y controles propios del proveedor cartografico son excepcion legitima |
| Historias: barra, viewer y creacion | Migrado | 95.5-D/95.5-J; HistoriasBar tematizada, viewer con apariencia fija validada y formulario con tokens/primitives | Media es contenido; escenario negro, texto/progreso claros y overlays cinematograficos son contrato local fijo |
| Agenda y reservas | Migrado | 95.5-K; Agenda general y privada, filtros, vista diaria, formularios, listados, estados y capas usan tokens/primitives | No existe actualmente calendario mensual ni flujo publico separado de reservas; no se inventaron superficies |
| Terminos y Politica de Privacidad | Migrado | 95.5-L; rutas publicas, shell legal, jerarquia, aviso, version y enlaces usan roles/primitives | Ninguna; contenido, versiones y contratos legales permanecen en sus owners |
| Home | Migrado | 95.5-O; canvas, hero, tres cards y tres CTAs-enlace usan roles, Surface y bubble compartida | Ninguna; Home no posee media, overlays ni estados asincronos propios |
| Detalle de publicacion | Migrado | 95.5-N; shell, estados, acciones, media y confirmacion usan tokens/primitives | Negro del escenario de imagen/video es excepcion legitima de contenido |
| DenunciaModal | Migrado | 95.5-N; ActiveLayer, Surface, formulario, estados y botones compartidos | Ninguna; payload y owner funcional permanecen inalterados |

## 3. Evidencia de 95.5-C — Explorar

La migracion de Explorar cubre canvas local, modos Espacios/Publicaciones,
buscador y sugerencias, contexto territorial, cards, distancia publica,
estado horario, loading, error, empty, ampliaciones de 50/100 km y paginacion.
Tambien migra los owners globales estrictamente necesarios `MainLayout`,
`GeographicContextControls`, `EstadoHorarioBadge` y
`SessionInactivityGuard`.

Se preservaron Search, Discovery, Candidate Engine, ranking, query keys,
prefetch, debounce, paginacion, privacidad, permisos, `positionRevision` y
Cache-First. Las imagenes, videos y branding de comercios/publicaciones
permanecen fuera del tema global. La evidencia automatizada final comprende
83 tests frontend correctos, lint sin errores y build productivo correcto.

## 4. Evidencia de 95.5-D — Feed

Feed, `PublicacionCard`, `HistoriasBar` e `InteraccionButton` resuelven canvas,
superficies, textos, metadata, acciones, badges, skeletons y estados mediante
tokens/primitives. La bienvenida utiliza overlay, Surface y Button compartidos.

Se preservaron query key, `staleTime`, hidratacion Cache-First, requests,
optimistic updates, locks, mutaciones, navegacion, precarga multimedia, vistas
y reproduccion de historias. La evidencia automatizada comprende 93 tests
frontend correctos, lint sin errores y build productivo correcto.

Los fondos negros, gradientes y textos claros superpuestos directamente sobre
imagen/video en `PublicacionCard` son excepciones de contraste del escenario
multimedia, no tema global. `HistoriasViewer` conserva su implementacion hasta
la validacion de apariencia fija registrada por 95.5-J.

## 5. Evidencia de 95.5-E — Ranking / Tendencias

`RankingPage` resuelve canvas, encabezado, texto secundario, skeletons, error y
estado vacio mediante tokens y primitives. La grilla reutiliza exclusivamente
`PublicacionCard`; no se creo una card, tab, filtro, control o boton paralelo.

Se preservaron query key, endpoint owner, `staleTime`, hidratacion Cache-First,
merge en el orden recibido, locks, optimistic updates, mutaciones y rollback.
La inspeccion productiva detecto y corrigio en el owner CSS el alias de texto
Tailwind v4 para que `text-primary`, `text-secondary`, `text-muted` y
`text-inverse` generen la API documentada. La evidencia automatizada comprende
101 tests frontend correctos, lint sin errores y build productivo correcto.

## 6. Evidencia de 95.5-F — Seguidos

`VerSeguidosPage` resuelve shell, tabs, cards de espacios, placeholders,
distancia publica y estados mediante tokens, `Button`, `Surface` y `Alert`.
Reutiliza sin duplicacion `GeographicContextControls`; los enlaces a espacios y
publicaciones conservan su semantica nativa.

Se preservaron `useMisEspaciosSeguidos`, endpoint, query key con
`positionRevision`, `staleTime`, coordenadas del request, placeholder
Cache-First, permisos y privacidad backend-owned. La ciudad se representa
cuando existe y la distancia solo cuando `distancia_km` forma parte del
contrato publico. Imagenes y overlay de metadata sobre miniaturas guardadas
permanecen como excepcion legitima de contenido multimedia.

La evidencia automatizada comprende 107 tests frontend correctos, lint sin
errores y build productivo correcto.

## 7. Evidencia de 95.5-G — Perfil / identidad de usuario

La superficie real disponible es `/perfil`, protegida y perteneciente a la
cuenta autenticada. No existe ruta ni contrato de perfil publico de terceros.
95.5-G migra su canvas, cabecera, tarjeta de identidad, shell/fallback del
avatar, metadata, mensajes y acciones directas mediante tokens, `Surface`,
`Button` y `Alert`, sin inventar tabs, publicaciones o funcionalidad social.

Se preservaron la carga imperativa existente mediante `GET /usuarios/me`, el
upload de avatar, edicion, logout, navegacion y acciones administrativas. Esta
superficie no poseia query cache ni `PublicacionCard`; por ello no se agrego
una capa Cache-First artificial. Avatar y datos visuales del usuario permanecen
contenido, mientras su borde, fallback y superficie pertenecen al tema.

La evidencia automatizada comprende 114 tests frontend correctos, lint sin
errores y build productivo correcto.

## 8. Evidencia de 95.5-H — Alta, edicion y administracion de espacios

El formulario compartido de alta/edicion y el listado de espacios propios
resuelven superficies, campos, selects, textarea, privacidad, uploads, estados,
cards y acciones mediante tokens y primitives. `LocationPicker` migra solo su
shell FeedGo; conserva borrador, busqueda, alternativas, mapa, reverse,
confirmacion/cancelacion y proteccion asincrona. El editor directo de horarios
y `HoraInput` tambien quedan tematizados sobre `ActiveLayer`, sin modificar
Availability.

Se preservaron `useMisComercios`, Cache-First existente, payloads, endpoints,
validaciones, rubros, especialidades, coordenadas, Geoapify, privacidad,
activar/pausar, ownership y navegacion. Portadas, imagenes y sus
overlays de contraste permanecen como contenido. Los modales de Agenda se
auditaron como owner independiente y continúan en la fila pendiente de Agenda,
sin quedar absorbidos artificialmente por este bloque.

La evidencia automatizada comprende 123 tests frontend correctos, lint sin
errores y build productivo correcto.

## 9. Evidencia de 95.5-I — Perfil publico de espacio

`PerfilComercioPage` resuelve canvas, superficie de identidad, fallback de
avatar, metadata, geografia publica, acciones, estadisticas, creacion de
publicacion y estados mediante tokens, `Button`, `Surface`, controles, `Alert`
y `Skeleton`. Reutiliza `PublicacionCard` y `EstadoHorarioBadge`; no crea cards
ni calculos geograficos paralelos.

Se preservaron `useComercioDetalle`, `usePublicacionesComercio`,
`useHistoriasComercio`, sus query keys y `staleTime`, seguimiento, optimistic
updates, navegacion y proyeccion de privacidad backend-owned. La pantalla solo
presenta direccion y acceso a Maps cuando esos campos existen en el contrato
publico, muestra ciudad cuando es el unico dato territorial recibido y no
interpreta privacidad como ubicacion inexistente. Este endpoint de detalle no
recibe posicion del usuario ni entrega actualmente `distancia_km`; el bloque no
invento calculo o formato alternativo y deja la distancia en su owner vigente.

WhatsApp e Instagram conservan sus colores de marca como excepciones de
identidad externa. Avatar, historias y publicaciones son contenido. Los shells
de `HistoriasViewer`, creacion de Historia, Agenda y Moderacion conservan owners
independientes y siguen clasificados en sus filas correspondientes. Evidencia:
129 tests frontend correctos, lint sin errores y build productivo correcto.

## 10. Evidencia de 95.5-J — Historias

`HistoriasViewer` queda cubierto como `Migrado - apariencia fija validada`.
Declara un owner local `historias-viewer-fixed`, aislamiento de stacking y
`color-scheme: dark`; no consume `ThemeProvider`, tokens adaptativos, `Button`
ni `interactive-bubble`. El escenario negro, progreso y textos claros,
overlays, posiciones y geometria permanecen iguales bajo light/dark/system.
Se preservaron indice, RAF, timer, navegacion, video `playsInline`, autoplay,
likes, `heartFly`, vistas y denuncia. El hardening se limito a foco visible y
nombres accesibles de controles nativos; no se cambiaron sus eventos.

`CrearHistoriaModal` resuelve backdrop, superficie, campos, ayuda, error y
acciones mediante `Surface`, `Input`, `Alert`, `Button` y roles semanticos. Se
preservaron seleccion de archivo, upload, fallback URL, expiracion, payload,
endpoint, callback y cierre. No existe actualmente preview local y no se
invento uno. La evidencia automatizada comprende 140 tests frontend correctos,
lint sin errores y build productivo correcto.

## 11. Evidencia de 95.5-K — Agenda y reservas

Las superficies reales `AgendaGeneralModal` y `AgendaPrivadaModal` resuelven
shell, backdrop, encabezados, vista diaria, fechas, filtros, formularios,
listados, estados, error, warning, loading y empty mediante tokens, `Surface`,
`Button`, controles, `Alert` y `Skeleton`. Ambas conservan `ActiveLayer` como
owner exclusivo de portal, foco, Escape, backdrop y scroll lock.

Se preservaron calculos y seleccion de fechas, contexto archivado, deteccion de
cambios sin guardar, versionado optimista, solapamientos, payloads, endpoints,
query keys, `staleTime`, `placeholderData` Cache-First e invalidaciones de
agenda individual/general. Los estados activo, completado, cancelado y
archivado siguen comunicados textualmente; completar y cancelar conservan
roles success/danger. Availability y horarios reutilizan sus owners ya
migrados y no fueron reimplementados.

El dominio frontend actual no posee calendario mensual ni un flujo publico
separado de reservas; no se inventaron pantallas, estados ni contratos. La
evidencia automatizada comprende 147 tests frontend correctos, lint sin errores
y build productivo correcto.

## 12. Evidencia de 95.5-L — Superficies legales

Las dos superficies reales, `TermsPage` y `PrivacyPolicyPage`, reutilizan un
unico `LegalDocumentLayout` sobre `MainLayout`. El shell, jerarquia visual,
version vigente, aviso institucional, divisores y navegacion consumen tokens,
`Surface` y `Alert`; headings, parrafos, listas, secciones y enlaces conservan
semantica HTML nativa. El enlace de regreso permanece como navegacion y agrega
subrayado y foco visible sin convertirse artificialmente en boton.

No se modificaron textos juridicos, rutas, destinos, consulta de documentos,
query key, `staleTime`, version recibida del backend, checkboxes separados y
desmarcados, obligatoriedad ni payload atomico de Registro. No se detectaron
superficies legales adicionales ni hallazgos nuevos de contenido. La evidencia
automatizada comprende 152 tests frontend correctos, lint sin errores y build
productivo correcto.

## 13. Gate restante

95.5 permanece abierto. Los bloques siguientes deben convertir cada fila
pendiente en `Migrado` o en una excepcion documentada valida. Luego corresponde
el QA visual global light/dark/runtime definido en el contrato propietario.

## 14. Evidencia de 95.5-M — Auditoria visual transversal

La auditoria recorrio todas las rutas y superficies registradas, sus controles,
estados y owners compartidos en light/dark. La inspeccion del CSS productivo y
la reproduccion visual detectaron una causa transversal: `interactive-bubble`
estaba fuera de las capas Tailwind y su `background: transparent` y foreground
tenian precedencia sobre las utilities semanticas de `Button`. Por eso acciones
primary como `Crear elemento` y acciones de Mi cuenta podian quedar con texto
claro sobre una superficie clara. El owner se movio completo a
`@layer components`; geometria, mascara, gradientes, animaciones, timings,
focus, active y reduced motion permanecen iguales, mientras las utilities de
variante recuperan precedencia. `ActiveLayer` tambien adopta el backdrop
semantico como default, sin cambiar portal, foco, Escape ni scroll lock.

### Matriz de validacion visual

| Pantalla / superficie | Adopcion tecnica | Validacion light/dark | Resultado 95.5-M |
| --- | --- | --- | --- |
| Tema, canvas, tokens y primitives | Migrado | Validado | Correccion central de cascade en Button/bubble |
| MainLayout y navegacion | Migrado | Validado | Primary, selected, iconos, foco y canvas verificados |
| Perfil / Editar perfil | Migrado | Validado tras correccion | Acciones de Mi cuenta recuperan superficie/foreground de variante |
| Registro y Login | Migrado | Validado | Formularios, checkboxes, links, password trailing y submit |
| Explorar y contexto geografico | Migrado | Validado | Buscador, selected, resultados, estados y ampliaciones |
| Feed, Ranking y PublicacionCard | Migrado | Validado | Shell/acciones; media conserva excepcion documentada |
| Seguidos | Migrado | Validado | Tabs, cards, distancia, estados y selected |
| Alta/edicion/administracion de espacios | Migrado | Validado | Formularios, branding circundante, LocationPicker y horarios |
| Perfil publico de espacio | Migrado | Validado | Shell, acciones, geografia publica y contenido |
| Historias y Crear Historia | Migrado | Validado | Viewer fijo invariante; formulario adaptativo |
| Agenda general y privada | Migrado | Validado tras correccion | `Crear elemento` recupera fondo primary y contraste correcto |
| Terminos y Politica | Migrado | Validado | Lectura responsive, jerarquia, aviso y enlaces |
| Home | Migrado | Validado | Canvas, hero, cards, foregrounds y CTAs verificados en light/dark |
| Detalle de publicacion | Migrado | Validado | Shell, loading, error, acciones y confirmacion light/dark |
| DenunciaModal | Migrado | Validado | Overlay, campos, mensajes, disabled y acciones light/dark |

Tras 95.5-O quedan **0 superficies funcionales pendientes de migracion**. Las
filas genericas anteriores de overlays, estados y botones ya quedaron
materializadas; no constituyen superficies adicionales. Esto no cierra 95.5:
queda obligatorio el QA visual global final light/dark/runtime de todas las
superficies antes de determinar si existen correcciones residuales.

La correccion acotada posterior mantiene `Perfil / Editar perfil` como
validado: `Color de fondo` abre bajo demanda el selector local de apariencia,
el control historico `Color del perfil` fue retirado, y Guardar y Cancelar
comparten la variante secundaria con `interactive-bubble`. El PATCH queda
limitado a provincia y ciudad; el tema sigue fuera del payload de usuario. Las
opciones conservan radios nativos y bubble sobre superficies neutrales, sin
usar los roles violetas `selected-*`. La correccion no altera el conteo de
superficies pendientes.

## 15. Evidencia de 95.5-N — Detalle de publicacion y denuncia

`PublicacionDetallePage` resuelve canvas, loading, error, superficie, identidad,
texto, metadata y acciones mediante tokens, `Surface`, `Skeleton`, `Alert`,
`Button` e `InteraccionButton`. El escenario negro de imagen/video permanece
como excepcion legitima alineada con `PublicacionCard`; autoplay, loop,
`playsInline`, controls y helpers de media no cambiaron. La confirmacion de
eliminacion reutiliza `ActiveLayer` y bloquea cierre mientras la mutacion esta
activa, igual que el flujo previo.

`DenunciaModal` reutiliza `ActiveLayer` como owner de portal, foco, Escape,
backdrop y scroll lock. Su shell, campos, ayudas, mensajes y acciones consumen
`Surface`, `FormControl`, `Select`, `Textarea`, `Alert` y `Button`. Se preservan
reset por apertura/recurso, limite de detalle, payload, endpoint, bloqueo de
cierre durante submit y estados success/error. La auditoria productiva light y
dark confirma canvas/skeleton del detalle; la composicion del modal usa los
mismos pares de tokens contrastados y no contiene colores fisicos ni logica de
tema local.

## 16. Evidencia de 95.5-O - Home

La ruta publica `/` renderiza `Home` dentro de `MainLayout`. Su superficie real
comprende canvas, hero, etiqueta, titulo, textos, tres CTAs-enlace y tres cards;
no posee requests, loading, error, empty, overlays, formularios, footer o media
propios. Canvas y texto consumen roles semanticos, hero y cards reutilizan
`Surface`, y los CTAs conservan `Link` con sus destinos existentes y componen
la unica implementacion `interactive-bubble`.

Se preservo la bifurcacion de `estaAutenticado`: Explorar permanece publico,
un usuario autenticado accede a `/feed` y un invitado a `/registro`. No se
agregaron listeners, estado de tema, requests ni condiciones responsive. La
inspeccion light/dark verifica foreground, superficie, borde, foco y bubble
desde los owners compartidos; no quedan colores fisicos ni condiciones de tema
en Home.

La matriz acumulada contiene 22 filas: 0 `Pendiente`, 0 `Correccion requerida`
y 0 migradas sin validacion light/dark en la matriz de validacion. Permanecen
solo excepciones justificadas de contenido/media, branding externo, mapa y la
apariencia fija validada de `HistoriasViewer`. El QA visual global posterior
sigue siendo gate abierto y puede volver a clasificar defectos si encuentra
evidencia nueva.

## 17. QA visual global final de 95.5

Se confrontaron las 22 filas de la matriz, los contratos de tema/primitives,
los consumidores reales y el CSS productivo. La inspeccion renderizada con el
frontend real cubrio Home, Login, Registro, Explorar, Terminos y Privacidad en
light/dark, desktop y viewport bajo el breakpoint movil. Las superficies
protegidas, estados con datos, overlays y modales se confrontaron con la
evidencia visual previa de 95.5-M/N, sus owners y tests contractuales; no se
simularon datos ni autenticacion para producir estados irreales.

El QA detecto un riesgo responsive compartido: `Surface` y los controles de
formulario `w-full` no declaraban contraccion explicita dentro de flex/grid.
Se corrigio en primitives con `min-w-0`, incluido el wrapper de trailing action,
y se verificaron Login/Registro reales en light/dark bajo el breakpoint movil.
No se cambio layout, validacion, password toggle ni comportamiento funcional.

Primary, secondary, success, warning, danger, ghost, iconOnly, selected y
disabled conservan foreground, superficie, borde, foco y bubble desde tokens y
owners compartidos. `interactive-bubble` mantiene mascara, gradiente, estados y
reduced motion. Los botones nativos residuales pertenecen a la implementacion
funcional de `InteraccionButton`, sentinela de foco de `ActiveLayer`, selector
de archivo y controles cinematograficos fijos de `HistoriasViewer`; no son una
segunda base visual general.

Los colores fisicos residuales quedan clasificados: escenarios/scrims sobre
media, branding externo WhatsApp/Instagram, tiles/controles Leaflet y contrato
fijo de `HistoriasViewer`. No se detectaron residuos cromaticos accidentales en
superficies normales. El selector de apariencia conserva disclosure cerrado,
radios neutrales con bubble y separacion total del PATCH de perfil.

Resultado final: **22 superficies Validado light/dark**, incluyendo
`HistoriasViewer` como **Apariencia fija validada**; **0 Pendiente**, **0
Correccion requerida**, **0 Sin validar** y **0 defectos visuales bloqueantes
conocidos**. System y cambio runtime permanecen cubiertos por el owner global y
tests de adopcion sin remount, listeners locales ni requests. Con tests, lint y
build correctos, Sprint 95.5 queda tecnicamente cerrado. Este cierre no inicia
95.6 ni ejecuta las auditorias finales de ownership o residuos.

## 18. Evidencia de 95.6-B - Overlays y modales

`ActiveLayer` queda confirmado como owner canonico y unico de portal, backdrop,
foco inicial, focus trap, Escape, restauracion de foco, scroll lock y stacking
base. Bienvenida, inactividad, Agenda general/privada, editor de horarios,
Crear Historia, Crear Publicacion, estadisticas, Denuncia y confirmacion de
eliminacion reutilizan ese owner. La capa compartida cancela el foco inicial si
se desmonta antes del siguiente tick, solo restaura un trigger aun conectado y
permite desplazar verticalmente contenido que supera el viewport.

El editor de horarios adopta el rol valido `overlay-backdrop`; no quedan
backdrops FeedGo normales con aliases paralelos. `HistoriasViewer` permanece
como unica capa fullscreen local justificada por su contrato multimedia fijo y
Denuncia usa `zIndex=1200` para aparecer sobre el viewer sin modificarlo.
`LocationPicker` es una superficie inline, no un modal, y conserva mapa,
borrador y acciones en su owner. No se creo una escala global de z-index ni una
primitive modal adicional.

## 19. Evidencia de 95.6-C - Responsive transversal

Se reauditaron las 22 superficies/owners de la matriz en los rangos existentes:
movil angosto (320 px), movil estandar, breakpoint intermedio y desktop. La
revision cubrio canvas, navegacion, flex/grid, formularios, cards, modales,
media, Historias, LocationPicker, Agenda y documentos legales. No se agregaron
breakpoints nuevos ni se oculto overflow globalmente.

Los defectos objetivos se corrigieron en el owner mas cercano. `Button` limita
su ancho y permite wrap del label; `Alert` admite contraccion y palabras largas;
Explorar apila su encabezado en movil; Seguidos permite wrap de tabs y protege
la contraccion de avatar/texto; las cards de publicacion limitan metadata larga;
y Perfil de espacio/Perfil de cuenta permiten wrap de ubicacion, badges y datos
largos. Tambien se corrigio el typo `max-w-5x1` por el owner Tailwind valido
`max-w-5xl`.

`Surface`, controles de formulario y `ActiveLayer` conservan los contratos
transversales ya cerrados: `min-w-0`, ancho disponible, modal dentro del
viewport, scroll interno y acciones accesibles. MainLayout mantiene navegacion
horizontal controlada en movil; HistoriasBar conserva su scroll intencional y
HistoriasViewer su geometria fullscreen/safe-area; mapa, media y branding no
fueron alterados. Las correcciones son independientes del tema y no introducen
colores fisicos, `dark:*`, listeners ni logica funcional.

La evidencia automatizada agrega un contrato responsive permanente para
contraccion, wrapping, viewport modal, navegacion controlada, cards, perfil de
espacio, LocationPicker y legales. El intento complementario de capturas
headless no produjo archivos de imagen utilizables y no se contabiliza como
evidencia. No quedan defectos responsive bloqueantes conocidos; los estados
autenticados/datos reales siguen dependiendo del QA visual con fixtures o
sesion representativa de ETAPA 98 - Correccion y Pulido Visual del Frontend.

## 20. Cierre tecnico de 95.6

La confrontacion final confirma una cadena coherente: `core/theme` resuelve el
tema, `theme-tokens.css` concentra valores fisicos, las primitives consumen
roles, `interactive-bubble` mantiene una unica implementacion, `ActiveLayer`
concentra infraestructura modal y `MainLayout` conserva el shell global.
`HistoriasViewer` mantiene su contrato multimedia fijo y `LocationPicker`
permanece como superficie inline; ninguno duplica ActiveLayer.

La API publica de primitives queda limitada a `Button`, `Surface`,
`FormControl`, `Input`, `Select`, `Textarea`, `Alert` y `Skeleton`.
`classNames`, tablas de variantes y helpers de controles permanecen internos.
No se encontraron ciclos, variantes nuevas sin evidencia, tema manual, colores
fisicos ni residuos estructurales introducidos por 95.6. Las correcciones de
wrapping no cambian geometria base, focus, disabled, iconOnly, reduced motion o
la composicion del bubble.

Los cinco warnings de lint quedan atribuidos a sus owners preexistentes:
dependencias de hooks en `AuthContext`, `ProfilePage`, `RankingPage` y
`PerfilComercioPage`, mas un disable ahora innecesario en `FeedPage`. No fueron
introducidos ni agravados por 95.6 y se difieren al hardening integral de 95.7
para no alterar comportamiento en este cierre.

Build productivo conserva bootstrap y tokens locales; no se agregaron
dependencias. Permanecen como deuda conocida Browserslist desactualizado,
resolucion runtime de assets Leaflet y chunk principal superior a 500 kB. Con
contratos transversales, suite completa, lint sin errores y build correctos,
95.6 queda tecnicamente cerrado. Esto no ejecuta la Frontend Ownership Audit ni
la auditoria integral de residuos, ambas gates obligatorios de 95.7.
