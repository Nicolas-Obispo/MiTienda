# Expediente Legal, Privacidad y Seguridad del Sistema de Ubicacion

Estado del documento: Expediente Tecnico Oficial de FeedGo v1.0.
Version: 1.0.
Categoria: Documento tecnico de gate.
Nivel de autoridad: Tecnico subordinado a `docs/15_LEGAL_AND_OPERATIONAL.md`.
Documento dueno: `docs/19_LOCATION_LEGAL_GATE.md`.
Responsable funcional: Producto, Ingenieria, Seguridad, Compliance, Legal y
Direccion, dentro de las competencias definidas por el Sistema de Gobierno.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `03_SEARCH.md`, `04_CURRENT_STAGE.md`,
`05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`, `08_ENGINEERING_PRINCIPLES.md`,
`15_LEGAL_AND_OPERATIONAL.md`.
Cuando debe consultarse: antes de disenar, implementar, ampliar, persistir o
lanzar funciones de ubicacion precisa, geocoding, publicacion de domicilios,
ranking geografico, permisos de geolocalizacion o cambios sustanciales en los
documentos publicos y sus aceptaciones.

## 1. Autoridad, finalidad y limites

Este expediente aplica el marco obligatorio de
`docs/15_LEGAL_AND_OPERATIONAL.md` al Sistema de Ubicacion de ETAPA 95.1.

No reemplaza:

- el Sistema de Gobierno;
- Terminos y Condiciones;
- Politica de Privacidad;
- avisos contextuales;
- contratos o politicas de proveedores;
- revision profesional legal;
- aprobaciones reales de los responsables aplicables.

Direccion confirmo que la aprobacion legal necesaria para avanzar con el
Sistema de Ubicacion ya existe. El expediente registra esa confirmacion sin
inventar identidad profesional, matricula, firma, fecha de firma ni documento
firmado. Esos metadatos permanecen pendientes de formalizacion y trazabilidad.

## 2. Estado y resolucion vigente

Resolucion actual: `GO condicionado` para disenar e implementar ETAPA 95.1.

Fundamento:

1. Direccion confirma que la aprobacion legal necesaria para el Sistema de
   Ubicacion ya existe;
2. Direccion aprueba el contrato funcional y habilita su implementacion;
3. las matrices identifican los controles de Seguridad que deben implementarse
   y validarse dentro de 95.1;
4. las condiciones administrativas de formalizacion no impiden el desarrollo;
5. Terminos, Politica de Privacidad y procedimientos operativos definitivos
   permanecen como gate de activacion publica y lanzamiento;
6. la integracion productiva de geocoding queda condicionada a un proveedor y
   arquitectura compatibles con sus politicas y con este expediente.

El `GO condicionado` no autoriza autocomplete contra Nominatim publico, envio
de domicilios privados a un servicio incompatible, exposicion frontend de
datos privados ni lanzamiento con documentos publicos incompletos.

## 3. Alcance evaluado

Incluye:

- ubicacion efimera del usuario que busca;
- territorio manual de busqueda;
- ubicacion precisa persistida del espacio;
- direccion publica o privada del espacio;
- distancia y ranking geografico;
- forward y reverse geocoding;
- proveedor cartografico y de geocoding;
- registro, documentos publicos y evidencia de aceptacion;
- rectificacion, revocacion, eliminacion y cambios documentales.

Excluye:

- seguimiento en segundo plano;
- historial de recorridos;
- mapas offline;
- geolocalizacion nativa futura;
- Web Push, Background Sync o mutaciones offline;
- implementacion de ETAPA 96.

## 4. Evaluacion de impacto

### 4.1 Necesidad de producto

FeedGo es un buscador local. La ubicacion territorial permite determinar el
ambito inicial de Search y Discovery. La posicion precisa permite calcular
cercania cuando la ubicacion del espacio es publica.

Todo espacio nuevo debera declarar provincia, ciudad, direccion y coordenadas
validas confirmadas. La necesidad interna no implica publicar el domicilio.

### 4.2 Personas y recursos afectados

- usuarios generales que habilitan ubicacion durante el uso;
- propietarios que declaran la ubicacion de un espacio;
- personas cuyo domicilio particular coincide con la ubicacion del espacio;
- visitantes que consultan resultados y perfiles publicos;
- usuarios existentes sin evidencia historica o ubicacion valida completa.

### 4.3 Impactos principales

- acceso contextual a ubicacion precisa del dispositivo;
- persistencia de direccion y coordenadas del espacio;
- transmision potencial de consultas o coordenadas a un proveedor externo;
- posible exposicion directa o indirecta de un domicilio;
- inferencia por distancia, marcador, ruta, URL o ranking observable;
- necesidad de rectificacion y supresion;
- dependencia operativa de servicios comunitarios externos.

## 5. Tratamientos identificados

| Tratamiento | Titular o recurso | Datos | Finalidad | Persistencia | Publicacion | Estado del fundamento |
| --- | --- | --- | --- | --- | --- | --- |
| Ubicacion actual de busqueda | Usuario general | latitud, longitud, precision, timestamp tecnico | determinar territorio, distancia y cercania | memoria de sesion; sin historial | nunca | Aprobacion legal confirmada; permiso tecnico obligatorio |
| Territorio manual | Usuario general | ciudad, provincia, pais | fallback y busqueda local | cache funcional segun diseno; no presentarlo como GPS | contexto visible | Pendiente de documentar retencion |
| Ubicacion interna del espacio | Espacio/propietario | direccion, ciudad, provincia, pais, latitud, longitud | Search, Discovery, Indexer y relevancia territorial | persistente | condicionada por visibilidad | Aprobacion legal confirmada; controles tecnicos condicionantes |
| Visibilidad del espacio | Espacio/propietario | opcion publica/privada | controlar publicacion | persistente | publica solo la decision necesaria | Campo inexistente; implementacion pendiente |
| Ubicacion publica | Espacio publico | direccion, coordenadas derivadas, distancia, marcador, maps_url | informar ubicacion y como llegar | segun datos del espacio | si | Decidir alcance exacto en documentos publicos |
| Ubicacion privada | Espacio privado | ubicacion exacta interna; ciudad publica | busqueda local sin publicar domicilio | persistente internamente | solo ciudad segura | Requiere proyeccion backend y controles anti-inferencia |
| Forward geocoding | Propietario | consulta de direccion y territorio; metadatos de red | proponer coordenadas | FeedGo no persiste la consulta ni mantiene cache; Geoapify declara retencion operativa | no | Adapter Geoapify implementado; activacion pendiente de key, plan y formalizacion |
| Reverse geocoding | Propietario | coordenadas precisas; metadatos de red | proponer direccion | propuesta temporal; FeedGo no mantiene cache | no | Adapter Geoapify implementado; activacion pendiente de key, plan y formalizacion |
| Evidencia de documentos | Usuario registrado | usuario, tipo, version, fecha, canal, metodo, estado y referencia | demostrar aceptacion | persistente y separada | nunca | Implementado; textos publicos reales pendientes |

La formalizacion de retencion y eliminacion definitivas permanece pendiente
para los documentos y procedimientos operativos. No se autoriza conservar historial de posiciones, consultas crudas,
IP completa, user-agent completo ni payloads de geocoding sin justificacion.

## 6. Matriz Legal y Compliance

| Tema | Regla o riesgo | Control requerido | Responsable segun Gobierno | Estado |
| --- | --- | --- | --- | --- |
| Finalidad | No usar datos para fines incompatibles | informar busqueda local, cercania y publicacion elegida | Producto, Compliance, Legal | Aprobacion legal confirmada; formalizacion pendiente |
| Necesidad | Ubicacion precisa no debe recolectarse por conveniencia | separar territorio manual, ubicacion efimera y persistida | Producto, Legal | Aprobada para implementacion |
| Informacion previa | Informar finalidad, obligatoriedad, destinatarios y derechos | Politica completa y avisos contextuales | Legal, Compliance | Condicion de activacion publica y lanzamiento |
| Fundamento | Aceptacion general no resuelve todos los tratamientos | matriz de bases juridicas por tratamiento | Legal | Aprobacion confirmada; evidencia detallada pendiente de formalizacion |
| Permiso GPS | Aceptar documentos no concede acceso al dispositivo | permiso nativo contextual, revocable y con fallback | Ingenieria, Producto | Implementado y validado en 95.1-F |
| Domicilio privado | Direccion comercial puede ser domicilio personal | opcion de privacidad y proyeccion backend | Legal, Seguridad, Direccion | Aprobado; controles tecnicos dentro de 95.1 |
| Publicacion por defecto | La ubicacion interna y su publicacion son independientes | nuevos espacios publicos por defecto, con control visible para desactivar | Legal, Producto, Direccion | Aprobado expresamente por Direccion |
| Proveedor | Direccion o coordenadas pueden salir a un tercero | matriz de proveedor, pais, rol, contrato, retencion y salida | Compliance, Legal, Seguridad | Bloquea la integracion productiva incompatible, no el resto de 95.1 |
| Derechos | Acceso, rectificacion, actualizacion y supresion | canal y procedimiento operativo | Legal, Compliance, Operacion | Pendiente antes de lanzamiento |
| Cambios documentales | Una aceptacion historica no cubre toda finalidad futura | versionado, clasificacion material y reaceptacion | Legal, Compliance | Owner de version implementado; clasificacion/reaceptacion pendiente antes de lanzamiento |
| Evidencia | No inventar aceptaciones retroactivas | conservar evidencia minima existente | Compliance, Ingenieria | Implementado para registro; no se inventaron evidencias historicas |

## 7. Matriz de Seguridad

| Riesgo | Superficie | Control minimo | Dueno natural | Estado |
| --- | --- | --- | --- | --- |
| Exposicion de domicilio privado | respuestas publicas | proyeccion backend sin direccion, coordenadas, distancia, maps_url ni marcador | Backend de Comercios | Implementado y validado en 95.1-B |
| Bypass de privacidad frontend | API publica | privacidad y autorizacion decididas en backend | Backend de Comercios | Implementado y validado en 95.1-B |
| Coordenadas invalidas | create/update | rangos, finitud y presencia conjunta | Schemas/servicio backend | Implementado y validado en 95.1-A |
| Cambio no autorizado | mutaciones | ownership `Usuario -> Comercio` | Backend | Implementado y cubierto por suites de ownership/autorizacion |
| Triangulacion por ranking | Search/Discovery | banda interna, orden estable, sin score geografico publico, rate limiting | Backend Search/Seguridad | Banda, orden y no exposicion validados en 95.1-E; rate limiting general queda como condicion operativa |
| Abuso del proveedor | geocoding | limite global, cache permitida, consultas explicitas y proveedor configurable | Integracion geografica backend | Adapter Geoapify y limite local configurable implementados en 95.1-D2; monitoreo de cuota pendiente |
| Respuesta asincrona tardia | selector | cancelar solicitudes o ignorar respuestas obsoletas por revision | Frontend selector | Implementado y validado en 95.1-C |
| Filtracion en logs | frontend/backend/proxy | no registrar consultas, coordenadas o payloads crudos | Observabilidad/Seguridad | Geocoding sin payloads sensibles y SearchEvent sin coordenadas validados; infraestructura/proxy productivos pendientes |
| Caché cruzada | Search/API/PWA futura | claves territoriales y aislamiento de respuestas privadas | Search/Cache/Seguridad | Query keys territoriales/revision y proyeccion backend validadas en 95.1-B/E/F |
| Enumeracion | endpoints publicos | rate limiting y contratos sin derivados privados | Backend/Seguridad | Contratos sin derivados privados validados; rate limiting general pendiente antes de produccion |

La banda interna de 1 km es una mitigacion inicial de producto, no una garantia
de anonimato ni una exigencia externa. Queda autorizada para implementacion
condicionada a tests de no exposicion, orden estable, rate limiting y validacion
final de Seguridad.

## 8. Proveedor cartografico y geocoding

### 8.1 Situacion auditada y correccion 95.1-D

Al iniciar 95.1-D, `frontend/src/shared/components/LocationPicker.jsx` llamaba
directamente a `https://nominatim.openstreetmap.org/search` y no existia reverse
geocoding. El endpoint y el payload del proveedor estaban fijados en el cliente.

95.1-D elimina esa llamada. El frontend consume ahora contratos FeedGo de
forward y reverse mediante un service propio. El backend posee el modulo de
geocoding, validacion, normalizacion, errores sanitizados e interfaz de proveedor
reemplazable.

El proveedor queda deshabilitado por defecto: no se implementa ni activa un
adaptador al servidor publico de Nominatim porque la creacion de espacios puede
transmitir domicilios personales o confidenciales. Forward y reverse productivos
requieren un proveedor o instancia compatible evaluado conforme a este gate.

El mapa continua utilizando tiles de OpenStreetMap con atribucion; ese consumo
es independiente del contrato de geocoding.

### 8.2 Politica oficial relevante

La politica del servidor publico de Nominatim exige, entre otras condiciones:

- maximo absoluto de una solicitud por segundo para toda la aplicacion;
- identificacion valida de la aplicacion;
- atribucion;
- busquedas directas iniciadas por el usuario;
- cache de consultas repetidas;
- capacidad de cambiar de servicio sin actualizar la aplicacion;
- no implementar autocomplete cliente;
- no realizar consultas sistematicas;
- no enviar datos personales o material confidencial.

### 8.3 Conclusion

La busqueda manual auditada podia ser tecnicamente tolerada para uso moderado,
pero no demostraba todos los controles y no era una base aprobada para
domicilios privados. La llamada fue retirada en 95.1-D. No se autoriza
incorporar autocomplete ni reverse geocoding frecuente sobre el servidor
publico.

Un proxy puede aportar rate limiting, cache y conmutacion, pero no elimina la
transmision al proveedor ni corrige por si solo la restriccion de privacidad.

Antes de activar geocoding productivo debe decidirse entre:

1. proveedor con condiciones compatibles y contrato evaluado;
2. instancia controlada;
3. alcance temporal sin envio de domicilios privados al servicio publico.

La seleccion posterior de un proveedor debe quedar registrada y condicionada a
sus controles tecnicos, comerciales, de privacidad y atribucion.

### 8.4 Seleccion controlada de Geoapify - 95.1-D2

Direccion selecciona Geoapify como candidato principal sin convertirlo en
contrato del dominio. El adapter backend utiliza los endpoints EU de forward y
reverse y permanece detras de `GeocodingProvider`.

Datos enviados por operacion:

- forward: direccion consultada, ciudad, provincia, pais, idioma y limite;
- reverse: latitud, longitud, idioma y limite;
- autenticacion tecnica: API key backend;
- no se envian usuario, email, comercio completo, IDs internos ni tokens FeedGo.

Condiciones oficiales verificadas:

- la API key es obligatoria y debe conservarse en backend;
- Geocoding y Reverse Geocoding consumen un credito por request;
- el plan gratuito publica 3000 creditos diarios y hasta 5 requests por segundo;
- los planes y limites superiores dependen de la suscripcion;
- el almacenamiento de resultados esta permitido conservando atribuciones;
- se exige atribucion a OpenStreetMap y, en plan gratuito, a Geoapify;
- la politica de privacidad declara retencion de body, headers, IP y timestamp
  de cada request, normalmente no mayor a 24 horas para requests exitosos;
- el DPA informa que detalles excepcionales pueden conservarse hasta dos meses
  por fraude o actividad sospechosa y que `api-eu.geoapify.com` mantiene el
  procesamiento de API dentro de la Union Europea.

Controles implementados:

- `GEOAPIFY_API_KEY` exclusivamente por environment backend;
- inicio normal y respuesta `503` segura cuando la key falta;
- timeout configurable y errores 4xx, 5xx y 429 sanitizados;
- limite conservador configurable, por defecto 5 RPS por proceso;
- sin cache de consultas o coordenadas sensibles;
- atribucion generica devuelta por contrato FeedGo y renderizada por el selector;
- tipo y confianza normalizados a conceptos neutrales de precision y confianza;
- ninguna credencial, URL o parametro Geoapify llega a `LocationPicker`.

En 95.1-D2 no existia API key y no se registraron resultados inventados. La
credencial local fue incorporada posteriormente y la evidencia real se registra
en 95.1-D3.

## 9. Fuentes oficiales verificadas

- W3C Geolocation: https://www.w3.org/TR/geolocation/
- MDN `getCurrentPosition`: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/getCurrentPosition
- Politica de Nominatim: https://operations.osmfoundation.org/policies/nominatim/
- API Search de Nominatim: https://nominatim.org/release-docs/latest/api/Search/
- API Reverse de Nominatim: https://nominatim.org/release-docs/latest/api/Reverse/
- Politica de privacidad de OSMF: https://osmfoundation.org/wiki/Privacy_Policy
- Politica de tiles OSMF: https://operations.osmfoundation.org/policies/tiles/
- Geoapify Forward Geocoding:
  https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/
- Geoapify Reverse Geocoding:
  https://apidocs.geoapify.com/docs/geocoding/reverse-geocoding/
- Geoapify Pricing: https://www.geoapify.com/pricing/
- Geoapify Terms: https://www.geoapify.com/terms-and-conditions/
- Geoapify Privacy: https://www.geoapify.com/privacy-policy/
- Geoapify DPA: https://www.geoapify.com/data-processing-agreement/
- Ley argentina 25.326, texto actualizado:
  https://www.argentina.gob.ar/normativa/nacional/ley-25326-64790/actualizacion

Las recomendaciones de W3C para receptores de ubicacion son consideraciones de
privacidad y no sustituyen la legislacion argentina. La aplicacion concreta de
la Ley 25.326 requiere revision profesional.

## 10. Contrato de ubicacion sujeto al gate

### 10.1 Usuario que busca

- la ubicacion actual es efimera y se mantiene en memoria;
- se solicita solo ante una funcion geografica contextual;
- no se crea historial ni seguimiento en segundo plano;
- aceptar Terminos y Politica no concede permiso tecnico;
- el permiso se obtiene mediante el navegador o plataforma;
- rechazo o revocacion no elimina la cuenta ni bloquea el uso general;
- debe existir seleccion territorial manual y visible;
- una ciudad manual nunca se presenta como posicion GPS;
- territorio inicial: ciudad, provincia y pais;
- perfil del usuario: fallback explicito, no sustituto de una lectura valida;
- ampliacion fuera de ciudad: accion explicita, primero 50 km y luego hasta
  100 km;
- frescura territorial propuesta: cinco minutos con precision de hasta 1.000 m;
- frescura de distancia propuesta: 60 segundos con precision de hasta 100 m;
- no hay `watchPosition` permanente.

Texto contextual aprobado como base de implementacion, sujeto a validacion UX:

> FeedGo usa tu ubicacion mientras utilizas la app para determinar tu zona,
> mostrarte resultados cercanos y calcular distancias. No guardamos un historial
> de tus desplazamientos. Tambien puedes elegir una ciudad manualmente.

### 10.2 Propietario que crea o edita un espacio

- todo espacio nuevo declara provincia, ciudad, direccion y coordenadas validas;
- la propuesta direccion-coordenadas permanece temporal hasta confirmacion;
- el proveedor propone y el usuario confirma;
- cancelar nunca modifica la ubicacion persistida;
- guardar requiere confirmacion y validacion backend;
- ubicacion interna y publicacion son decisiones separadas;
- un espacio privado sigue participando de Search, Discovery e Indexer;
- privacidad no equivale a ubicacion inexistente o invalida.

Textos contextuales aprobados como base de implementacion, sujetos a validacion
UX:

> FeedGo necesita la ubicacion real desde la que funciona tu espacio para
> incluirlo correctamente en las busquedas locales.

> ¿No atiendes al publico alli? Puedes mantener privada la direccion. Los
> usuarios solo veran tu ciudad.

### 10.3 Presentacion publica

Espacio publico:

- conserva direccion, marcador, `maps_url`, Como llegar y distancia precisa;
- preserva calculo y formato existentes cuando ya cumplen el contrato.

Espacio privado:

- muestra solo ciudad, o ciudad y provincia cuando sea necesario desambiguar;
- no devuelve direccion, coordenadas, distancia, marcador, `maps_url`, ruta ni
  derivados precisos;
- puede usar una banda interna de cercania de 1 km, subordinada a relevancia
  semantica, sin persistirla ni exponerla.

Espacio historico sin ubicacion valida:

- constituye un estado distinto;
- no debe presentarse como espacio privado;
- requiere estrategia de regularizacion antes de exigir el nuevo contrato.

## 11. Registro y documentos publicos: estado real

### 11.1 Controles existentes

- el formulario presenta checkboxes separados y desmarcados;
- frontend bloquea el submit si falta alguno;
- backend exige literalmente `True` para ambas aceptaciones;
- usuario y evidencias se crean en una misma transaccion;
- existe `usuarios_documentos_aceptaciones` como dueno persistente separado;
- se registran usuario, tipo, version, fecha, canal, metodo, estado y referencia;
- existen tests backend para rechazo, atomicidad, evidencia y unicidad;
- Explorar y perfiles publicos pueden utilizarse sin cuenta mediante rutas de
  invitado, aunque hoy existe una redireccion temporal despues de cinco minutos.

### 11.2 Gaps obligatorios

- `/terminos-y-condiciones` y `/politica-de-privacidad` no tienen rutas ni
  paginas implementadas; los enlaces caen en el fallback general;
- no existen textos publicos completos que respalden las referencias `v1`;
- `documento_referencia` es una referencia logica, no evidencia de un contenido
  legal real aprobado;
- falta incorporar la referencia formal de la aprobacion legal ya confirmada y
  completar el versionado de los textos publicos;
- falta estrategia de reaceptacion;
- falta tratamiento de cuentas anteriores sin evidencia;
- falta comprobar que la navegacion a documentos no pierda el formulario;
- falta accesibilidad, impresion/descarga o mecanismo equivalente de consulta;
- la continuidad indefinida de Explorar sin registro es una decision de
  producto pendiente porque el router actualmente limita la sesion invitada a
  cinco minutos.

No se necesita otra tabla para la evidencia minima actual.

## 12. Flujo recomendado de registro

1. El usuario puede abrir Terminos y Politica completos antes de aceptar.
2. Cada documento mantiene identidad, version y fecha de vigencia propias.
3. Los checkboxes comienzan desmarcados y permanecen separados.
4. Sin ambas aceptaciones no se envia ni crea la cuenta.
5. Backend valida la version vigente y las dos aceptaciones.
6. Usuario y evidencias se persisten atomicamente.
7. La respuesta no expone el historial de aceptaciones.
8. El usuario puede continuar en Explorar sin registrarse conforme a la politica
   de acceso invitado que Producto apruebe.

La aceptacion de la Politica registra que el usuario recibio y acepto el
documento aplicable cuando el fundamento lo requiera; no debe presentarse como
consentimiento universal para todo tratamiento futuro.

## 13. Permiso tecnico de geolocalizacion

1. No solicitar GPS por crear una cuenta.
2. Mostrar explicacion breve al pedir resultados cercanos, distancia o territorio
   automatico.
3. Invocar el mecanismo nativo del navegador solamente tras una accion
   contextual.
4. Reutilizar el estado y lecturas aceptables conforme a las capacidades del
   navegador y la politica de frescura.
5. Ante denegacion, timeout, indisponibilidad o precision insuficiente, ofrecer
   ciudad manual.
6. No insistir repetidamente ante una decision conocida.
7. La revocacion detiene futuras lecturas y elimina el estado efimero en memoria;
   no elimina cuenta, espacios ni evidencia legal.

## 14. Cambios materiales, revocacion y derechos

### 14.1 Cambios documentales

- todo texto mantiene version identificable;
- Legal determina si el cambio es material;
- un cambio material o una finalidad nueva exige nueva evaluacion;
- cuando corresponda, debe solicitarse reaceptacion antes de la funcion afectada;
- no se altera ni inventa la evidencia historica;
- cambios editoriales no materiales pueden mantener version solo si Legal lo
  aprueba y existe trazabilidad.

### 14.2 Revocacion de geolocalizacion

- se respeta el estado del navegador;
- no se vuelve a solicitar automaticamente;
- se ofrece territorio manual;
- se invalidan distancias dependientes de una lectura que ya no deba usarse;
- no se interpreta como revocacion de Terminos o Politica.

### 14.3 Acceso, rectificacion, actualizacion y supresion

Debe existir antes del lanzamiento:

- identidad y contacto del responsable;
- canal verificable de solicitudes;
- verificacion proporcional de identidad;
- procedimiento y plazos aplicables;
- rectificacion de ubicacion del espacio;
- eliminacion o disociacion segun fundamento, obligaciones y backups;
- trazabilidad minima de solicitud y respuesta;
- explicacion del tratamiento de datos en backups.

## 15. Estructura requerida de Terminos y Condiciones

El texto definitivo debe redactarse y aprobarse separadamente. Estructura
minima propuesta:

1. identidad y datos del responsable;
2. objeto, alcance y definiciones;
3. acceso como invitado y creacion de cuenta;
4. requisitos de edad y capacidad;
5. cuenta, credenciales y seguridad;
6. roles de usuario y administracion de espacios;
7. contenido aportado, licencias y responsabilidades;
8. datos de espacios, veracidad y ubicacion declarada;
9. visibilidad publica o privada de la direccion;
10. Search, Discovery, ranking y limitaciones informativas;
11. conductas prohibidas, denuncias y moderacion;
12. proveedores y servicios externos;
13. disponibilidad, cambios y continuidad del servicio;
14. propiedad intelectual;
15. baja, suspension y eliminacion de cuenta;
16. limitacion de responsabilidad conforme a derecho aplicable;
17. modificaciones y mecanismo de notificacion/reaceptacion;
18. ley aplicable, jurisdiccion y canales de contacto.

Datos institucionales desconocidos deben permanecer como `[PENDIENTE]` y no
publicarse como texto definitivo.

## 16. Estructura requerida de Politica de Privacidad

Debe permanecer diferenciada de los Terminos. Estructura minima propuesta:

1. identidad, domicilio y contacto del responsable;
2. alcance y definiciones;
3. categorias de titulares y datos;
4. finalidades y fundamentos por tratamiento;
5. datos de cuenta y autenticacion;
6. datos de perfil y contenido;
7. ubicacion efimera del usuario;
8. ubicacion persistida y visibilidad del espacio;
9. Search, Discovery, ranking, Indexer y distancia;
10. cookies, almacenamiento local, analytics y logs reales;
11. proveedores, destinatarios, paises y transferencias;
12. conservación, bloqueo, eliminacion y backups;
13. medidas de seguridad y limites razonables;
14. derechos de acceso, rectificacion, actualizacion y supresion;
15. revocacion de permisos y consentimientos opcionales;
16. menores de edad;
17. cambios de politica, versiones y reaceptacion;
18. autoridad de aplicacion y contacto de privacidad.

La politica debe describir solo tratamientos reales y aprobados. No debe
afirmar anonimato, cifrado, plazos o certificaciones no demostrados.

## 17. Datos legales y operativos pendientes

- identidad o razon social del responsable;
- domicilio legal;
- correo o canal de privacidad;
- contacto de soporte;
- identidad y evidencia formal del responsable legal que emitio la aprobacion
  confirmada por Direccion;
- responsables reales de Seguridad, Compliance y Direccion;
- edad minima aplicable;
- fundamento juridico de cada tratamiento;
- plazos de retencion;
- procedimiento de derechos y verificacion de identidad;
- proveedores, roles, paises, contratos y subencargados;
- transferencias internacionales;
- regimen aplicable a cookies/analytics reales;
- estrategia para usuarios existentes;
- criterio de cambio material y reaceptacion;
- metadatos formales de la decision aprobada sobre el valor publico por defecto;
- proveedor de geocoding apto para domicilios privados.

## 18. Decisiones de producto incorporadas

Quedan registradas como alcance aprobado para implementacion bajo las
condiciones de este gate:

- separar ubicacion interna y publicacion;
- `mostrar_direccion_publicamente = true` por defecto para nuevas altas;
- preservar como publicos los registros historicos durante la migracion, sin
  inventar direccion ni coordenadas ausentes;
- exigir ubicacion valida a espacios nuevos;
- conservar utilidad de espacios privados en Search/Discovery;
- mostrar solo ciudad para privados;
- distinguir privacidad de ausencia/invalidez;
- no mostrar distancia ni derivados para privados;
- solicitar GPS en contexto y mantener fallback manual;
- no almacenar historial ni usar segundo plano;
- relevancia semantica anterior a cercania;
- ampliacion territorial explicita de 50 km y luego 100 km;
- banda interna inicial de 1 km para privados, condicionada a validacion de
  Seguridad;
- aceptaciones separadas de Terminos y Politica para crear cuenta;
- permiso tecnico de geolocalizacion independiente.

Aprobacion de Direccion para implementar ETAPA 95.1: confirmada mediante la
instruccion que actualiza este expediente. Identidad, fecha de firma, firma y
documento formal: `[PENDIENTE DE FORMALIZACION]`.

## 19. Condiciones del `GO condicionado`

Habilitacion de implementacion:

- [x] aprobacion legal del Sistema de Ubicacion confirmada por Direccion;
- [x] contrato funcional aprobado por Direccion;
- [x] tratamientos, riesgos y controles identificados;
- [x] permisos y fallback definidos para implementacion;
- [x] separacion entre ubicacion interna y publicacion definida;
- [x] ausencia de seguimiento, historial y segundo plano definida.

Condiciones durante la implementacion:

- [x] implementar proyeccion privada y reglas de ownership en backend;
- [x] validar coordenadas, presencia conjunta y transicion historica;
- [ ] implementar controles de ranking privado, rate limiting y logging seguro;
- [x] desacoplar geocoding del frontend con owner backend y proveedor
  reemplazable;
- [x] impedir usos incompatibles de Nominatim publico;
- [x] completar validaciones automatizadas y rollback por bloque.

Condiciones previas a activar geocoding productivo o lanzar:

- [x] proveedor y transferencia evaluados con limitaciones documentadas;
- [ ] Terminos y Politica con textos reales, versiones y referencias;
- [ ] estrategia de reaceptacion definida;
- [ ] retencion, eliminacion y derechos formalizados;
- [ ] usuarios y espacios historicos con estrategia operativa aprobada;
- [ ] validacion final de Seguridad;
- [ ] metadatos y evidencia formal de aprobaciones incorporados al expediente;
- [ ] no existen contradicciones con `15_LEGAL_AND_OPERATIONAL.md`.

## 20. Registro de revisiones y aprobaciones

| Fecha | Rol | Responsable real | Resultado | Condiciones | Evidencia |
| --- | --- | --- | --- | --- | --- |
| No informada | Legal | `[IDENTIDAD NO INFORMADA]` | Aprobacion confirmada por Direccion | Formalizar identidad, alcance y evidencia | Documento o referencia pendiente de incorporar |
| En 95.1 | Seguridad | `[PENDIENTE DE FORMALIZACION]` | `GO condicionado` | Implementar y validar matriz de controles | Tests y evidencia por bloque |
| En 95.1 | Compliance | `[PENDIENTE DE FORMALIZACION]` | Seguimiento condicionado | Completar matrices y trazabilidad | Expediente y documentos publicos |
| No informada | Direccion | `[IDENTIDAD NO INFORMADA]` | Implementacion aprobada | Formalizar identidad, fecha y evidencia | Instruccion de Direccion que actualiza el expediente |

No completar esta tabla retroactivamente ni con identidades o resultados no
verificados.

## 21. Evidencia de implementacion 95.1-A

Estado: completado. ETAPA 95.1 permanece abierta.

Contrato implementado:

- `Comercio` es dueno de `mostrar_direccion_publicamente`;
- default ORM y de base: `true`;
- la migracion asigna `true` a historicos y no completa datos ausentes;
- nuevas altas exigen provincia, ciudad, direccion, latitud y longitud;
- latitud y longitud deben existir juntas, ser finitas y respetar rangos;
- create persiste coordenadas y visibilidad;
- historicos incompletos siguen siendo legibles y administrables;
- una edicion no geografica no exige completar retroactivamente la ubicacion;
- si se modifica ubicacion, el estado resultante debe quedar completo.

Evidencia automatizada:

- upgrade, idempotencia y downgrade de la migracion;
- preservacion historica como publica;
- metadata de `comercios` alineada con el esquema fisico;
- alta valida y default publico;
- ausencia y parcialidad;
- `NaN`, infinito y rangos;
- administracion de historicos incompletos;
- rechazo de correccion historica parcial;
- suite backend completa.

Exclusiones preservadas al cerrar 95.1-A:

- la proyeccion de respuestas todavia no se habia implementado porque
  correspondia al bloque posterior 95.1-B;
- no se modificaron Haversine, distancia, Search, Discovery, ranking,
  LocationPicker, geocoding, Nominatim, Cache-First ni frontend.

## 22. Evidencia de implementacion 95.1-B

Estado: completado. ETAPA 95.1 permanece abierta.

Contrato implementado:

- el schema publico omite direccion, latitud, longitud, `maps_url` y
  `distancia_km` cuando `mostrar_direccion_publicamente = false`;
- ciudad permanece disponible y provincia conserva el contrato territorial;
- lista, detalle y Explorar aplican la proyeccion antes de responder;
- Search/Candidate conserva sus algoritmos internos y su hidratacion publica
  termina en el mismo contrato seguro de Explorar;
- el contrato privado de administracion no hereda la proyeccion publica y
  conserva ubicacion completa para el propietario;
- el calculo Haversine existente permanece intacto para espacios publicos;
- la salida manual de espacios seguidos utiliza el helper geografico del
  dominio y omite distancia para privados;
- historicos publicos conservan su comportamiento.

Evidencia automatizada:

- privado sin direccion, coordenadas, `maps_url` ni distancia en lista;
- misma garantia en detalle y Explorar;
- owner con ubicacion privada completa en `/comercios/mis`;
- espacio publico con contrato geografico y distancia preservados;
- espacios seguidos sin distancia privada y con distancia publica preservada;
- suites afectadas y suite backend completa.

Exclusiones preservadas:

- no se implementaron banda privada, Search territorial, ampliaciones,
  `positionRevision`, selector, geocoding ni frontend;
- no se modificaron formula, precision ni formato visual de distancia.

## 23. Evidencia de implementacion 95.1-C

Estado: completado. ETAPA 95.1 permanece abierta.

Contrato implementado:

- `LocationPicker` conserva un borrador local independiente del formulario;
- la posicion inicial de referencia no constituye una seleccion;
- una ubicacion canonica de edicion se reconstruye desde direccion y
  coordenadas recibidas;
- las alternativas de busqueda requieren seleccion explicita y ya no se
  selecciona automaticamente el primer resultado;
- click, drag y ubicacion del dispositivo modifican solamente el borrador e
  invalidan su coherencia hasta una revision explicita;
- direccion y coordenadas se transfieren juntas al formulario unicamente con
  `Confirmar ubicacion`;
- cancelar o cerrar descarta el borrador sin alterar el formulario;
- editar la direccion del formulario invalida sus coordenadas confirmadas;
- las operaciones asincronas se invalidan por revision y las busquedas en curso
  tambien se cancelan cuando corresponde;
- existe un contrato puro para aplicar en el futuro una propuesta de direccion
  solamente al punto que la origino, sin conectar reverse geocoding productivo.

Evidencia automatizada:

- referencia inicial sin confirmacion;
- seleccion explicita de una alternativa;
- click y drag limitados al borrador;
- confirmacion del conjunto direccion/coordenadas;
- invalidacion por edicion de direccion;
- cancelacion y reapertura desde datos canonicos;
- rechazo de revisiones asincronas obsoletas;
- rechazo de propuestas de direccion correspondientes a otro punto;
- lint y build del frontend.

Exclusiones preservadas:

- no se implemento reverse geocoding ni una integracion productiva nueva;
- no se modificaron backend, Search, Discovery, Candidate Engine, ranking,
  Haversine, distancia publica, Cache-First ni privacidad de respuestas;
- no se implemento la UX completa de visibilidad de direccion.

## 24. Evidencia de implementacion 95.1-D

Estado: ownership y contratos completados. ETAPA 95.1 permanece abierta y la
activacion productiva de geocoding continua bloqueada hasta resolver proveedor.

Arquitectura implementada:

- `LocationPicker` ya no conoce URL, parametros ni payload de Nominatim;
- un service frontend consume exclusivamente contratos FeedGo;
- endpoints backend autenticados reciben forward y reverse mediante `POST`;
- el modulo backend valida entrada, normaliza resultados y nunca devuelve el
  payload crudo del proveedor;
- una interfaz inyectable mantiene al contrato independiente del proveedor;
- el default seguro responde indisponibilidad sin transmitir consultas ni
  coordenadas a terceros;
- errores de proveedor y timeout se convierten en respuestas sanitizadas sin
  incluir consultas, coordenadas ni mensajes internos;
- reverse se integra con el borrador de 95.1-C y solo aplica la propuesta si la
  revision y el punto que la originaron siguen vigentes;
- no se incorpora cache compartida ni rate limiting arbitrario mientras no
  exista un proveedor aprobado cuya politica determine esos controles.

Evidencia automatizada:

- forward valido y multiples alternativas normalizadas;
- validacion de query, limite y contexto Argentina;
- reverse valido y coordenadas invalidas;
- proveedor deshabilitado, timeout y errores publicos sanitizados;
- ausencia de campos crudos o identificadores del proveedor;
- contrato probado con proveedor falso independiente;
- test frontend que impide reintroducir Nominatim en `LocationPicker`;
- seleccion explicita, revision asincrona y propuesta ligada al punto;
- suites backend y frontend, compileall, lint y build.

Condicion pendiente:

- evaluar y configurar un proveedor o instancia apto para domicilios privados,
  incluyendo contrato, transferencias, identificacion, timeout, limites, cache
  permitida y atribucion. Hasta entonces forward y reverse informan
  indisponibilidad y permiten la resolucion manual explicita del borrador.

## 25. Evidencia de implementacion 95.1-D2

Estado historico: adapter y controles locales implementados; validacion real
completada posteriormente en 95.1-D3.

Evidencia automatizada:

- forward, reverse, multiples resultados, contexto Argentina y limite maximo;
- normalizacion territorial, precision generica y confianza;
- key ausente, timeout, 4xx, 5xx, 429 y payload invalido;
- rate limit local determinista y configurable;
- ausencia de filtracion de API key y payload propietario;
- contrato FeedGo y `LocationPicker` independientes de Geoapify;
- fallback recuperable sin retorno automatico a Nominatim;
- script controlado preparado sin ejecutar por ausencia de key.

Riesgos pendientes de produccion:

- seleccionar y formalizar plan, cuenta responsable y condiciones comerciales;
- confirmar atribucion final aplicable al plan elegido;
- incorporar a Terminos/Privacidad la transferencia y retencion declarada;
- ejecutar y aprobar matriz real Rafaela/Sunchales/reverse;
- monitorear cuota diaria y considerar limitacion distribuida antes de escalar a
  multiples procesos o instancias.

## 26. Evidencia real 95.1-D3 - Geoapify Argentina

Clasificacion: `APROBADO CON LIMITACIONES` como proveedor actual reemplazable.
El dominio continua dependiendo exclusivamente de `GeocodingProvider`.

Consumo controlado:

- 35 requests reales al proveedor: 27 forward y 8 reverse;
- cero respuestas 429 y cero errores del proveedor;
- latencia observada aproximada: 0,98 a 2,24 segundos, promedio cercano a
  1,32 segundos;
- diez intentos iniciales bloqueados por el entorno local no alcanzaron al
  proveedor y no se contabilizan como consumo Geoapify;
- no se realizaron pruebas de carga ni se persistieron resultados.

Rafaela:

- `Moreno 8`: coincidencia exacta, address, confidence 1.0;
- `Moreno 8, Rafaela`: mismo punto correcto, confidence 0.81;
- `Sgto. Cabral 159`: normaliza a `Sargento Cabral 159`, address, confidence
  0.9;
- `Sargento Cabral 159`: coincidencia exacta, confidence 1.0;
- calle sin numero: dos segmentos razonables para seleccion explicita;
- `Sargento Cabral 160`: numero resuelto como alternativa propia;
- `Morreno 8`: corrige el error menor y ofrece dos alternativas coherentes;
- Municipalidad: varias alternativas, incluidas dos ubicaciones municipales
  correctas y una referencia territorial de menor confianza.

Sunchales:

- `Av. Belgrano 103`, `Avenida Belgrano 103` y `Av Belgrano 103`: mismo
  Palacio Municipal correcto, address, confidence 1.0;
- calle sin numero: Avenida Belgrano, street, confidence 1.0;
- `Avenida Belgrano 105`: numero cercano resuelto como address independiente;
- `Belgranno 103`: solo puede sostener una referencia a Sunchales de precision
  locality y confidence 0.25;
- `Municipalidad de Sunchales`: no produce una coincidencia util segura.

Control derivado de evidencia:

- el adapter descarta resultados con confidence 0;
- cuando existe ciudad contextual, descarta resultados incompatibles con esa
  ciudad;
- el typo de Sunchales conserva solo la referencia territorial util;
- la consulta municipal ambigua queda vacia en vez de exponer alternativas de
  Funes, Rosario u otras ciudades.

Reverse:

- Rafaela: Moreno 8 y Sargento Cabral 159 regresan direccion, ciudad y
  provincia coherentes;
- Sunchales: Avenida Belgrano 103 regresa el Palacio Municipal correcto;
- un punto de calle sin numero produjo una numeracion cercana (`512`), por lo
  que toda propuesta reverse sigue tratandose como sugerencia revisable y nunca
  como verdad o confirmacion automatica.

Privacidad verificada por inspeccion:

- forward envia solamente query, ciudad, provincia, pais, idioma, limite y key
  tecnica backend;
- reverse envia solamente latitud, longitud, idioma, limite y key tecnica;
- no se envian usuario, email, comercio, IDs FeedGo ni tokens internos;
- la key no se registra, devuelve ni expone al frontend.

Limitaciones aceptadas:

- nombres de POI ambiguos pueden no resolverse;
- errores ortograficos no siempre preservan precision de domicilio;
- reverse puede proponer una numeracion cercana;
- ciudad devuelta puede usar la forma `Municipio de Sunchales`, cuya futura
  normalizacion territorial canonica pertenece al contrato geografico posterior;
- confidence y precision orientan la revision pero no reemplazan la confirmacion
  explicita del usuario.

Resultado del gate tecnico: 95.1-D queda cerrado. La formalizacion del plan,
atribucion final, tratamiento en documentos publicos y monitoreo de cuota
continuan como condiciones operativas previas a produccion/lanzamiento, no como
bloqueo para continuar la implementacion de ETAPA 95.1.

## 27. Evidencia de implementacion 95.1-E

Estado: completado en backend. ETAPA 95.1 permanece abierta.

Controles implementados y verificados:

- la identidad territorial usa ciudad normalizada, codigo ISO 3166-2 de
  provincia argentina y codigo de pais `AR`, sin hardcodear ciudades;
- `scope=local` restringe candidatos al territorio activo y
  `scope=expanded` solo se ejecuta por solicitud explicita con 50 km o 100 km;
- la frontera territorial se aplica en el servicio comun de Comercios despues
  de obtener candidatos relevantes y antes del ranking final y la paginacion;
  Candidate Engine, Discovery, Knowledge, Indexer y embeddings no fueron
  redisenados;
- los caminos clasico, keyword y semantico respetan la misma frontera; el camino
  clasico deja de paginar globalmente antes de filtrar y ordenar por geografia;
- un espacio publico conserva Haversine y `distancia_km` exacta; un espacio
  privado participa territorialmente y ordena por banda interna de 1 km,
  subordinada a relevancia, sin devolver distancia, banda, coordenadas ni score
  geografico;
- los historicos con ciudad y provincia validas participan en el territorio sin
  inventar coordenadas ni producir distancia;
- `SearchEvent.metadata_json` registra territorio, alcance, expansion y estado
  de resultados sin coordenadas precisas, domicilio ni banda privada;
- la ausencia transitoria de `scope` conserva el contrato anterior de Explorar
  hasta que 95.1-F aporte y gestione el contexto territorial del usuario; no
  ejecuta ampliaciones ocultas ni se presenta como ubicacion actual.

Evidencia automatizada: cobertura especifica de normalizacion, ciudades
homonimas, los tres caminos de busqueda, frontera previa a paginacion, privacidad
publica/privada, banda estable, ampliaciones explicitas, historicos y
observabilidad sin coordenadas. No se modificaron frontend, Geoapify,
`LocationPicker`, Haversine ni formatos de distancia.

## 28. Evidencia de implementacion 95.1-F

Estado: completado. ETAPA 95.1 permanece abierta.

Controles implementados y verificados:

- un owner frontend compartido mantiene en memoria fuente, territorio, posicion,
  precision, captura y `positionRevision`; no persiste coordenadas ni historial;
- Explorar y Seguidos dejan de solicitar geolocalizacion al montar y reutilizan
  el mismo owner; la solicitud se inicia mediante una accion con explicacion
  visible y usa `getCurrentPosition`, nunca `watchPosition`;
- lectura rapida: `maximumAge=60 s`, `timeout=3 s`, sin alta precision;
  refinamiento: `maximumAge=0`, `timeout=8 s`, con alta precision cuando la
  lectura no alcanza 100 m para distancia o 1000 m para territorio;
- territorio admite 5 minutos/1000 m y distancia 60 segundos/100 m como
  vigencias independientes; una lectura territorial util puede conservarse si
  falla el refinamiento sin publicarse como distancia actual;
- `positionRevision` cambia por territorio, accion explicita, lectura aceptada
  tras obsolescencia o desplazamiento de al menos
  `max(50 m, accuracy anterior + accuracy nueva)`, no por ruido GPS;
- la resolucion `POST /geocoding/territory` reutiliza el owner backend y devuelve
  solamente identidad/textos territoriales normalizados; no requiere cuenta y no
  expone domicilio, coordenadas ni payload del proveedor;
- fallback manual y ciudad de perfil son elecciones visibles diferenciadas de
  GPS; el perfil nunca se presenta como ubicacion actual;
- las query keys incluyen consulta, territorio, modo, alcance, paginacion y
  revision, pero no latitud/longitud crudas; el request envia la posicion exacta
  solo si conserva vigencia de distancia;
- prefetch y consulta principal comparten el mismo builder; al cambiar territorio
  no se usa la respuesta anterior como placeholder, se conserva la cache previa
  y se consulta/revalida la clave de la nueva ciudad;
- 50 km y 100 km se activan por acciones explicitas y nunca mediante una busqueda
  oculta; sin posicion no se ofrece ampliacion radial;
- espacios publicos conservan distancia/formato existentes y los privados
  muestran ciudad sin calcular distancia en frontend.

Evidencia automatizada: permiso recuperable, opciones de lectura, refinamiento,
frescura, ruido/desplazamiento, cambio territorial, fallback manual/perfil,
query key/revision, prefetch comun, ausencia de solicitudes automaticas y
contrato backend territorial sin datos precisos.

## 29. Gate completado de cierre de ETAPA 95 - Frontend Ownership Audit

Antes de cerrar ETAPA 95 debia realizarse una auditoria transversal acotada para
detectar responsabilidades backend alojadas indebidamente en frontend, incluidas
llamadas directas a proveedores, reglas de negocio, permisos, privacidad,
ranking, validaciones de dominio y transformaciones propietarias.

El gate fue completado en 95.7-A y su evidencia queda en
`docs/24_FRONTEND_OWNERSHIP_AUDIT.md`. No autorizo refactors preventivos ni
amplio 95.1-D; cada hallazgo quedo remitido a su documento y owner natural.

## 30. Evidencia de implementacion y cierre tecnico 95.1-G

Estado: completado. Sprint 95.1 queda tecnicamente cerrado; ETAPA 95 continua
abierta.

Evidencia implementada:

- Terminos y Politica poseen rutas publicas separadas, contenido acorde a los
  tratamientos reales, estructura semantica y version visible;
- backend Usuarios es el owner unico de tipo, version, referencia y URL de los
  documentos vigentes; la misma definicion genera evidencia de registro;
- los enlaces de registro abren una nueva pestana, conservan el formulario y
  mantienen checkboxes separados, desmarcados y obligatorios; no solicitan GPS;
- los textos no inventan razon social, CUIT, domicilio, responsable, firma ni
  contacto. Indican que su activacion productiva depende de completar esos datos
  y las formalizaciones registradas en este expediente;
- creacion y edicion presentan `Mostrar mi direccion publicamente`, activo por
  defecto, con explicacion de uso interno y ciudad publica; el valor canonico se
  carga al editar y los cambios invalidan detalle, Explorar y Seguidos;
- el detalle publico muestra direccion y ciudad cuando se publican, y solo
  ciudad cuando la proyeccion privada omite domicilio; Como llegar continua
  dependiendo de coordenadas o `maps_url` publicos;
- LocationPicker conserva attribution y la resolucion territorial expone la
  attribution generica del provider sin credenciales ni acoplamiento;
- privacidad de APIs, ownership, coordenadas, banda privada, SearchEvent,
  Cache-First, asincronia, ausencia de historial/background y secretos quedaron
  cubiertos por inspeccion y suites automatizadas A-G;
- upgrade, downgrade y equivalencia metadata/base fisica permanecen cubiertos
  por la suite de contrato de ubicacion.

Resolucion de Seguridad tecnica de 95.1: controles implementados y evidencia
automatizada suficiente para cerrar el sprint. No se registra una revision
profesional o independiente inexistente.

Condiciones fuera del cierre tecnico que bloquean produccion o lanzamiento:
identificacion, domicilio y contactos institucionales; procedimiento operativo
de derechos; retencion y eliminacion formal; estrategia material de
reaceptacion; rate limiting general y controles de infraestructura productiva;
formalizacion de aprobaciones y revision final identificada de Seguridad.

La `Frontend Ownership Audit`, pendiente al cerrar 95.1-G, fue ejecutada y
cerrada en 95.7-A. Las condiciones institucionales y operativas enumeradas
arriba permanecen previas a produccion y no se declaran aprobadas por el cierre
tecnico de ETAPA 95.
