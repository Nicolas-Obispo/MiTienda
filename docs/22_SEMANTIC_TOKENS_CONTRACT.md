# Contrato de Tokens Semanticos

Estado del documento: Documento Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento tecnico de arquitectura visual.
Nivel de autoridad: Tecnico subordinado a `docs/05_SEARCH_ROADMAP.md` para
ETAPA 95.
Documento dueno: `docs/22_SEMANTIC_TOKENS_CONTRACT.md`.
Responsable funcional: Arquitectura frontend, producto y accesibilidad visual.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `18_PWA_ENTERPRISE.md`,
`20_FRONTEND_VISUAL_INVENTORY.md`, `21_THEME_CONTRACT.md`.
Cuando debe consultarse: antes de crear, modificar, mapear o migrar tokens
visuales, primitives compartidos, colores globales, estados funcionales,
efecto burbuja, canvas o `theme-color` en ETAPA 95.

## 1. Finalidad y limites

Este documento define el contrato semantico de 95.4-A. No implementa tokens,
no migra pantallas, no crea primitives y no cambia funcionalidades.

Light y dark son variantes visuales del mismo producto. No pueden alterar
navegacion, Search, permisos, cache, estructura, estado funcional, animaciones,
eventos ni comportamiento de componentes. Un componente consume un rol visual
y no decide colores mediante consultas manuales al tema resuelto.

Dark debe conservar la identidad actual. Light adapta canvas, superficies,
texto, bordes y estados sin convertir toda la interfaz en blanco/negro ni
eliminar profundidad o marca.

## 2. Principios semanticos

1. Los nombres expresan responsabilidad, nunca color fisico o tema.
2. Un rol debe existir porque al menos una responsabilidad visual real lo
   necesita, no para reflejar cada clase Tailwind encontrada.
3. Un mismo valor fisico puede servir a varios roles, pero los roles no se
   fusionan si pueden evolucionar de manera independiente.
4. Marca, accion primaria, seleccion y estado funcional son responsabilidades
   diferentes aunque hoy compartan tonos.
5. Fondo, foreground y borde de un estado deben formar un conjunto verificable.
6. La jerarquia se conserva entre temas: canvas < surface < elevated.
7. Los componentes no consumen hex, escalas gray/orange ni `dark:` cuando el
   valor pertenece al tema.
8. Branding de espacios es contenido y permanece fuera del contrato global.
9. Animacion, geometria, timing y comportamiento no son tokens cromaticos.
10. Todo valor propuesto es candidato sujeto a validacion automatizada de
    contraste antes de implementarse.

### 2.1 Arquitectura visual evolucionable

La direccion permanente de dependencias visuales es:

```text
tokens semanticos
-> primitives y componentes compartidos
-> componentes de dominio
-> pantallas
```

Las pantallas no son propietarias de la apariencia global. Colores, fondos,
superficies, bordes, sombras y demas decisiones que expresen identidad FeedGo
deben consumirse desde su owner compartido. Cambiar una decision global debe
requerir principalmente una modificacion central y propagarse por composicion,
sin recorrer manualmente pantallas o consumidores.

La centralizacion no elimina variantes. Una base compartida puede ofrecer
primary, secondary, danger, success, ghost o icon y conservar para cada una su
rol, semantica, dimensiones justificadas y comportamiento. Lo comun centraliza
infraestructura, accesibilidad, geometria base, estados y efecto FeedGo; lo
variable conserva el significado del dominio o de la accion.

Antes de introducir una decision visual repetida debe verificarse:

> Pertenece a esta pantalla o expresa identidad visual global de FeedGo?

Si es global o compartida, debe buscarse un owner comun antes de repetirla. Si
pertenece al contenido, al branding de un comercio o a una necesidad real del
dominio, permanece local. Esta separacion permite evolucionar apariencia sin
modificar negocio, navegacion, Search, cache, backend ni contratos de datos.

## 3. Lista minima aprobable

### 3.1 Canvas y superficies

- `canvas`: fondo global principal.
- `canvas-subtle`: segundo plano o zona diferenciada de pagina.
- `surface`: contenedor base, card o formulario.
- `surface-subtle`: agrupacion interna o control neutral.
- `surface-elevated`: modal, dropdown o superficie por encima del flujo.
- `elevation-shadow`: sombra comun para superficies elevadas.

### 3.2 Texto

- `text-primary`: contenido y titulos principales.
- `text-secondary`: labels, metadata y ayudas relevantes.
- `text-muted`: informacion atenuada no esencial.
- `text-inverse`: texto sobre fondos oscuros o intensos independientes del
  canvas actual.

### 3.3 Bordes

- `border-subtle`: separacion de baja prominencia.
- `border`: limite normal de controles y superficies.
- `border-strong`: limite que necesita mayor contraste.

No se crea `border-selected`: el estado seleccionado tiene su propio conjunto
completo y evita mezclar seleccion con borde generico.

### 3.4 Marca e interaccion primaria

- `brand`: acento identificatorio FeedGo.
- `brand-strong`: variante de mayor contraste para texto/icono o enfasis.
- `interactive-primary`: fondo de accion primaria.
- `interactive-primary-hover`: hover de esa accion.
- `interactive-primary-active`: estado presionado.
- `interactive-on-primary`: contenido sobre la accion primaria.

No se define un token generico `interactive-hover`: el hover depende del tipo
de control. Los controles neutrales podran derivar su hover de
`surface-subtle`, mientras la accion primaria usa su conjunto propio.

### 3.5 Disabled

- `disabled-surface`: superficie no interactiva.
- `disabled-text`: contenido deshabilitado.
- `disabled-border`: limite deshabilitado cuando exista.

Disabled no debe expresarse solo con opacidad; esta puede permanecer como
refuerzo cuando el componente actual la use, sin ser la unica senal.

### 3.6 Estados funcionales y seleccion

Cada estado tiene superficie, texto/acento y borde:

- `success-surface`, `success-text`, `success-border`;
- `warning-surface`, `warning-text`, `warning-border`;
- `danger-surface`, `danger-text`, `danger-border`;
- `selected-surface`, `selected-text`, `selected-border`.

Rojo conserva danger/error y like activo cuando corresponda; verde/emerald
conserva success; amber/yellow conserva warning/guardado; purple conserva la
seleccion actual mientras no exista una decision visual posterior.

### 3.7 Overlay, skeleton y foco

- `overlay-backdrop`: oscurecimiento de fondo para capas activas.
- `skeleton-base`: bloque en reposo.
- `skeleton-highlight`: variacion perceptible durante la carga.
- `focus-ring`: indicador de foco visible global.

## 4. Valores candidatos dark/light

Los nombres CSS definitivos usaran el prefijo interno `--fg-` para evitar
colisiones y se expondran a Tailwind con aliases semanticos. Ejemplo:
`--fg-color-canvas` -> utilidad futura `bg-canvas`.

| Rol | Dark | Light |
| --- | --- | --- |
| `canvas` | `#030712` | `#f8fafc` |
| `canvas-subtle` | `#111827` | `#f1f5f9` |
| `surface` | `#111827` | `#ffffff` |
| `surface-subtle` | `#1f2937` | `#f1f5f9` |
| `surface-elevated` | `#172033` | `#ffffff` |
| `elevation-shadow` | `0 20px 45px rgb(0 0 0 / 0.35)` | `0 20px 45px rgb(15 23 42 / 0.14)` |
| `text-primary` | `#f9fafb` | `#111827` |
| `text-secondary` | `#d1d5db` | `#374151` |
| `text-muted` | `#9ca3af` | `#6b7280` |
| `text-inverse` | `#111827` | `#ffffff` |
| `border-subtle` | `#1f2937` | `#e5e7eb` |
| `border` | `#374151` | `#d1d5db` |
| `border-strong` | `#4b5563` | `#9ca3af` |
| `brand` | `#fb923c` | `#c2410c` |
| `brand-strong` | `#f97316` | `#9a3412` |
| `interactive-primary` | `#fb923c` | `#c2410c` |
| `interactive-primary-hover` | `#fdba74` | `#9a3412` |
| `interactive-primary-active` | `#f97316` | `#7c2d12` |
| `interactive-on-primary` | `#111827` | `#ffffff` |
| `disabled-surface` | `#1f2937` | `#e5e7eb` |
| `disabled-text` | `#6b7280` | `#6b7280` |
| `disabled-border` | `#374151` | `#d1d5db` |
| `success-surface` | `#052e16` | `#f0fdf4` |
| `success-text` | `#bbf7d0` | `#166534` |
| `success-border` | `#166534` | `#86efac` |
| `warning-surface` | `#451a03` | `#fffbeb` |
| `warning-text` | `#fde68a` | `#92400e` |
| `warning-border` | `#b45309` | `#fcd34d` |
| `danger-surface` | `#450a0a` | `#fef2f2` |
| `danger-text` | `#fecaca` | `#991b1b` |
| `danger-border` | `#991b1b` | `#fca5a5` |
| `selected-surface` | `#3b0764` | `#f3e8ff` |
| `selected-text` | `#d8b4fe` | `#6b21a8` |
| `selected-border` | `#7e22ce` | `#c084fc` |
| `overlay-backdrop` | `rgb(0 0 0 / 0.75)` | `rgb(15 23 42 / 0.55)` |
| `skeleton-base` | `#1f2937` | `#e5e7eb` |
| `skeleton-highlight` | `#374151` | `#f8fafc` |
| `focus-ring` | `#fb923c` | `#c2410c` |

La propuesta dark consolida los `gray-950/900/800` dominantes sin redisenar la
identidad actual. Light usa canvas slate claro, surfaces blancas, texto slate
oscuro y bordes visibles. `surface` y `surface-elevated` pueden compartir valor
en light porque borde y sombra expresan la elevacion; sus roles permanecen
separados para evolucion independiente.

## 5. Accesibilidad y contraste

Antes de implementar 95.4-B deben verificarse programaticamente las parejas
reales:

- texto normal: objetivo minimo 4.5:1;
- texto grande: 3:1;
- foco, bordes funcionales y componentes no textuales: 3:1 contra superficies
  adyacentes cuando WCAG lo requiera;
- `interactive-on-primary` sobre los tres estados de accion;
- cada `*-text` sobre su `*-surface`;
- textos primary/secondary/muted sobre canvas y surfaces permitidos;
- focus-ring sobre canvas, surface y controles;
- disabled debe seguir siendo legible y no depender solo de color/opacidad.

Un valor que no supere su pareja autorizada debe ajustarse antes de declararse
implementado. No se garantiza contraste por inspeccion visual ni por el nombre
de una escala Tailwind.

## 6. Marca y semantica funcional

`brand` identifica FeedGo y no significa automaticamente success, warning o
selected. `interactive-primary` puede comenzar con el mismo valor fisico, pero
es un rol independiente para permitir que acciones y marca evolucionen sin
acoplarse.

Los estados funcionales nunca toman su color de `brand`. Like activo puede
usar `danger-text` como acento semantico sin convertir todo danger en like.
Guardado activo puede usar warning/acento amarillo solo cuando su significado
visual actual se conserve y el contexto no comunique una advertencia falsa.

## 7. Contrato de `interactive-bubble`

`interactive-bubble` forma parte del contrato visual general de los botones de
accion FeedGo. La composicion contractual es:

```text
color o superficie semantica del boton + interactive-bubble = boton FeedGo
```

Esto no uniforma el color de los botones. Primary/brand conserva naranja;
danger, rojo; success, verde; warning, amber/yellow; selected, su rol; y
secondary, su superficie correspondiente. El efecto se adapta a cada rol y no
lo reemplaza.

El efecto burbuja se preserva en dark y light. No se modifican:

- DOM, mascara ni geometria;
- animaciones `likePop` y `saveBounce`;
- duraciones y transiciones;
- hover, focus, active o disabled;
- comportamiento de `InteraccionButton`;
- gradiente multicolor que constituye identidad visual.

Las variables locales existentes se mantienen como API interna del componente,
pero deben derivarse de roles globales:

- `--bubble-text` desde `text-secondary`;
- `--bubble-text-hover` desde `text-primary`;
- `--bubble-focus` desde `focus-ring`;
- variantes primary/danger/warning desde brand o el estado funcional
  correspondiente;
- bordes mediante mezcla transparente del acento semantico, no hex/RGBA
  repetidos en JSX.

Se justifican variables locales adicionales para adaptar el arte en light sin
convertirlas en tokens globales: opacidad de borde, opacidad del gradiente,
highlight y sombra interna. En light el borde/gradiente debe aumentar contraste
y el highlight no puede depender solo de blanco sobre superficie blanca. Esos
ajustes son cromaticos; no cambian el efecto ni su comportamiento.

`InteraccionButton` no debe seguir inyectando RGBA fisicos inline cuando se
migre: debe seleccionar una variante semantica, conservando icono, animacion y
eventos.

El owner visual comun futuro debe evolucionar desde la implementacion existente
`interactive-bubble` y reutilizar `InteraccionButton` donde su contrato de
interaccion corresponda. Una futura primitive `Button` podra componer esa unica
base visual, pero no duplicar su CSS, mascara o animacion ni convertir
`InteraccionButton` en owner de acciones para las que su API no sea adecuada.

La migracion posterior debe inventariar y clasificar por owner los aproximadamente
105 botones detectados, sin sustitucion automatica masiva. Cada caso debe
preservar accion, semantica HTML (`button` o `a`), tamano, accesibilidad y rol
cromatico. Los enlaces con apariencia de boton se evaluan por su semantica real;
la apariencia no autoriza cambiar el elemento.

El efecto no puede ocultar texto, degradar foco, impedir teclado ni ser la unica
senal de estado. Debe respetar `prefers-reduced-motion` cuando corresponda.

## 8. Branding de espacios

`color_fondo`, imagenes, portadas, historias y colores elegidos por comercios
permanecen fuera de los tokens globales. No se renombran como brand ni surface.

El tema solo provee contexto para contenido superpuesto, por ejemplo
`text-inverse`, bordes o scrims cuando sean necesarios. La legibilidad de un
color arbitrario del propietario requiere una estrategia especifica en la
migracion de Spaces, sin alterar el dato ni su ownership.

### 8.1 HistoriasViewer: superficie cubierta con apariencia fija

`HistoriasViewer` forma parte de la cobertura visual, pero su escenario
multimedia posee un contrato deliberadamente invariante entre light, dark y
system: fondo negro, progreso y texto claros, scrims, controles, geometria y
posiciones cinematograficas. No consume canvas/surface adaptativos ni `Button`
cuando estos pudieran alterar esa apariencia. Su owner local explicito debe
aislarlo de cambios indirectos del tema global, sin crear un segundo sistema de
temas. La media sigue siendo contenido; el viewer se clasifica como `Migrado -
apariencia fija validada` y requiere regresion visual, funcional y accesible.

## 9. Integracion CSS-first con Tailwind v4

La fuente fisica debe declararse una sola vez en CSS:

```css
html[data-theme="dark"] {
  --fg-color-canvas: #030712;
  /* resto de valores dark */
}

html[data-theme="light"] {
  --fg-color-canvas: #f8fafc;
  /* resto de valores light */
}
```

El CSS procesado por Tailwind v4 expondra aliases mediante `@theme inline`, por
ejemplo:

```css
@theme inline {
  --color-canvas: var(--fg-color-canvas);
}
```

Esto habilitara utilidades semanticas como `bg-canvas` y `text-primary` sin
`tailwind.config.js` ni cientos de `dark:`. Los nombres internos `--fg-*`
evitan colision entre la variable fuente y el alias de Tailwind.

Las clases deben escribirse de forma estatica y trazable. No se construiran
nombres de utilidad concatenando strings en runtime.

## 10. Theme-color y carga previa

`canvas` pasa a ser el owner visual de `theme-color`:

- dark candidato definitivo: `#030712`;
- light candidato definitivo: `#f8fafc`.

95.4-B debe evitar una segunda tabla JS. Como el kernel corre antes del CSS
principal de React, la fuente minima necesaria para canvas debe estar disponible
en un asset CSS local cargado antes del kernel. El kernel aplicara `data-theme`,
leera el custom property computado y sincronizara el meta. El resto de aliases
Tailwind puede permanecer en el CSS procesado.

El manifest conserva un fallback estatico gobernado por ETAPA 96; no puede
representar dinamicamente ambos temas.

## 11. Primitives justificables en bloques posteriores

La evidencia permite disenar, no implementar todavia:

- `Button`: variantes primary/secondary/danger, foco, disabled y loading con
  responsabilidad comun, compuesta sobre la unica base `interactive-bubble`;
- `FormControl` o familia coordinada Input/Select/Textarea: superficie, texto,
  placeholder, borde, focus, error y disabled compartidos;
- `Surface/Card`: canvas interno, borde y elevacion reutilizables;
- `Alert/Message`: conjuntos success/warning/danger y semantica accesible;
- `Skeleton`: base/highlight y reduced motion;
- `ModalSurface`: contenido visual sobre `ActiveLayer`, sin reemplazar su
  ownership de portal, foco, Escape y scroll;
- `EmptyState`: solo si el diseno demuestra estructura y accesibilidad comun,
  no por compartir un texto centrado.

No se justifica una primitive por el numero de tags HTML aislado; debe reducir
una responsabilidad visual repetida sin apropiarse de logica de feature.

## 12. Tokens deliberadamente excluidos

No se crean en este contrato:

- tokens por color fisico (`gray900`, `white`, `orange500`);
- tokens por pantalla o feature (`profile-card`, `agenda-modal`);
- un token por cada hover local;
- escalas numericas completas de marca o grises;
- tokens de `color_fondo` o branding de comercios;
- tokens de z-index, spacing, radius, tipografia o duracion sin auditoria
  especifica que demuestre necesidad;
- tokens para coordenadas, mapas, imagenes o contenido multimedia;
- tokens para cada stop del gradiente burbuja;
- tokens que codifiquen `dark` o `light` en el nombre;
- aliases duplicados con el mismo rol solo para imitar clases existentes.

La exclusion actual no declara que radius, shadow, spacing, typography o motion
deban permanecer dispersos para siempre. Si una auditoria posterior demuestra
que alguno expresa una decision visual global repetida, debera evaluarse su
centralizacion con alcance y owner explicitos. Hasta entonces no se anticipan
tokens ni se introducen nuevos hardcodes globales innecesarios durante la
migracion.

## 13. Riesgos de migracion

1. Sustituir colores por similitud fisica puede cambiar jerarquia o significado.
2. Migrar toda la aplicacion a la vez impediria aislar regresiones.
3. Un modo claro parcial puede dejar texto claro sobre superficies claras.
4. Funcionales sin validacion por pareja pueden perder contraste.
5. Reemplazar `interactive-bubble` por Button eliminaria identidad y
   comportamiento aprobado.
6. Convertir variables locales de arte en tokens globales inflaria el contrato.
7. Mezclar branding de espacios con tema puede alterar datos del propietario.
8. Duplicar valores de canvas entre CSS y JS desincronizaria `theme-color`.
9. Clases Tailwind generadas dinamicamente pueden ser omitidas en build.
10. Crear primitives antes de validar tokens consolidaria una API incorrecta.
11. Aplicar el efecto a 105 botones mediante reemplazo masivo puede cambiar
    semantica HTML, dimensiones, acciones o accesibilidad.

## 14. Gate para 95.4-B

95.4-A queda cerrado documentalmente. 95.4-B debe implementar exclusivamente
la fuente CSS de tokens y sus aliases Tailwind, sin migracion masiva:

1. crear el asset/fuente unica bajo el owner `core/theme` o su frontera de
   bootstrap documentada;
2. declarar los valores dark/light aprobados;
3. exponer aliases CSS-first estaticos a Tailwind v4;
4. alinear fondo anti-flash y `theme-color` con `canvas` sin tabla JS duplicada;
5. adaptar solamente las variables cromaticas de `interactive-bubble`,
   preservando comportamiento y efecto;
6. agregar tests de presencia, simetria dark/light, ausencia de tokens fisicos,
   contraste de parejas y build de utilidades semanticas;
7. no migrar pantallas ni crear primitives; esos consumidores requieren bloques
   posteriores aprobados.

La implementacion de 95.4-B debe respetar la direccion de dependencias de la
seccion 2.1 y evitar APIs o valores que obliguen a los futuros consumidores a
conocer colores fisicos. Este requisito no amplia sus tareas autorizadas.

El owner compartido de botones debe disenarse e implementarse en un bloque
posterior de componentes compartidos dentro de 95.4. La adopcion controlada por
owner y pantalla corresponde a 95.5. Ninguna de ambas tareas forma parte de
95.4-B.

## 15. Evidencia de implementacion 95.4-B

Estado al cerrar el bloque: implementado y validado. Su evidencia habilito el
diseno posterior de 95.4-C sin migrar pantallas.

- `frontend/public/theme-tokens.css` es la fuente fisica unica, local y previa
  a React para los 38 tokens aprobados en dark y light;
- `frontend/src/core/theme/tokens.css` expone exclusivamente aliases CSS-first
  mediante `@theme inline`, sin duplicar valores;
- `theme-bootstrap.css` obtiene el fondo inicial desde
  `--fg-color-canvas` y el kernel obtiene del mismo token el `theme-color`;
- el orden productivo es tokens, fondo anti-flash, kernel y luego entrypoint
  React; no se agregaron scripts o estilos inline;
- `interactive-bubble` deriva texto, borde, focus, highlights y variantes de
  roles semanticos sin cambiar DOM, mascara, geometria, animaciones, timings ni
  eventos;
- `InteraccionButton` dejo de inyectar RGBA locales y reutiliza las variantes
  danger/warning existentes sin migrar otros botones;
- los tests verifican simetria, aliases, contraste, canvas unico, CSP,
  ausencia de configuracion Tailwind paralela y preservacion del efecto;
- validacion: 52 tests frontend correctos, lint sin errores y build productivo
  correcto;
- no se migraron pantallas, no se crearon primitives y no se modifico branding
  de espacios.

El gate resultante para 95.4-C exigio auditar y definir la base compartida de
botones/primitives comenzando por la composicion entre `interactive-bubble`,
`InteraccionButton` y un futuro `Button`, sin migracion masiva. Su evidencia
vigente se registra en la seccion siguiente.

## 16. Evidencia de implementacion 95.4-C

Estado: implementado y validado. No se migraron pantallas ni consumidores y no
se inicio 95.5.

Owner: `frontend/src/shared/components/primitives/`.

Primitives justificadas e implementadas:

- `Button`: elemento `button` nativo, props y eventos passthrough, variantes
  primary, secondary, danger, success, warning y ghost, opcion iconografica,
  disabled accesible y composicion unica sobre `interactive-bubble`;
- `Surface`: infraestructura visual base, subtle y elevated, con elemento
  semantico configurable y sin logica de dominio;
- `FormControl`, `Input`, `Select` y `Textarea`: apariencia, foco, disabled y
  error compartidos, sin validacion ni ownership de formularios;
- `Alert`: success, warning y danger sin imponer live region o estado vacio;
- `Skeleton`: color semantico, sin layout impuesto y con reduced motion.

Responsabilidades preservadas:

- `InteraccionButton` continua siendo owner funcional de like/guardar y sus
  animaciones; no fue reemplazado por `Button`;
- el CSS, mascara, gradiente y comportamiento de `interactive-bubble` siguen en
  su unica implementacion global;
- `ActiveLayer` continua siendo el unico owner de portal, foco, Escape,
  backdrop y scroll lock. `ModalSurface` fue diferido hasta contar con un
  contrato visual de modal suficientemente comun;
- loading de Button fue diferido porque no existe contrato compartido de
  contenido/indicador y no corresponde inventar un spinner;
- enlaces con apariencia de boton permanecen fuera de `Button`; su semantica
  debe evaluarse durante la migracion sin convertir `a` y `button`
  automaticamente.

Validacion:

- 15 tests especificos y 61 tests frontend globales correctos;
- lint sin errores y build productivo correcto;
- primitives sin colores fisicos, `dark:`, lectura de tema ni logica de
  dominio;
- ningun consumidor de pantalla fue modificado.

Siguiente bloque sujeto a aprobacion: 95.4-D - validacion final, hardening de la
API compartida y cierre tecnico de 95.4, sin migrar consumidores. El selector
visible y la primera adopcion de pantalla permanecen en 95.5-A.

## 17. Cierre tecnico de 95.4

Estado: 95.4-D completado y Sprint 95.4 cerrado tecnicamente. El resultado
habilita la adopcion controlada en 95.5 sin autorizar migraciones dentro de
este cierre.

La confrontacion final entre los contratos de tema, inventario, tokens y la
implementacion confirma:

- una unica fuente fisica para los 38 roles, con contratos dark/light
  simetricos, aliases Tailwind CSS-first, contraste automatizado y canvas como
  owner de anti-flash y `theme-color`;
- `Button` conserva semantica nativa, `type="button"` por defecto, props y
  eventos passthrough, disabled, variantes justificadas y composicion unica de
  `interactive-bubble`; `iconOnly` exige `aria-label` o `aria-labelledby`;
- `Surface`, controles de formulario, `Alert` y `Skeleton` limitan su ownership
  a apariencia y accesibilidad representable, sin logica de dominio ni tema
  manual;
- `InteraccionButton` continua siendo owner funcional de like/guardar y
  `ActiveLayer` conserva portal, foco, Escape, backdrop y scroll lock;
- la API publica exporta solo las primitives aprobadas y no expone helpers,
  tablas de variantes ni detalles internos;
- no se agregaron dependencias, ciclos ni configuracion Tailwind paralela; la
  API compartida incorporo un crecimiento acotado del bundle, sin duplicar
  implementaciones ni incorporar librerias;
- se corrigio unicamente el contrato accesible de `iconOnly`, el formato de
  `Skeleton` y constantes internas sin necesidad de inmutabilidad runtime;
- validacion final: 63 tests frontend correctos, lint sin errores, build
  productivo correcto y `git diff --check` correcto.

No se migraron Registro, Editar perfil ni las instancias existentes de
botones. El siguiente sprint oficial es 95.5 - Migracion controlada de
pantallas criticas. Su primer bloque, 95.5-A, debe implementar el selector
visible de apariencia exclusivamente en `Perfil -> Editar perfil`, consumiendo
`preference` y `setPreference(...)`.

## 18. Gate global de cobertura visual

ETAPA 95 no puede cerrarse con una experiencia parcialmente tematica. La
migracion continua ejecutandose por bloques pequenos durante 95.5, pero su
resultado acumulado debe cubrir todas las superficies de uso normal en light y
dark:

- pantallas, layouts y navegacion;
- formularios, cards y superficies compartidas;
- modales, overlays y capas;
- estados empty, error, success y loading;
- loaders y skeletons;
- botones y controles interactivos.

La mezcla transitoria entre superficies migradas y pendientes es admisible
solo mientras 95.5 permanezca abierto. Antes de cerrar 95.5 debe existir una
matriz exhaustiva derivada del inventario real con, como minimo:

| Superficie/owner | Estado | Evidencia | Excepcion o pendiente |
| --- | --- | --- | --- |
| cada pantalla, layout o componente compartido real | `migrado`, `excepcion justificada` o `pendiente` | tokens/primitives y validacion aplicable | fundamento y owner de resolucion |

El estado `pendiente` bloquea el cierre de 95.5. Una excepcion solo es valida
para branding de contenido, mapa/proveedor externo, media o una necesidad de
dominio documentada. No son excepciones una clase heredada, un header oscuro
en light, un canvas incompatible, un overlay hardcodeado o falta de tiempo.

### 18.1 Botones y contraste

Una superficie clara con texto claro, foco insuficiente o efecto ilegible es
un defecto del contrato visual. Los roles primary, danger, success, warning,
secondary y selected conservan su significado; texto, borde, focus, highlight
e `interactive-bubble` deben alcanzar contraste mediante tokens y primitives.

Si el defecto se reproduce entre consumidores, debe corregirse primero en
tokens o `Button`. No se autorizan clases fisicas locales pantalla por pantalla
para compensar un defecto del owner compartido.

### 18.2 QA visual de cierre

Despues de completar los bloques de 95.5 debe ejecutarse una pasada global en
light, dark y cambio runtime que cubra contraste, botones, textos, formularios,
navegacion, layouts, overlays, cards, skeletons, responsive y estados de
error/empty/loading. Los defectos se resuelven siguiendo:

```text
tokens -> primitives -> componente compartido -> pantalla
```

Este gate no reabre 95.5-A ni 95.5-B y no autoriza migracion masiva. Obliga a
que los bloques restantes, en conjunto, clasifiquen y cubran todas las
superficies antes del cierre de 95.5 y de ETAPA 95.

La matriz acumulada y sus evidencias viven en
`23_FRONTEND_VISUAL_COVERAGE.md`. Ese documento registra cobertura sin
redefinir este contrato.
