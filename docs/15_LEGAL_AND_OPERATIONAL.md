# Gobierno Legal, Privacidad y Operacion

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Documento transversal legal y operativo.
Nivel de autoridad: Alto para gobierno legal, privacidad, compliance,
seguridad operativa y lanzamiento.
Documento dueno: `docs/15_LEGAL_AND_OPERATIONAL.md`.
Responsable funcional: Legal, compliance, seguridad operativa y direccion.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`02_PRODUCT.md`, `05_SEARCH_ROADMAP.md`, `07_DECISIONS.md`,
`08_ENGINEERING_PRINCIPLES.md`, `16_DATA_INTEGRITY_AND_RECOVERY.md`,
`17_OBSERVABILITY_AND_OPERATIONS.md`.
Documentos tecnicos relacionados: `18_PWA_ENTERPRISE.md`,
`19_LOCATION_LEGAL_GATE.md`.
Cuando debe consultarse: antes de modificar funcionalidades sensibles,
proveedores, datos personales, permisos, contenido publico, geolocalizacion,
comunicaciones, notificaciones, reservas, productos, pagos, IA, logs, backups
u operacion en produccion.
Jurisdiccion principal: Republica Argentina.

Este documento no es un contrato, no constituye asesoramiento juridico, no
redacta textos legales definitivos y no garantiza cumplimiento normativo por si
solo.

Los documentos publicos de FeedGo deberan redactarse y revisarse por separado.
Este documento gobierna como deben disenarse, aprobarse, implementarse,
versionarse y mantenerse esos documentos y las funcionalidades relacionadas.

## 1. Naturaleza, alcance y autoridad

### 1.1 Naturaleza

Este documento es una guia obligatoria de gobierno interno para producto,
ingenieria, seguridad, compliance, operacion y direccion.

No reemplaza:

- Terminos y Condiciones;
- Politica de Privacidad;
- Politica de Cookies o tecnologias equivalentes;
- Politica de IA;
- Politica de Moderacion;
- Normas de la Comunidad;
- contratos con usuarios, comercios o proveedores;
- revision profesional legal.

### 1.2 Alcance

Debe consultarse antes de modificar o crear funcionalidades relacionadas con:

- usuarios;
- datos personales;
- permisos;
- ownership;
- geolocalizacion;
- camara, galeria, archivos o medios;
- contenido publico;
- comercios;
- publicaciones;
- precios;
- promociones;
- moderacion;
- denuncias;
- comunicaciones externas;
- notificaciones;
- reservas;
- productos e inventario;
- pagos y facturacion futura;
- analytics;
- ranking;
- IA;
- proveedores externos;
- transferencias internacionales;
- logs;
- backups;
- eliminacion de informacion;
- incidentes;
- administracion;
- operacion en produccion.

### 1.3 Autoridad dentro del Sistema de Gobierno

Si una funcionalidad contradice este documento, la implementacion o el
lanzamiento quedan bloqueados hasta que exista una decision documentada.

Si este documento contradice una norma vigente, prevalece la norma vigente y el
documento debe actualizarse antes de continuar.

Si este documento contradice otro documento oficial del repositorio, debe
informarse la contradiccion y detenerse la tarea hasta resolver el dueno natural
de la regla.

### 1.4 Etiquetas de reglas

Las reglas internas pueden clasificarse como:

- `[LEY]`: obligacion derivada de normativa vigente identificada.
- `[CONTROL FEEDGO]`: control interno obligatorio adoptado por FeedGo.
- `[BLOQUEANTE]`: condicion que impide implementar o lanzar hasta resolverse.
- `[REVISION LEGAL]`: requiere validacion profesional antes de publicar o
  activar.
- `[CONDICIONAL]`: aplica solo si FeedGo adopta la funcionalidad indicada.
- `[BUENA PRACTICA]`: recomendacion oficial, estandar preventivo o control
  prudente.

## 2. Principios permanentes

Compliance by Design se encuentra definido en
`docs/08_ENGINEERING_PRINCIPLES.md` y constituye el mecanismo mediante el cual
el cumplimiento forma parte del diseno inicial de funcionalidades.

### 2.1 Necesidad real

`[CONTROL FEEDGO]` FeedGo no implementara funcionalidades unicamente porque
sean tecnicamente posibles. Toda funcionalidad que aumente significativamente
la complejidad debera estar respaldada por una necesidad del producto,
evidencia de uso real o una decision estrategica documentada.

### 2.2 Legalidad desde el diseno

`[BLOQUEANTE]` Ninguna funcionalidad sensible puede implementarse sin
identificar previamente finalidad, datos, usuarios afectados, permisos,
proveedores, riesgos, evidencia, retencion y eliminacion.

### 2.3 Minimizacion

`[LEY]` Los datos deben ser ciertos, adecuados, pertinentes y no excesivos
respecto de la finalidad informada.

`[CONTROL FEEDGO]` No se recolectaran datos "por si algun dia sirven". Cada
campo nuevo debe tener necesidad concreta, dueno natural y ciclo de vida.

### 2.4 Finalidad

`[LEY]` Los datos no deben usarse para finalidades distintas o incompatibles
con las informadas al recolectarlos.

`[BLOQUEANTE]` Una finalidad nueva que afecte datos existentes requiere
auditoria documental antes de implementarse.

### 2.5 Transparencia real

`[CONTROL FEEDGO]` La informacion relevante debe presentarse en el momento de
la decision, en castellano claro, sin patrones oscuros, sin casillas
premarcadas y sin depender exclusivamente de textos extensos escondidos.

### 2.6 Seguridad y confidencialidad

`[LEY]` FeedGo debe adoptar medidas tecnicas y organizativas razonables para
evitar adulteracion, perdida, consulta o tratamiento no autorizado de datos.

`[CONTROL FEEDGO]` Toda funcionalidad sensible debe respetar minimo privilegio,
ownership backend, trazabilidad, proteccion de secretos y logging seguro.

### 2.7 Evidencia proporcional

`[CONTROL FEEDGO]` FeedGo debe poder demostrar decisiones relevantes sin
conservar mas datos de los necesarios.

## 3. Roles, responsables y poder de bloqueo

### 3.1 Ingenieria

Responsabilidades:

- identificar datos, permisos, rutas, modelos, logs y proveedores afectados;
- implementar ownership y autorizacion en backend;
- evitar duplicacion de fuentes de verdad;
- proteger secretos y configuracion;
- validar seguridad tecnica;
- impedir que el frontend sea fuente unica de autorizacion;
- detener implementaciones cuando falte una decision bloqueante.

### 3.2 Producto

Responsabilidades:

- justificar la necesidad de producto;
- definir usuarios afectados;
- evitar alcance innecesario;
- separar funciones obligatorias y opcionales;
- garantizar claridad de la experiencia;
- no convertir FeedGo en marketplace sin decision explicita.

### 3.3 Seguridad

Responsabilidades:

- revisar autenticacion, autorizacion, permisos, secretos, logs, proveedores y
  superficies administrativas;
- definir controles de abuso, rate limiting y respuesta a incidentes;
- bloquear riesgos criticos no mitigados.

### 3.4 Compliance

Responsabilidades:

- mantener matrices y evidencia;
- verificar checklists;
- registrar excepciones;
- coordinar revision periodica;
- asegurar trazabilidad de aprobaciones y revocaciones.

### 3.5 Responsable legal

Responsabilidades:

- validar documentos publicos;
- evaluar normas aplicables;
- revisar datos personales, consumidores, menores, comunicaciones, reservas,
  proveedores, pagos, IA y transferencias;
- aprobar o bloquear riesgos juridicos.

### 3.6 Direccion

Responsabilidades:

- aprobar decisiones estrategicas de alto impacto;
- aceptar o rechazar excepciones relevantes;
- definir edad minima, modelo comercial, pagos, proveedores criticos y uso
  sensible de IA;
- autorizar lanzamiento publico.

## 4. Flujo obligatorio para nuevas funcionalidades

### 4.1 Idea

Debe documentarse:

- problema de producto;
- necesidad real;
- usuarios afectados;
- si toca datos, permisos, IA, pagos, reservas, comunicaciones, contenido
  publico, geolocalizacion o proveedores.

Salida: ficha inicial de funcionalidad.

### 4.2 Diseno

Debe documentarse:

- flujo funcional;
- datos requeridos;
- pantallas o interacciones;
- permisos del dispositivo;
- proveedores;
- estados;
- riesgos previsibles;
- documentos publicos afectados.

Salida: diseno funcional con impacto legal-operativo.

### 4.3 Auditoria

Debe completarse, cuando corresponda:

- matriz de tratamientos;
- matriz de bases legales;
- matriz de consentimientos;
- matriz de retencion;
- matriz de permisos;
- matriz de proveedores;
- matriz de riesgos;
- evaluacion de menores;
- evaluacion de consumidor;
- evaluacion de seguridad.

Salida: `GO`, `GO condicionado` o `NO GO`.

### 4.4 Aprobacion

Debe aprobarse por los roles aplicables segun riesgo.

`[BLOQUEANTE]` Una funcionalidad sensible no puede implementarse si tiene un
`NO GO`, una matriz obligatoria incompleta o una revision legal pendiente
marcada como previa a implementacion.

### 4.5 Implementacion

La implementacion no puede ampliar el alcance aprobado sin volver a auditoria.

Debe preservar:

- minimizacion;
- ownership backend;
- logs seguros;
- evidencias necesarias;
- textos consistentes con documentos publicos;
- bloqueo o feature flag cuando falte una dependencia externa.

### 4.6 Validacion

Antes de lanzar debe verificarse:

- datos realmente recolectados;
- permisos solicitados;
- revocacion;
- errores;
- accesibilidad;
- seguridad;
- logs;
- eliminacion;
- documentos publicos;
- evidencias.

### 4.7 Lanzamiento

El lanzamiento requiere:

- documentos publicos vigentes;
- soporte preparado;
- monitoreo minimo;
- plan de rollback;
- responsable operativo;
- version registrada;
- aprobacion final.
- ETAPA 96 - Plataforma Instalable y PWA Enterprise cerrada, sin bloqueantes
  criticos o altos.

## 5. Clasificacion de funcionalidades sensibles

Una funcionalidad es sensible si involucra al menos una de estas categorias:

- datos personales;
- datos de menores;
- ubicacion;
- datos publicos de comercios;
- contenido generado por usuarios;
- mensajes o comunicaciones;
- proveedores externos;
- transferencias internacionales;
- pagos;
- reservas;
- productos, precios o promociones;
- ranking, recomendaciones o IA;
- administracion interna;
- logs o exportaciones;
- seguridad o autenticacion.

`[BLOQUEANTE]` Toda funcionalidad sensible requiere ficha, matrices aplicables
y aprobacion antes de implementarse o lanzarse.

## 6. Datos personales y tratamientos

### 6.1 Inventario obligatorio

Antes del lanzamiento debe existir un inventario versionado de tratamientos.

`[BLOQUEANTE]` No puede crearse una tabla, campo, log, evento, indice, cache,
embedding, integracion o exportacion que trate datos personales sin registrar
el tratamiento o actualizar el documento tecnico de la etapa.

### 6.2 Dueno natural del dato

Cada dato debe tener un unico dueno natural. No debe duplicarse informacion
personal si una referencia a una entidad existente es suficiente.

### 6.3 Datos a evitar por defecto

No se recolectaran salvo decision especifica:

- DNI;
- fecha completa de nacimiento;
- domicilio particular de usuarios;
- datos de salud;
- datos biometricos;
- contactos del dispositivo;
- ubicacion precisa persistente;
- historial de recorridos;
- mensajes privados para analytics;
- identificadores publicitarios persistentes;
- datos sensibles inferidos.

## 7. Bases legales, consentimientos y evidencia

### 7.1 Fundamento distinto de consentimiento

Cada tratamiento debe identificar su fundamento juridico u operativo.

El consentimiento no debe usarse como respuesta generica para todo riesgo. Se
debe distinguir cuando el tratamiento sea necesario para la cuenta, contractual,
legal, de seguridad, de interes legitimo evaluado o verdaderamente opcional.

### 7.2 Consentimientos separados

Los consentimientos deben separarse por finalidad:

- Terminos y Condiciones;
- Politica de Privacidad;
- geolocalizacion precisa;
- comunicaciones comerciales;
- WhatsApp;
- email marketing;
- push promocional;
- cookies o SDK no esenciales;
- compartir datos con comercios para reservas;
- IA o entrenamiento, si algun dia aplica;
- reglas de comunidad;
- cambios sustanciales.

`[BLOQUEANTE]` No se permite agrupar finalidades opcionales en una aceptacion
unica ni usar casillas premarcadas.

### 7.3 Evidencia minima

Cuando corresponda, conservar:

- usuario o identificador interno;
- documento o finalidad aceptada;
- version;
- timestamp;
- canal o pantalla;
- metodo de aceptacion;
- alcance;
- estado: aceptado, rechazado o revocado;
- referencia verificable de la version presentada;
- revocaciones;
- solicitudes de derechos;
- acciones administrativas sensibles.

No conservar indefinidamente IP, user-agent completo, coordenadas exactas,
payloads completos, mensajes privados, tokens o cookies de sesion sin
justificacion documentada.

### 7.4 Evidencia persistente separada

Cuando la aceptacion de un documento publico versionado sea necesaria para crear
u operar una cuenta, la evidencia minima puede requerir una entidad persistente
separada, con responsabilidad unica y alcance limitado.

La decision permanente que define el dueno persistente separado se registra en
`DEC-041`. Este documento gobierna los controles legales y operativos aplicables
a esa evidencia.

El documento aceptado debe ser identificable y versionado. La evidencia tecnica
debe registrar la aceptacion o estado aplicable, pero no reemplaza la redaccion,
revision ni aprobacion profesional de Terminos, Politica de Privacidad u otros
documentos publicos.

Mientras los textos legales definitivos no existan como documentos versionados
con contenido estable, la evidencia debe conservar una referencia verificable de
tipo y version presentada. No debe declararse como hash criptografico del
contenido legal real si ese contenido no fue incorporado al mecanismo tecnico.

Los usuarios existentes sin evidencia historica deben tratarse como usuarios sin
evidencia. No se deben inventar aceptaciones retroactivas.

La evidencia no debe incluir informacion tecnica excesiva sin justificacion,
como IP completa, user-agent completo, geolocalizacion, token o sesion, payload
completo o copia completa del texto legal.

Los consentimientos opcionales, como comunicaciones comerciales, WhatsApp,
email marketing, push promocional, cookies no esenciales o finalidades futuras
de IA, deben permanecer separados de las aceptaciones necesarias para crear y
operar una cuenta.

Estado tecnico al cierre de ETAPA 91:

- el registro exige aceptacion explicita separada de Terminos y Politica de
  Privacidad;
- el backend valida ambas aceptaciones;
- las versiones y referencias documentales son controladas por backend;
- la evidencia persistente minima queda implementada en
  `usuarios_documentos_aceptaciones`;
- `documento_referencia` conserva una referencia logica de tipo y version, no
  un hash criptografico del contenido legal definitivo;
- la creacion de usuario y evidencias se realiza atomicamente;
- los usuarios existentes permanecen sin evidencia historica retroactiva.

Pendiente antes del lanzamiento publico:

- textos definitivos de Terminos y Politica de Privacidad;
- versionado legal aprobado de esos textos;
- revision profesional legal;
- estrategia de reaceptacion para nuevas versiones;
- tratamiento operativo de usuarios existentes sin evidencia historica.

## 8. Derechos de usuarios

FeedGo debe poder atender solicitudes de acceso, rectificacion, actualizacion,
supresion, baja y reclamos.

Antes del lanzamiento deben definirse:

- responsable legal;
- domicilio;
- canal de privacidad;
- canal de soporte;
- verificacion de identidad;
- plazos internos;
- registro de solicitud y respuesta;
- excepciones por seguridad, fraude, disputas o obligaciones legales;
- tratamiento de datos en backups.

`[BLOQUEANTE]` No puede lanzarse una version publica sin canal y procedimiento
de derechos de usuarios.

## 9. Menores de edad

Las personas menores de 18 anos tienen proteccion especial.

Antes del lanzamiento debe existir decision formal sobre:

- edad minima;
- si menores pueden registrarse;
- consentimiento parental cuando corresponda;
- contenido visible;
- contacto con comercios;
- ubicacion;
- moderacion;
- denuncias;
- eliminacion.

`[BLOQUEANTE]` No se implementaran funciones dirigidas especificamente a
menores sin revision legal y decision de direccion.

## 10. Geolocalizacion

La ubicacion vinculada a una persona identificada o identificable es dato
personal.

Controles:

- ubicacion exacta opcional para usuarios generales;
- explicar finalidad antes del permiso del sistema;
- solicitar permiso solo cuando se use la funcion;
- ofrecer ciudad, zona o busqueda manual;
- no insistir repetidamente ante denegacion;
- no bloquear toda la app si la ubicacion no es esencial;
- no usar ubicacion en segundo plano en el MVP;
- no guardar historial de recorridos;
- no publicar ubicacion precisa del usuario;
- reducir precision cuando alcance;
- permitir revocacion.

La direccion comercial puede ser publica, pero puede coincidir con un domicilio
personal. Deben contemplarse comercios desde el hogar y servicios por zona.

`[BLOQUEANTE]` Ubicacion precisa persistente, segundo plano o perfilado por
recorridos requieren revision legal, de seguridad y de direccion.

El expediente aplicable a la ubicacion de ETAPA 95 se registra en
`docs/19_LOCATION_LEGAL_GATE.md`. Ese documento aplica este marco al alcance
concreto, conserva evidencia y condiciones del gate y no sustituye esta norma,
los documentos publicos ni la revision profesional requerida.

## 11. Permisos del dispositivo, medios y archivos

### 11.1 Permisos

Cada permiso debe tener finalidad, momento de solicitud y alternativa.

Permisos a evaluar:

- ubicacion precisa;
- ubicacion aproximada;
- camara;
- fotos o galeria;
- archivos;
- notificaciones push;
- microfono;
- contactos;
- identificadores publicitarios;
- almacenamiento amplio;
- tracking entre apps o sitios;
- autenticacion biometrica local.

`[BLOQUEANTE]` No se solicitaran contactos, microfono, almacenamiento amplio,
tracking o identificadores publicitarios sin decision explicita y revision
previa.

### 11.2 Archivos y medios

Todo upload debe contemplar:

- validacion server-side;
- limite de tamano;
- tipo real;
- nombres generados por servidor;
- eliminacion de metadatos sensibles cuando sea razonable;
- control de malware cuando aplique;
- ownership;
- eliminacion coordinada;
- URLs controladas;
- no exponer rutas internas.

## 12. Contenido publico, UGC y propiedad intelectual

FeedGo debe distinguir contenido creado por usuarios, contenido creado por
comercios, datos enriquecidos por FeedGo y contenido generado o asistido por
IA.

Antes de publicar o permitir publicar contenido deben definirse:

- quien puede crear;
- quien puede editar;
- quien puede eliminar u ocultar;
- visibilidad;
- licencia necesaria para mostrar el contenido;
- responsabilidad del publicador;
- derecho de imagen;
- marcas, logos y nombres comerciales;
- infracciones de propiedad intelectual;
- procedimiento de retiro;
- evidencia minima.

`[BLOQUEANTE]` No puede lanzarse una superficie publica relevante sin reglas de
contenido, denuncias y accion de moderacion.

## 13. Moderacion, denuncias y medidas sobre contenido

La moderacion debe ser proporcional, trazable y no arbitraria.

Debe contemplar:

- contenido prohibido;
- abuso;
- fraude;
- suplantacion;
- explotacion o riesgo para menores;
- discriminacion;
- violencia;
- productos o servicios restringidos;
- publicidad enganosa;
- urgencias;
- preservacion de evidencia;
- sanciones;
- apelacion;
- confidencialidad del denunciante;
- acceso limitado del equipo interno.

FeedGo no debe automatizar denuncias penales ni entrega de datos a autoridades
sin procedimiento aprobado.

### 13.1 Canal minimo de denuncia

FeedGo debe ofrecer un canal minimo para que usuarios autenticados reporten
contenido publico. La denuncia es una solicitud de revision, no una
determinacion automatica de incumplimiento.

El denunciante y sus datos deben permanecer protegidos y no deben exponerse
publicamente al recurso denunciado, al comercio denunciado ni a otros usuarios.

Los motivos deben ser controlados. El texto libre solo puede existir como
detalle opcional limitado y sujeto a minimizacion.

El contenido no debe ocultarse automaticamente solo por cantidad de denuncias.
El retiro, restauracion, sancion o cualquier medida de plataforma requiere una
decision de moderacion separada, proporcional y trazable.

La entidad de denuncias no reemplaza una futura entidad de decisiones de
moderacion y no debe mezclarse con la evidencia de aceptacion de documentos.

Normas de la Comunidad y Politica de Moderacion deben existir como documentos
publicos versionados antes del lanzamiento. La implementacion tecnica del canal
de denuncia no reemplaza la revision ni redaccion legal profesional.

Estado tecnico al cierre de ETAPA 91:

- el canal minimo autenticado de denuncias queda implementado;
- la entidad persistente `contenido_denuncias` registra denuncias sobre
  comercio, publicacion e historia;
- los motivos son controlados;
- el denunciante no se expone en respuestas publicas;
- la repeticion exacta por usuario, recurso y motivo es idempotente;
- la denuncia no oculta contenido, no sanciona usuarios y no modifica estados
  operativos.

Pendiente antes del lanzamiento publico:

- Normas de Comunidad versionadas;
- Politica de Moderacion versionada;
- reglas de contenido incorporadas o referenciadas desde Terminos;
- revision profesional legal;
- operacion administrativa de denuncias;
- decisiones de moderacion, sanciones, apelaciones y restauraciones;
- criterios de accion manual sobre contenido reportado.

## 14. Comercios, publicaciones, precios y promociones

FeedGo es una vidriera digital y motor de descubrimiento. No debe asumir
automaticamente el rol de vendedor, procesador de pagos, garante de stock,
habilitacion, calidad, seguridad o cumplimiento del comercio.

Si se muestran bienes, servicios, precios o promociones deben definirse:

- comercio responsable;
- caracteristicas esenciales;
- moneda;
- si el precio es final o informativo;
- vigencia;
- impuestos, cargos o restricciones;
- disponibilidad;
- condiciones;
- fuente y fecha de publicacion;
- correccion de errores;
- distincion entre disponibilidad del comercio, horario, producto y reserva.

`[BLOQUEANTE]` No se deben mostrar precios, promociones o disponibilidad como
confirmados si FeedGo no cuenta con fuente y estado verificables.

## 15. Reservas, solicitudes y rol de FeedGo

Reservas publicas no deben exponer la agenda privada completa del propietario.

Antes de implementar reservas se debe definir:

- si FeedGo actua como intermediario tecnico o asume obligaciones adicionales;
- datos compartidos con el comercio;
- estados;
- vencimiento;
- cancelacion;
- confirmacion;
- rechazo;
- errores;
- soporte;
- relacion con precios;
- ausencia o presencia de pago;
- responsabilidad del comercio.

El carrito de reserva no debe presentarse como compra si no existe compraventa
ni pago dentro de FeedGo.

`[BLOQUEANTE]` No puede lanzarse Reservas publicas sin revision legal sobre
rol de FeedGo, consumidor, privacidad y responsabilidad.

## 16. Comunicaciones, notificaciones y Registro No Llame

FeedGo debe separar:

- comunicaciones de seguridad;
- comunicaciones operativas;
- comunicaciones transaccionales;
- notificaciones locales dentro de FeedGo;
- push;
- email;
- WhatsApp;
- comunicaciones comerciales.

Controles:

- opt-in separado para comerciales;
- baja simple;
- revocacion por canal;
- registro de origen del consentimiento;
- respeto de preferencias internas;
- evaluacion de Registro No Llame cuando corresponda;
- plantillas cuando el proveedor lo requiera;
- no enviar datos sensibles;
- no reutilizar email o telefono de identidad como destino comercial sin
  revisar finalidad y estado.

`[BLOQUEANTE]` No puede integrarse correo, WhatsApp o push comercial sin
proveedor auditado, consentimiento o fundamento aplicable, baja y trazabilidad.

## 17. Cookies, SDKs, analytics y tracking

Antes de integrar cookies, almacenamiento local no esencial, pixels, analytics
o SDKs debe definirse:

- finalidad;
- proveedor;
- datos recolectados;
- identificadores;
- transferencia;
- retencion;
- esencial u opcional;
- revocacion;
- documentacion publica aplicable;
- impacto en App Store o Google Play.

`[BLOQUEANTE]` No se integraran SDKs publicitarios, tracking entre apps,
identificadores publicitarios o analytics invasivo sin auditoria previa.

## 18. IA, ranking, recomendaciones y decisiones automatizadas

Se debe distinguir:

- busqueda textual;
- ranking;
- recomendaciones;
- embeddings;
- conocimiento derivado;
- IA generativa;
- moderacion automatizada;
- decisiones automatizadas relevantes.

La IA no puede:

- presentar inferencias como hechos;
- afirmar habilitacion, seguridad o calidad de un comercio sin evidencia;
- revelar datos privados;
- contactar comercios o reservar sin confirmacion;
- sancionar definitivamente sin revision cuando afecte derechos relevantes;
- usar mensajes privados para entrenamiento sin decision legal y de producto.

`[BLOQUEANTE]` Todo uso de IA con datos personales, perfilado relevante,
entrenamiento, moderacion automatizada o decisiones que afecten usuarios
requiere revision legal, privacidad, seguridad y producto.

## 19. Proveedores, encargados y transferencias internacionales

Antes de usar nube, email, mapas, almacenamiento, WhatsApp, analytics, IA,
pagos o cualquier proveedor externo se debe identificar:

- entidad contratada;
- servicio;
- rol;
- datos tratados;
- finalidad;
- pais;
- subencargados;
- seguridad;
- retencion;
- eliminacion;
- soporte;
- incidentes;
- exportacion;
- plan de salida;
- contrato;
- transferencia internacional.

`[LEY]` Las transferencias a paises sin nivel adecuado requieren encuadre en
una excepcion o garantias apropiadas, como clausulas contractuales modelo,
cuando corresponda.

`[BLOQUEANTE]` No se aprobara un proveedor solo por popularidad, facilidad
tecnica o bajo costo.

## 20. Seguridad, DevSecOps y controles tecnicos

Controles minimos:

- contrasenas con hash robusto;
- tokens con expiracion;
- autorizacion backend;
- ownership;
- roles;
- MFA para administracion;
- validacion server-side;
- CORS restrictivo;
- CSRF cuando corresponda;
- rate limiting;
- manejo seguro de errores;
- dependencias actualizadas;
- secretos fuera del repositorio;
- HTTPS;
- separacion de ambientes;
- usuario de base de datos sin privilegios administrativos;
- no usar datos productivos en desarrollo;
- acciones administrativas trazables.

`[BLOQUEANTE]` Una accion privada o sensible sin ownership backend no puede
lanzarse.

## 21. Logs, observabilidad y auditoria

La arquitectura tecnica de observabilidad y operacion pertenece a
`17_OBSERVABILITY_AND_OPERATIONS`.

Ese documento gobierna eventos operativos, logging estructurado, request
context, health, metricas, alertas, runbooks y separacion entre observabilidad,
auditoria, analytics y evidencia de backup/restore.

No registrar innecesariamente:

- contrasenas;
- tokens;
- cookies de sesion;
- contenido completo de mensajes;
- documentos;
- coordenadas exactas;
- datos sensibles;
- archivos;
- cabeceras de autenticacion;
- cuerpos completos de formularios.

Permitido con minimizacion:

- request ID;
- endpoint;
- codigo;
- duracion;
- usuario seudonimizado cuando sea necesario;
- recurso;
- error sanitizado;
- version;
- ambiente.

Los logs deben tener responsable, acceso limitado, plazo de retencion,
eliminacion y proveedor documentado.

## 22. Backups, recuperacion, retencion y eliminacion

Antes del lanzamiento debe definirse:

- periodicidad;
- cifrado;
- copia fuera del servidor principal;
- acceso limitado;
- retencion;
- rotacion;
- integridad;
- prueba de restauracion;
- RPO;
- RTO;
- procedimiento de desastre.

La definicion tecnica y operativa de tablas criticas, RPO/RTO, backup, restore
y validacion de schema pertenece a `16_DATA_INTEGRITY_AND_RECOVERY`.

Al cierre de ETAPA 92 existen herramientas oficiales de backup y restore seguro
sobre base temporal, un backup oficial ejecutado y un restore real validado con
evidencia operativa fuera del repositorio. La definicion tecnica completa,
incluyendo rutas, manifiestos, mediciones y riesgos diferidos, pertenece a
`16_DATA_INTEGRITY_AND_RECOVERY`.

Este control tecnico no equivale todavia a cumplimiento operativo maduro. Antes
del lanzamiento publico deben resolverse automatizacion periodica, copia externa
cifrada, retencion operativa real, monitoreo, pruebas recurrentes de restore y,
si se requiere un RPO menor, evaluacion de PITR/binlogs.

La baja de cuenta y la supresion de datos no son necesariamente identicas.

El flujo debe explicar que contenido se elimina, despublica, anonimiza,
bloquea o conserva por obligaciones, seguridad, fraude, denuncias o disputas.

`[BLOQUEANTE]` No se debe prometer eliminacion inmediata de todo si existen
backups o retenciones justificadas.

## 23. Incidentes, requerimientos de autoridad y crisis

Antes del lanzamiento debe existir un plan minimo de incidentes.

Debe contemplar:

- canal de reporte;
- responsables;
- severidad;
- contencion;
- preservacion de evidencia;
- cambio de secretos;
- revocacion;
- alcance;
- datos afectados;
- terceros;
- comunicacion;
- correccion;
- aprendizaje.

Los requerimientos de autoridad deben tener procedimiento aprobado, verificacion
de legitimidad, registro y revision legal cuando corresponda.

## 24. App stores y plataformas de distribucion

Antes de publicar una app movil se debe verificar:

- Google Play Data Safety;
- Google Play User Data;
- Google Play Permissions;
- Google Play Families, si aplica;
- Apple App Privacy Details;
- Apple Review Guideline 5.1;
- App Tracking Transparency, si aplica;
- eliminacion de cuenta dentro de la app cuando corresponda;
- coherencia entre permisos reales, politica publica y declaracion de tienda.

`[BLOQUEANTE]` No puede publicarse una app movil si las declaraciones de la
tienda contradicen el uso tecnico real.

## 25. Documentos publicos obligatorios

Este documento no reemplaza documentos publicos. Debe gobernar su existencia,
versionado, aprobacion y coherencia.

Documentos a preparar segun alcance:

- Terminos y Condiciones;
- Politica de Privacidad;
- Normas de la Comunidad;
- Politica de Moderacion;
- Politica de Cookies o tecnologias equivalentes;
- Politica de IA;
- textos de consentimiento;
- avisos cortos por funcionalidad;
- textos de baja, arrepentimiento o soporte cuando apliquen.

`[BLOQUEANTE]` No puede lanzarse una funcionalidad publica sensible sin el
documento publico aplicable y versionado.

## 26. Controles bloqueantes generales

La implementacion o lanzamiento queda bloqueado si:

- no existe dueno interno;
- no existe finalidad documentada;
- no se identificaron datos personales;
- no se definio fundamento o consentimiento aplicable;
- no se separaron consentimientos opcionales;
- falta mecanismo de revocacion;
- falta retencion;
- falta eliminacion;
- existe proveedor no auditado;
- existe transferencia internacional no evaluada;
- se solicita permiso sin finalidad clara;
- se usa ubicacion precisa sin alternativa;
- afecta menores sin politica aprobada;
- expone contenido publico sin moderacion minima;
- permite comunicaciones comerciales sin opt-in u opt-out;
- usa WhatsApp, email o push externo sin proveedor y baja;
- usa IA con datos personales sin revision;
- modifica ownership o permisos sin validacion backend;
- genera logs con datos sensibles;
- falta documento publico aplicable;
- falta evidencia de aceptacion cuando corresponde;
- introduce pagos, reservas o productos sin revision legal;
- contradice el roadmap, `02_PRODUCT.md`, decisiones permanentes o este
  documento.

## 27. Matrices de gobierno

Las matrices son plantillas reutilizables. No deben completarse con datos
ficticios.

### 27.1 Matriz de tratamientos

| ID | Funcion | Datos | Finalidad | Obligatorio/Opcional | Fuente | Usuario afectado | Visibilidad | Dueno interno | Documento publico |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### 27.2 Matriz de bases legales

| Tratamiento | Fundamento | Requiere consentimiento | Excepcion aplicable | Riesgo | Revision legal | Evidencia requerida |
| --- | --- | --- | --- | --- | --- | --- |

### 27.3 Matriz de consentimientos

| Consentimiento | Finalidad | Pantalla | Texto/version | Obligatorio/Opcional | Revocable | Metodo de revocacion | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 27.4 Matriz de retencion

| Dato | Tratamiento | Plazo activo | Plazo bloqueado | Backup | Motivo de conservacion | Eliminacion/anonimizacion |
| --- | --- | --- | --- | --- | --- | --- |

### 27.5 Matriz de permisos del dispositivo

| Permiso | Funcion | Momento de solicitud | Alternativa sin permiso | Plataforma | Riesgo | Texto previo | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 27.6 Matriz de proveedores

| Proveedor | Servicio | Datos tratados | Rol | Pais | Subencargados | Contrato | Seguridad | Salida | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### 27.7 Matriz de transferencias internacionales

| Proveedor | Pais | Datos | Fundamento/Garantia | Riesgo | Medida contractual | Aprobacion legal |
| --- | --- | --- | --- | --- | --- | --- |

### 27.8 Matriz de riesgos

| Funcion | Riesgo legal | Riesgo usuario | Riesgo empresa | Probabilidad | Impacto | Mitigacion | Bloqueante |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 27.9 Matriz RACI

| Proceso | Ingenieria | Producto | Seguridad | Compliance | Legal | Direccion |
| --- | --- | --- | --- | --- | --- | --- |

### 27.10 Matriz de documentos publicos

| Documento | Estado | Dueno | Revision legal | Version | Fecha | Funciones cubiertas |
| --- | --- | --- | --- | --- | --- | --- |
| Terminos y Condiciones | Superficie publica implementada; no habilitada para lanzamiento hasta completar datos institucionales y formalizacion | Legal/Compliance; version tecnica en backend Usuarios | Aprobacion del sistema confirmada; evidencia formal pendiente | `v1` | `[PENDIENTE DE FORMALIZACION]` | cuenta, uso, espacios, contenido, ubicacion y proveedores |
| Politica de Privacidad | Superficie publica implementada; no habilitada para lanzamiento hasta completar responsable, contacto, derechos y retencion | Legal/Compliance; version tecnica en backend Usuarios | Aprobacion del sistema confirmada; evidencia formal pendiente | `v1` | `[PENDIENTE DE FORMALIZACION]` | tratamientos reales, ubicacion, geocoding, Search, logs, seguridad y derechos |

### 27.11 Matriz de incidentes

| Tipo | Severidad | Responsable | Evidencia | Comunicacion | Plazo interno | Accion minima |
| --- | --- | --- | --- | --- | --- | --- |

### 27.12 Matriz de IA

| Uso IA | Datos fuente | Dato derivado | Usuario afectado | Explicabilidad | Revision humana | Entrenamiento | Riesgo |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 28. Checklists

### 28.1 Checklist previo a funcionalidad sensible

- [ ] Necesidad de producto documentada.
- [ ] Usuarios afectados identificados.
- [ ] Datos personales identificados.
- [ ] Datos opcionales identificados.
- [ ] Finalidad definida.
- [ ] Fundamento o consentimiento definido.
- [ ] Consentimientos opcionales separados.
- [ ] Revocacion definida.
- [ ] Retencion definida.
- [ ] Eliminacion definida.
- [ ] Ownership backend definido.
- [ ] Permisos identificados.
- [ ] Proveedores y paises identificados.
- [ ] Menores evaluados.
- [ ] Consumidor evaluado.
- [ ] Fraude y abuso evaluados.
- [ ] Moderacion evaluada.
- [ ] Seguridad evaluada.
- [ ] Logs revisados.
- [ ] Documentos publicos afectados identificados.
- [ ] Puntos de revision legal marcados.
- [ ] No existen bloqueantes abiertos.

### 28.2 Checklist previo al lanzamiento

- [ ] Responsable legal definido.
- [ ] Domicilio legal definido.
- [ ] Contacto de privacidad.
- [ ] Contacto de soporte.
- [ ] Terminos revisados.
- [ ] Politica de Privacidad revisada.
- [ ] Normas de Comunidad.
- [ ] Politica de Moderacion.
- [ ] Politica de eliminacion.
- [ ] Inventario de tratamientos.
- [ ] Bases registradas cuando corresponda.
- [ ] Proveedores auditados.
- [ ] Transferencias evaluadas.
- [ ] Retencion definida.
- [ ] Derechos de usuarios operativos.
- [ ] Menores resuelto.
- [ ] Ownership validado.
- [ ] Secretos protegidos.
- [ ] HTTPS.
- [ ] Rate limiting.
- [ ] Logs seguros.
- [ ] Backups.
- [ ] Restore probado.
- [ ] Plan de incidentes.
- [ ] Denuncias y moderacion.
- [ ] Soporte.
- [ ] Observabilidad.
- [ ] Rollback.
- [ ] ETAPA 96 cerrada y gate PWA aprobado.
- [ ] Piloto controlado aprobado.

### 28.3 Checklist previo a proveedores externos

- [ ] Identidad contractual.
- [ ] Finalidad.
- [ ] Datos.
- [ ] Pais.
- [ ] Subencargados.
- [ ] Seguridad.
- [ ] Retencion.
- [ ] Borrado.
- [ ] Incidentes.
- [ ] Transferencias.
- [ ] Exportacion.
- [ ] Costos.
- [ ] Limites.
- [ ] Consentimiento si corresponde.
- [ ] Politica publica actualizada.
- [ ] Aprobacion juridica y tecnica.

### 28.4 Checklist previo a app movil

- [ ] Permisos reales inventariados.
- [ ] Declaracion Google Play Data Safety coherente.
- [ ] Declaracion Apple App Privacy coherente.
- [ ] Purpose strings claros.
- [ ] Eliminacion de cuenta disponible cuando corresponda.
- [ ] ATT evaluado.
- [ ] Familias/menores evaluado.
- [ ] SDKs auditados.

### 28.5 Checklist previo a IA

- [ ] Uso de IA clasificado.
- [ ] Datos fuente identificados.
- [ ] Datos derivados identificados.
- [ ] Proveedor identificado.
- [ ] Transferencia evaluada.
- [ ] Entrenamiento definido.
- [ ] Exclusion de datos privados evaluada.
- [ ] Explicabilidad definida.
- [ ] Revision humana definida si corresponde.
- [ ] Riesgo de sesgo evaluado.
- [ ] Politica de IA requerida identificada.

## 29. Control de vigencia y revision periodica

Este documento debe revisarse:

- antes del lanzamiento publico;
- cada 6 meses;
- ante cambios normativos relevantes;
- antes de integrar proveedores criticos;
- antes de pagos;
- antes de IA sensible;
- antes de app movil;
- antes de permitir menores;
- antes de comunicaciones externas masivas.

La revision debe consultar fuentes oficiales vigentes y registrar fecha,
responsable y cambios.

## 30. Exclusiones y limites

Este documento:

- no implementa funcionalidades;
- no crea tablas;
- no aprueba proveedores;
- no define precios;
- no autoriza pagos;
- no redacta textos publicos definitivos;
- no reemplaza asesoramiento legal;
- no garantiza cumplimiento juridico;
- no aprueba lanzamiento publico por si solo.

## 31. Fuentes normativas y politicas externas a verificar

Las fuentes deben consultarse en su version oficial vigente antes de cada
revision:

- Ley 25.326 de Proteccion de los Datos Personales;
- Decreto 1558/2001;
- obligaciones y guias de la AAIP para responsables;
- derechos de titulares de datos personales;
- Resolucion AAIP 47/2018 sobre medidas de seguridad recomendadas;
- Resolucion AAIP 132/2018 sobre inscripcion, modificacion y baja de bases;
- Resolucion AAIP 14/2018 sobre informacion y leyenda de autoridad de control;
- guias y documentos AAIP de proteccion de datos e IA responsable;
- regimen de transferencias internacionales de datos personales;
- Ley 26.951 y normativa complementaria del Registro Nacional No Llame;
- Ley 26.061 de proteccion integral de ninas, ninos y adolescentes;
- Ley 24.240 de Defensa del Consumidor;
- Codigo Civil y Comercial de la Nacion en materia de contratos de consumo y
  contratacion a distancia;
- Resolucion 270/2020 sobre comercio electronico;
- Disposicion 954/2025 sobre boton de arrepentimiento y baja;
- Disposicion 3/2026 sobre verificacion razonable de identidad;
- normativa de propiedad intelectual, marcas y derecho de imagen aplicable;
- normativa penal e informatica aplicable a incidentes, fraude y acceso
  indebido;
- Google Play Developer Policies;
- Apple App Store Review Guidelines;
- politicas de proveedores externos que FeedGo integre.

Una fuente historica, nota periodistica, resumen privado o memoria de trabajo no
debe prevalecer sobre la fuente oficial vigente.

## 32. Control de cambios del documento

Todo cambio futuro debe registrar:

- fecha;
- responsable;
- motivo;
- secciones afectadas;
- fuentes revisadas;
- decision asociada;
- si requiere actualizacion de documentos publicos;
- si requiere revision legal externa.

No debe modificarse este documento para justificar una implementacion ya
realizada sin auditar el impacto y registrar la decision.
