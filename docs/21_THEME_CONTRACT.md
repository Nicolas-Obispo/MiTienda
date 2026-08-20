# Contrato Global de Tema

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento tecnico de arquitectura frontend.
Nivel de autoridad: Tecnico subordinado a `docs/05_SEARCH_ROADMAP.md` para
ETAPA 95.
Documento dueno: `docs/21_THEME_CONTRACT.md`.
Responsable funcional: Arquitectura frontend y experiencia visual.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `18_PWA_ENTERPRISE.md`,
`20_FRONTEND_VISUAL_INVENTORY.md`, `22_SEMANTIC_TOKENS_CONTRACT.md`.
Cuando debe consultarse: antes de implementar, modificar o validar preferencia
de apariencia, resolucion de tema, bootstrap visual, persistencia de tema,
tokens semanticos, `theme-color` o integracion de tema con PWA.

## 1. Finalidad y limites

Este documento es el owner del contrato runtime de apariencia global de
FeedGo. `20_FRONTEND_VISUAL_INVENTORY` conserva evidencia del estado anterior,
pero no gobierna el runtime.

El contrato no define todavia todos los tokens, no migra pantallas y no
convierte branding de espacios en tema global.

## 2. Owner

El owner de implementacion sera `frontend/src/core/theme/`. Ninguna feature,
pagina, layout, contexto de autenticacion o contexto geografico puede duplicar
lectura, resolucion, persistencia, observacion del sistema o manipulacion del
documento.

Responsabilidades:

- validar y leer la preferencia;
- persistir solo una preferencia explicita;
- resolver el tema efectivo;
- observar `prefers-color-scheme` cuando corresponda;
- aplicar el estado al elemento raiz y a `theme-color`;
- exponer la API React minima;
- adoptar el resultado del bootstrap previo a React;
- fallar de forma segura sin impedir el arranque.

El artefacto bloqueante entregado antes de React forma parte de esta misma
capacidad aunque, por necesidades de carga, se sirva como asset publico.

## 3. Modelo de estado

Tipos cerrados:

```text
ThemePreference = "system" | "light" | "dark"
ResolvedTheme = "light" | "dark"
```

Invariantes:

- `preference` representa la eleccion y nunca se sustituye por el resultado;
- `resolvedTheme` nunca puede ser `system`;
- si la preferencia es `light` o `dark`, el resultado es ese valor;
- si es `system`, el resultado sigue al media query del sistema;
- los cambios del sistema no sobrescriben la preferencia;
- el DOM y `theme-color` reflejan siempre el mismo `resolvedTheme` aceptado.

## 4. Default y degradacion

- Sin valor persistido: `preference = "system"`.
- Con `matchMedia` disponible: `system` se resuelve desde
  `(prefers-color-scheme: dark)`.
- Sin `matchMedia`, ante excepcion o resultado no confiable: fallback `dark`.
- Un valor persistido invalido se trata como ausente (`system`) y no se propaga
  a la API. El runtime puede limpiarlo de forma segura; el bootstrap no debe
  bloquear el render por intentar hacerlo.
- Sin storage o ante error de seguridad/cuota: la preferencia funciona en
  memoria durante la sesion; el arranque usa `system` y su fallback.

Esta politica preserva el aspecto oscuro actual, respeta la preferencia del
sistema cuando puede conocerse y es compatible con una PWA sin red.

## 5. Aplicacion al documento

El mecanismo canonico sera un atributo en el elemento `html`:

```html
<html data-theme="light">
<html data-theme="dark">
```

Tambien debe aplicarse `color-scheme: light` o `color-scheme: dark` al elemento
raiz. No se usara una clase booleana `dark` como estado canonico.

Motivos:

- representa explicitamente ambos estados;
- evita colisiones con clases utilitarias o de layout;
- sirve directamente como selector para variables CSS;
- Tailwind v4 puede consumir variables semanticas y, cuando sea excepcional,
  variantes basadas en el atributo;
- facilita tests, diagnostico y futura integracion PWA;
- permite que controles nativos, scrollbars y formularios reciban
  `color-scheme` coherente.

La futura migracion debe preferir variables semanticas bajo `data-theme` en vez
de multiplicar `dark:` por todas las pantallas.

## 6. Persistencia

Clave canonica:

```text
feedgo.theme.preference.v1
```

Reglas:

- solo se aceptan `system`, `light` y `dark`;
- solo se persiste `ThemePreference`;
- nunca se persiste `resolvedTheme`;
- `system` puede persistirse explicitamente para conservar la eleccion; su
  ausencia tambien se interpreta como `system`;
- el tema no comparte keys con autenticacion, Explorar ni datos de espacios;
- fallar al leer o escribir storage no impide cambiar el tema en memoria;
- no existe sincronizacion entre dispositivos en esta etapa;
- sincronizacion entre pestanas queda fuera del contrato minimo inicial y
  solo se agregara con evidencia, sin impedir una evolucion compatible.

Evolucion aprobada para auditar en ETAPA 99:

- una persona autenticada debe poder conservar su preferencia de apariencia
  entre dispositivos mediante persistencia backend-owned;
- frontend continua siendo owner exclusivo de aplicar y representar la
  preferencia, y el bootstrap local sigue siendo necesario antes de verificar
  sesion o mientras no exista red;
- la auditoria debe definir precedencia y reconciliacion entre preferencia de
  cuenta, storage local y logout/login sin filtrar la eleccion de otra
  identidad;
- para una cuenta sin preferencia persistida, el default de cuenta deseado es
  `dark`; el contrato actual `system` permanece vigente hasta que ETAPA 99
  implemente y migre esta capacidad de forma compatible.

## 7. Bootstrap anti-flash

Antes de que el navegador pinte la aplicacion y antes del modulo React, un
script clasico pequeno y bloqueante en `<head>` debe:

1. leer y validar la preferencia;
2. resolver `system` mediante `matchMedia` o fallback `dark`;
3. aplicar `data-theme` y `color-scheme` a `document.documentElement`;
4. actualizar el meta `theme-color` existente;
5. publicar un bridge privado con el snapshot y las operaciones canonicas que
   adoptara el runtime.

El script no depende de React, red, autenticacion ni backend. Debe formar parte
del app shell en ETAPA 96. La carga debe ocurrir antes de CSS/React susceptible
de pintar superficies; un script module/defer o un efecto React no satisface
este gate.

Fallbacks estaticos:

- `html`/`body` deben conservar un fondo oscuro seguro previo al script;
- el manifest conserva un fondo oscuro estatico para splash/carga, porque el
  manifest no es un selector dinamico de tema;
- un fallo total del bootstrap degrada al aspecto oscuro vigente.

## 8. Unica implementacion de resolucion

No se mantendran dos algoritmos independientes.

El asset de bootstrap constituye el kernel imperativo canonico y publica un
bridge privado, por ejemplo `window.__FEEDGO_THEME_BOOTSTRAP__`. El adapter de
`core/theme` adopta ese snapshot y usa sus operaciones de validar, resolver y
aplicar. React solo agrega suscripcion y API declarativa.

El nombre global es detalle interno, no API para features. Las pantallas nunca
lo consultan. Si el bridge no existe por una falla de carga, el runtime puede
recuperar la aplicacion con fallback oscuro, debe informar el fallo de manera
segura y no mantener una segunda ruta normal de resolucion.

La key, valores validos, media query y aplicacion al DOM deben declararse una
sola vez en el kernel. El runtime obtiene ese contrato desde el bridge.

## 9. Cambios dinamicos del sistema

- Con `preference = "system"`, el runtime mantiene un unico listener moderno
  `MediaQueryList.addEventListener("change", ...)` y actualiza tema resuelto,
  DOM y `theme-color` sin recargar.
- Puede existir fallback a `addListener` solo por compatibilidad comprobada.
- Con preferencia `light` o `dark`, no se instala o se desactiva el listener
  aplicable; cambios del sistema no alteran el tema.
- Al cambiar preferencia se resuelve y aplica sincronicamente antes de notificar
  consumidores para evitar estados intermedios.
- Todo listener se libera al cambiar de modo o desmontar el owner.

## 10. Tailwind v4 y tokens futuros

El contrato no necesita `tailwind.config.js`.

95.4 definira variables semanticas por selector:

```css
:root[data-theme="light"] { ... }
:root[data-theme="dark"] { ... }
```

Tailwind v4 consumira esas variables mediante su configuracion CSS-first y
utilidades semanticas. Las variantes condicionadas por tema se reservaran para
casos que no puedan expresarse mediante un token. El contrato no fija aun los
nombres ni valores de la paleta completa.

## 11. Theme color

Debe existir un unico meta `name="theme-color"`, actualizado por el mismo
`applyTheme` que modifica el DOM.

El mapping es una configuracion del owner, no de las pantallas:

- dark: `#111827`, preservando el chrome oscuro vigente;
- light: `#ffffff`, fallback claro neutro hasta que 95.4 lo alinee con el
  canvas claro definitivo.

Cuando 95.4 defina el canvas final, este mapping debe consumir el mismo valor
fuente o una constante derivada controlada, sin duplicarlo por features.

El manifest mantiene `background_color` oscuro como fallback estatico inicial.
ETAPA 96 validara splash, standalone, app shell y comportamiento offline; 95.3
solo deja el contrato compatible.

## 12. Branding de espacios

`color_fondo`, portadas, imagenes, gradientes y cualquier branding de un
comercio son contenido del dominio Spaces. No cambian `preference`,
`resolvedTheme`, `data-theme`, `color-scheme` ni `theme-color` global.

La migracion visual debera garantizar contraste del contenido dinamico en
ambos temas sin convertirlo en una preferencia global.

## 13. API publica minima

La API React conceptual para consumidores sera:

```text
preference: "system" | "light" | "dark"
resolvedTheme: "light" | "dark"
setPreference(nextPreference): void
```

No se exponen storage, `matchMedia`, bridge, metatags, setters directos de tema
resuelto ni funciones para manipular clases/atributos. Un hook consumidor
podra leer esta API desde el owner transversal.

### 13.1 Superficie de seleccion aprobada

La seleccion manual de apariencia vivira exclusivamente en `Perfil -> Editar
perfil`, como preferencia visual local del usuario. Presentara conceptualmente:

- `Fondo oscuro`, correspondiente a `preference = "dark"`;
- `Fondo claro`, correspondiente a `preference = "light"`;
- `Usar configuracion del sistema`, correspondiente a
  `preference = "system"`.

La pantalla consumira solamente `preference` y `setPreference(...)`. No puede
conocer ni manipular `localStorage`, `matchMedia`, `data-theme`, bootstrap,
bridge, `resolvedTheme` como setter ni `theme-color`. El owner continua siendo
`frontend/src/core/theme/` y el cambio se aplica inmediatamente mediante su
infraestructura global.

No se crearan selectores flotantes, controles en headers ni duplicaciones en
otras pantallas. La preferencia conserva la persistencia local definida en la
seccion 6; no se crea persistencia backend ni sincronizacion entre dispositivos
en ETAPA 95.

Dark conserva visualmente el aspecto vigente y light es su adaptacion visual.
Cambiar apariencia no altera funcionalidad, navegacion, estructura, Search,
permisos, cache, datos, animaciones ni comportamiento de componentes.
`InteraccionButton` e `interactive-bubble` conservan exactamente su efecto e
interaccion.

Esta decision es obligatoria antes del cierre de ETAPA 95. No amplia 95.4-B ni
95.4-C: ambos permanecen limitados, respectivamente, a infraestructura de
tokens y a componentes compartidos. Su implementacion corresponde a 95.5-A,
primer bloque de migracion controlada de pantallas criticas, sobre la superficie
`Perfil -> Editar perfil`.

95.5-A debe verificar cambio inmediato sin reload, persistencia en
`feedgo.theme.preference.v1`, restauracion posterior y consumo exclusivo de
`preference` y `setPreference(...)`. La ausencia del control visible impide
cerrar ETAPA 95 aunque el runtime global de tema este implementado.

## 14. Accesibilidad

- `color-scheme` coincide con el tema resuelto para controles nativos.
- La preferencia de color no modifica ni reemplaza
  `prefers-reduced-motion`.
- El cambio de tema no debe mover foco, cerrar capas ni anunciar ruido
  innecesario a lectores de pantalla.
- Focus visible conserva contraste verificable en ambos temas.
- Texto, iconos, bordes funcionales y estados no dependen solo del color.
- Los controles de seleccion de tema deben tener nombre accesible, estado
  seleccionado y operacion por teclado.
- Cada set de tokens futuro debe superar los criterios de contraste aprobados;
  este contrato no declara conformidad antes de medirla.

## 15. Matriz obligatoria de tests

| Caso | Resultado exigido |
| --- | --- |
| primera carga sin storage | preferencia `system`; tema segun sistema |
| system oscuro | `data-theme=dark`, color-scheme y meta oscuros |
| system claro | `data-theme=light`, color-scheme y meta claros |
| preferencia light | light aunque el sistema sea dark |
| preferencia dark | dark aunque el sistema sea light |
| cambio del sistema en system | actualizacion sincronica sin reload |
| cambio del sistema en explicito | sin cambio visual |
| preferencia persistida | se restaura antes de React |
| valor invalido | se ignora; system + fallback aplicable |
| storage lanza al leer | arranque seguro, preferencia en memoria |
| storage lanza al escribir | cambio de sesion funciona sin persistencia |
| matchMedia ausente/falla | resolvedTheme dark |
| documento | atributo y `color-scheme` siempre coherentes |
| theme-color | coincide con resolvedTheme |
| listener | alta/baja sin fugas ni duplicacion |
| API publica | no expone resolved setter ni detalles de plataforma |
| bootstrap/runtime | runtime adopta snapshot sin repaint divergente |
| anti-flash | atributo ya aplicado antes de cargar/montar React |
| carga directa/refresh | mismo resultado que navegacion normal |
| PWA/app shell | bootstrap local y sin dependencia de red |

La ausencia de flash se verificara inspeccionando orden del HTML y mediante un
test automatizado que ejecute el bootstrap antes del entrypoint React; no se
aceptara como unica evidencia una observacion manual.

## 16. Riesgos y controles

- CSP puede impedir inline scripts: se prefiere asset local bloqueante y una
  politica compatible, sin `unsafe-inline` como requisito.
- Un asset no incluido en app shell causaria flash offline: ETAPA 96 debe
  incluirlo y validarlo.
- Duplicar constantes en React y bootstrap causaria divergencia: bridge
  canonico obligatorio.
- `localStorage` puede fallar incluso cuando existe: toda operacion se protege.
- Un listener permanente ignorando preferencia explicita produciria cambios
  inesperados: suscripcion condicional.
- Actualizar solo `data-theme` y no `theme-color` produciria chrome incoherente:
  aplicacion atomica desde un owner.
- Migrar colores antes de 95.4 produciria un modo claro incompleto: 95.3-C solo
  implementa infraestructura y pruebas del contrato.

## 17. Gate para 95.3-C

95.3-B queda cerrado documentalmente. 95.3-C podra implementar solamente:

- kernel/asset bloqueante de bootstrap;
- modulo owner bajo `frontend/src/core/theme/`;
- provider y hook minimos;
- persistencia tolerante a fallas;
- listener condicional del sistema;
- aplicacion de `data-theme`, `color-scheme` y `theme-color`;
- fondo estatico anti-flash y tests del contrato.

95.3-C no crea la paleta semantica completa, no migra pantallas, no crea
primitives y no cambia el branding de espacios. La activacion visual completa
de light/dark depende de 95.4 y 95.5.

## 18. Evidencia de implementacion 95.3-C

Estado: implementado y validado. El contrato permanece vigente sin cambios de
alcance.

Implementacion:

- `frontend/public/theme-bootstrap.js` es el kernel clasico, local y bloqueante
  cargado en `<head>` antes del entrypoint React;
- la key `feedgo.theme.preference.v1`, validacion, resolucion, aplicacion,
  persistencia tolerante a fallas, snapshot y listener del sistema viven en el
  kernel canonico;
- el bridge privado `window.__FEEDGO_THEME_BOOTSTRAP__` expone solamente las
  operaciones internas necesarias para adopcion runtime;
- `frontend/src/core/theme/` contiene el adapter, contexto, provider y hook;
- React adopta el snapshot con `useSyncExternalStore`; Strict Mode no crea un
  segundo listener de `prefers-color-scheme`;
- `ThemeProvider` envuelve la aplicacion sin depender de autenticacion, Query o
  contexto geografico;
- `data-theme`, `color-scheme` y el unico meta `theme-color` se actualizan desde
  la misma operacion;
- el fallback de emergencia del runtime solo mantiene arranque oscuro si el
  asset no estuvo disponible y no constituye la ruta normal de resolucion;
- `index.html` aporta el fondo oscuro estatico minimo previo a React, sin
  migrar componentes ni crear modo claro visual completo;
- el build productivo copia `theme-bootstrap.js` y mantiene su referencia antes
  del bundle module de React.

Validaciones:

- tests contractuales nuevos: 13/13;
- suite frontend completa: 41/41;
- lint: 0 errores y 5 warnings preexistentes;
- build Vite: correcto, 1.950 modulos transformados;
- artifact productivo: `dist/theme-bootstrap.js` presente y ordenado antes del
  modulo React;
- no se agrego `tailwind.config.js`, tokens, primitives ni clases `dark:`;
- no se modifico branding de espacios ni funcionalidades de 95.1.

Pendientes deliberados al finalizar 95.3-C:

- 95.3-D debia ejecutar auditoria de cierre y hardening de esta infraestructura;
  su resultado queda registrado en la seccion siguiente;
- ETAPA 96 debera incorporar y validar el asset dentro del app shell/offline;
- 95.4 alineara el mapping de `theme-color` con el canvas semantico definitivo;
- 95.4/95.5 implementaran tokens y migracion visual real.

## 19. Validacion, hardening y cierre tecnico 95.3-D

Estado: completado. Sprint 95.3 queda tecnicamente cerrado; ETAPA 95 continua
vigente. El contrato semantico posterior se gobierna en
`docs/22_SEMANTIC_TOKENS_CONTRACT.md`.

Veredicto contrato/implementacion:

- `ThemePreference`, `ResolvedTheme`, default `system`, fallback `dark`, key de
  persistencia, `data-theme`, `color-scheme`, `theme-color`, bridge y API React
  coinciden con este contrato;
- la validacion, resolucion, storage key, media query, aplicacion al DOM y
  listener viven unicamente en `theme-bootstrap.js`;
- `themeRuntime.js` conoce solo la clave necesaria para adoptar el bridge y un
  fallback oscuro de emergencia; no constituye un segundo algoritmo normal;
- ningun feature, pagina o componente shared consume el bridge, storage key,
  `matchMedia`, `data-theme` o `theme-color`;
- existe una sola instancia global del bridge y un solo `ThemeProvider`.

Defecto encontrado y corregido:

- el fondo anti-flash de 95.3-C estaba declarado en un `<style>` inline y podia
  requerir `style-src 'unsafe-inline'`, nonce o hash bajo una CSP estricta;
- se traslado sin cambiar su valor a
  `frontend/public/theme-bootstrap.css`, cargado como stylesheet local antes
  del kernel;
- `index.html` no contiene scripts ni estilos inline introducidos por el tema;
  los estilos dinamicos preexistentes de features quedan fuera de este gate y
  deberan gobernarse en sus etapas correspondientes.

Evidencia automatizada final:

- tests contractuales de tema: 18/18;
- suite frontend completa: 46/46;
- lint: 0 errores y 5 warnings preexistentes;
- build Vite: correcto, 1.949 modulos transformados;
- artifacts: `dist/theme-bootstrap.css` y `dist/theme-bootstrap.js` presentes;
- orden del artifact: CSS anti-flash, kernel bloqueante y luego bundle React;
- inspeccion CSP del artifact: sin `<style>` ni script inline;
- Tailwind v4 preservado sin `tailwind.config.js` ni clases `dark:`;
- manifest: `theme_color` oscuro alineado con el contrato y
  `background_color` oscuro coherente como fallback estatico;
- accesibilidad: el kernel solo modifica raiz/meta, no foco, overlays, scroll ni
  `prefers-reduced-motion`.

Limites del cierre:

- no existe todavia migracion visual clara ni selector de preferencia visible;
- 95.4 debe definir tokens semanticos, valores de canvas y mapping definitivo
  de `theme-color`;
- 95.5 migrara pantallas de forma controlada;
- ETAPA 96 validara inclusion de ambos assets en app shell, offline,
  standalone, restauracion y CSP productiva;
- los warnings historicos de lint, Browserslist, Leaflet y tamano de chunk no
  fueron introducidos ni corregidos en 95.3.

## 20. Evidencia de implementacion 95.5-A

Estado: implementado y validado. La seleccion visible de apariencia existe
exclusivamente en `Perfil -> Editar perfil`.

- `AppearanceSelector` consume solo `preference` y `setPreference(...)` desde
  `useTheme`;
- presenta radios nativos para Fondo oscuro, Fondo claro y Usar configuracion
  del sistema, con estado seleccionado, foco visible y operacion por teclado;
- el cambio es inmediato y la persistencia/restauracion permanecen bajo el
  owner `frontend/src/core/theme/`, sin acceso de la feature a storage,
  `matchMedia`, DOM, bridge, bootstrap ni `theme-color`;
- no existe selector en header, control flotante ni persistencia backend;
- la superficie Editar perfil adopta tokens y las primitives `Surface`,
  `Button`, `FormControl`, `Input` y `Alert`, conservando handlers, validacion,
  upload, submit y branding `color_fondo`;
- sus acciones componen `interactive-bubble` unicamente mediante `Button`, sin
  copiar su CSS ni modificar animaciones;
- la evidencia automatizada cubre opciones, API consumida, teclado, seleccion,
  primitives, handlers preservados y ausencia de colores fisicos o logica
  manual de tema en la superficie migrada;
- validacion: 70 tests frontend correctos, lint sin errores y build productivo
  correcto.

95.5-A no migra Registro, Explorar, Feed, perfiles publicos, espacios, Search,
historias, Agenda ni documentos legales. Sprint 95.5 permanece abierto para
las siguientes migraciones controladas.

## 21. Evidencia de implementacion 95.5-B

Estado: implementado y validado. Registro y Login adoptan el contrato visual
global sin modificar autenticacion, navegacion ni aceptaciones legales.

- ambas superficies usan canvas y texto semanticos, `Surface`, `FormControl`,
  `Input`, `Button` y `Alert`;
- Crear cuenta e Ingresar conservan submit, loading y disabled, y componen
  `interactive-bubble` mediante la variante primary;
- los tres controles de visibilidad de contrasena conservan su estado y ahora
  tienen nombre accesible mediante Button iconografico;
- Registro conserva checkboxes separados, inicialmente desmarcados,
  obligatoriedad, payload, creacion, login automatico y enlaces reales a
  Terminos y Politica;
- los links siguen siendo enlaces, incorporan subrayado y foco visible y no se
  convierten en Button;
- no existe lectura de tema, storage o plataforma en estas pantallas y no
  quedan colores fisicos evitables en las superficies migradas;
- se corrigio el valor de altura visual invalido `min-h-[calc(100vh-px)]` por
  el canvas de pantalla completo, sin modificar flujo funcional;
- validacion: 77 tests frontend correctos, lint sin errores y build productivo
  correcto.

Residuos visuales diferidos: dimensiones y animacion historicas del logo,
branding textual/asset legacy y consistencia global con layouts aun no
migrados. Deben revisarse en los bloques posteriores o QA visual sin reabrir
los contratos de autenticacion.

95.5 permanece abierto. Registro y Login no autorizan migraciones de Perfil
publico, Explorar, Feed, espacios, Search, historias, Agenda o documentos
legales dentro de 95.5-B.
