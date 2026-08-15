# Integridad de Datos, Backups y Recuperacion

Estado del documento: Documento Oficial del Sistema de Gobierno FeedGo v1.0.
Version: 1.0.
Categoria: Documento tecnico-operativo transversal.
Nivel de autoridad: Alto para integridad de datos, backup, restore y
recuperacion operativa.
Documento dueno: `docs/16_DATA_INTEGRITY_AND_RECOVERY.md`.
Responsable funcional: Ingenieria, seguridad operativa y operacion.
Documentos relacionados: `00_GOVERNANCE.md`, `01_ENGINEERING.md`,
`04_CURRENT_STAGE.md`, `05_SEARCH_ROADMAP.md`,
`08_ENGINEERING_PRINCIPLES.md`, `15_LEGAL_AND_OPERATIONAL.md`,
`17_OBSERVABILITY_AND_OPERATIONS.md`.
Cuando debe consultarse: antes de modificar scripts de base de datos,
procedimientos de backup, restore, retencion, recuperacion, validaciones de
schema fisico o cualquier operacion que pueda afectar datos persistentes.

Este documento gobierna la integridad fisica y operativa de los datos de
FeedGo.

No reemplaza `15_LEGAL_AND_OPERATIONAL`, que gobierna riesgos legales,
privacidad, retencion y operacion desde la perspectiva legal y de compliance.

No contiene dumps, credenciales, secretos ni procedimientos con contrasenas.

## 1. Estado de ETAPA 92

### 1.1 Sprint 92.1

Estado: cerrado.

Alcance:

- `create_tables.py` queda protegido contra efectos laterales al importar.
- `reset_db.py` queda protegido contra ejecucion destructiva accidental.
- `check_database_schema.py` queda disponible como verificacion read-only.
- Se define una matriz inicial de tablas criticas.
- Se documentan RPO/RTO iniciales.
- Se documentan procedimientos conceptuales para backup y restore futuros.

### 1.2 Subetapas

- 92.2 - Estrategia y herramienta de backup: cerrada.
- 92.3 - Restore seguro y prueba de recuperacion: cerrada.
- 92.3A - Arquitectura extensible de backup/restore: cerrada.
- 92.4 - Prueba real de backup, alineacion y restore temporal: cerrada.
- 92.5 - Cierre documental y operativo: cerrada.

## 2. Estado operativo actual

Auditoria inicial:

- Base configurada: MySQL local `mitienda`.
- Metadata SQLAlchemy registrada: 27 tablas.
- Base fisica inspeccionada: 27 tablas.
- Tablas faltantes: ninguna.
- Tablas extra: ninguna.
- Backups reales verificables: ejecutados desde el procedimiento oficial.
- Ultimo backup verificable:
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz`.
- Manifiesto verificable:
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz.json`.
- Restore probado: ejecutado en base temporal y validado.
- Evidencia de restore exitoso:
  `C:\FeedGoOps\restore_tmp\evidence\feedgo_restore_tmp_20260801_183100_20260801T182747Z_restore.json`.
- Procedimiento operativo de backup: implementado, ejecutado y validado.
- Procedimiento operativo de restore: implementado, ejecutado y validado sobre
  base temporal.
- Arquitectura extensible de backup/restore: implementada y validada con los
  providers iniciales.
- Binlogs MySQL: disponibles en el entorno auditado, pero no reemplazan
  backups.

Riesgo principal:

FeedGo cuenta con una primera evidencia real de backup y restore, pero no debe
considerarse operativamente maduro hasta implementar automatizacion periodica,
copia externa cifrada, retencion monitoreada y pruebas recurrentes.

## 3. Objetivos RPO/RTO iniciales

### 3.1 Prelanzamiento

- RPO maximo objetivo: 24 horas.
- RTO maximo objetivo: 4 horas.

### 3.2 Lanzamiento controlado

- RPO maximo objetivo: 6 horas o menos.
- RTO maximo objetivo: 2 horas.

Estos valores son objetivos operativos iniciales.

Al cierre de ETAPA 92 existe una medicion real inicial:

- RTO observado del restore temporal y validacion: 3.336 s.
- Antiguedad observada del punto recuperado al iniciar el restore: ~13 minutos.

La antiguedad del punto recuperado no constituye RPO garantizado. El RPO solo
podra declararse cumplido cuando existan ejecucion periodica, retencion real,
monitoreo, evidencia recurrente y politica operativa aprobada.

Los binlogs pueden ayudar a reducir RPO, pero no sustituyen backups completos,
verificables y restaurables.

## 4. Matriz de tablas criticas

| Dominio | Tabla | Criticidad | Dueno natural | Tipo de dato | Borrado | Dependencias | Prioridad de backup | Observaciones |
| ------- | ----- | ---------- | ------------- | ------------ | ------- | ------------ | ------------------- | ------------- |
| Usuarios | `usuarios` | critica | Usuario | identidad, credenciales, perfil privado | fisico restringido por dependencias y cascadas | comercios, social, embeddings, aceptaciones, denuncias | critica | No regenerable. Contiene datos personales y credenciales hasheadas. |
| Comercios | `comercios` | critica | Comercio | perfil comercial publico y ownership | soft delete por `activo`; FK con cascadas fisicas | publicaciones, historias, horarios, agenda, metricas, embeddings | critica | No regenerable; eje de ownership. |
| Publicaciones | `publicaciones` | critica | Publicacion | contenido publico/comercial | soft delete por `is_activa`; cascada al borrar comercio | historias, likes, guardados, feed, busqueda | critica | No regenerable; contenido visible. |
| Historias | `historias` | alta | Historia | contenido publico temporal | soft delete por `is_activa`; expiracion; cascada al borrar comercio | vistas, likes, denuncias | alta | Media publica; puede vencer pero no es automaticamente regenerable. |
| Legal | `usuarios_documentos_aceptaciones` | critica | Evidencia legal de usuario | evidencia versionada | sin cascade explicita; debe preservarse | usuarios | critica | Legalmente sensible; no inventar registros retroactivos. |
| Moderacion | `contenido_denuncias` | alta | Denuncia | senal de contenido reportado | sin cascade explicita; debe preservarse operativamente | usuarios, recursos polimorficos por tipo/id | alta | No es decision de moderacion; denunciante protegido. |
| Agenda | `agenda_contextos_agendables` | critica | Agenda Core | contexto privado de agenda | restringido por elementos/integracion | agenda_elementos, feedgo_agenda_contextos | critica | No regenerable; relaciona agenda con dominio consumidor. |
| Agenda | `agenda_elementos` | critica | Agenda Core | eventos, tareas, bloqueos | `RESTRICT` hacia contexto | agenda_contextos_agendables | critica | Check fisico de rango temporal. |
| FeedGo Agenda | `feedgo_agenda_contextos` | critica | FeedGo Agenda | integracion comercio-agenda | `RESTRICT` | comercios, agenda_contextos_agendables | critica | Une comercio y agenda sin duplicar datos. |
| Disponibilidad | `comercios_horarios_atencion` | alta | Disponibilidad | horarios operativos | cascada al borrar comercio | comercios | alta | Operativo; reconstruccion manual costosa. |
| Social | `likes_publicaciones` | media | Senal social | interes de usuario | cascada por usuario/publicacion | usuarios, publicaciones | media | Regenerable solo por accion futura del usuario; perdida afecta ranking. |
| Social | `publicaciones_guardadas` | alta | Usuario | guardados personales | cascada por usuario/publicacion | usuarios, publicaciones | alta | Preferencia personal no regenerable automaticamente. |
| Social | `seguidores` | alta | Relacion usuario-comercio | seguimiento | fisico; sin ondelete explicito fisico actual | usuarios, comercios | alta | Relacion personal relevante para UX y metricas. |
| Stories Social | `historias_vistas` | media | Senal de historia | vista de usuario | cascada por usuario/historia | usuarios, historias | media | Historico operacional; puede perderse si se acepta perdida de analytics. |
| Stories Social | `historias_likes` | media | Senal de historia | reaccion | cascada por usuario/historia | usuarios, historias | media | Afecta metricas e interaccion. |
| Taxonomia | `rubros` | alta | Taxonomia comercial | categorias comerciales | logico por `activo` | comercios, productos | alta | Puede reseedearse parcialmente, pero cambios reales pueden perderse. |
| Taxonomia | `taxonomy_nodes` | alta | Knowledge/Discovery | grafo/taxonomia | logico por `activo` | taxonomy_assignments | alta | Derivado parcialmente, pero curacion puede perderse. |
| Taxonomia | `taxonomy_assignments` | alta | Discovery | asignaciones a entidades | fisico | taxonomy_nodes, recursos | alta | Recalculable parcialmente; perdida degrada discovery. |
| Productos legacy | `productos` | media | Productos legacy | producto heredado | fisico/desconocido | rubros | media | Dominio diferido a ETAPA 104; conservar hasta decision. |
| Secciones | `secciones` | media | Comercio | organizacion de comercio | cascada al borrar comercio | publicaciones | media | Puede afectar orden/organizacion del perfil. |
| Busqueda | `search_events` | media | Search/Knowledge | eventos de busqueda | acumulativo | analytics, aprendizaje | media | Historico de aprendizaje; perdida afecta metricas futuras. |
| Knowledge | `knowledge_proposals` | alta | Knowledge | propuestas de conocimiento | operativo | graph/workspace | alta | Curacion no necesariamente regenerable. |
| Analytics | `comercios_metricas_sociales` | regenerable | Analytics | agregados actuales | derivado | comercios, publicaciones, social, historias | media | Recalculable si sobreviven fuentes. |
| Analytics | `comercios_metricas_snapshots` | media | Analytics | historico agregado | acumulativo | comercios, senales | media | Snapshots historicos no se reconstruyen perfectamente. |
| IA | `comercios_embeddings` | regenerable | IA/Discovery | vector derivado | derivado | comercios | baja | Recalcular desde fuente y modelo. |
| IA | `usuarios_embeddings` | media | IA/Usuario | vector derivado de usuario | cascada por usuario | usuarios | media | Derivado, pero puede reflejar preferencias historicas. |
| Seguridad | `tokens_revocados` | media | Seguridad | tokens invalidados | temporal | usuarios | media | Perdida puede reactivar tokens hasta expiracion si no hay otra defensa. |

## 5. Matriz de borrado e integridad

| Relacion | FK / integridad | Comportamiento | Riesgo | Recomendacion futura |
| -------- | --------------- | -------------- | ------ | -------------------- |
| Usuario -> Comercio | `comercios.usuario_id` | `CASCADE` fisico en MySQL | borrar usuario puede borrar comercios y contenido derivado | Definir baja de cuenta antes de habilitar eliminacion real. |
| Comercio -> Publicaciones | `publicaciones.comercio_id` | `CASCADE` | borra contenido publico y senales derivadas | Mantener soft delete operativo salvo decision documentada. |
| Comercio -> Historias | `historias.comercio_id` | `CASCADE` | borra historias, vistas y likes | Revisar ciclo de vida de medios antes de borrado fisico. |
| Comercio -> Horarios | `comercios_horarios_atencion.comercio_id` | `CASCADE` | perdida de disponibilidad operativa | Cubrir en backups criticos. |
| Comercio -> FeedGo Agenda | `feedgo_agenda_contextos.comercio_id` | `RESTRICT` | bloquea borrado si hay agenda vinculada | Correcto para evitar perdida silenciosa; requiere procedimiento de baja. |
| Agenda Contexto -> Elementos | `agenda_elementos.contexto_id` | `RESTRICT` | evita borrar agenda con elementos | Correcto; mantener procedimiento explicito. |
| Publicacion -> Likes | `likes_publicaciones.publicacion_id` | `CASCADE` | perdida de senales de ranking/interes | Validar en ETAPA 94. |
| Publicacion -> Guardados | `publicaciones_guardadas.publicacion_id` | `CASCADE` | perdida de preferencias personales | Validar en ETAPA 94. |
| Publicacion -> Historias | `historias.publicacion_id` | `SET NULL` | conserva historia desvinculada | Correcto, pero revisar experiencia publica. |
| Usuario -> Aceptaciones | `usuarios_documentos_aceptaciones.usuario_id` | sin `ondelete` explicito | puede bloquear baja fisica de usuario | Debe gobernarse por privacidad, retencion y procedimiento de baja. |
| Usuario -> Denuncias | `contenido_denuncias.usuario_id` | sin `ondelete` explicito | puede bloquear baja fisica de usuario | Debe definirse retencion por moderacion/legal. |
| Taxonomia -> Asignaciones | `taxonomy_assignments.node_id` | FK sin cascade fisica auditada | posible bloqueo o perdida de asignaciones segun flujo | Definir procedimiento de cambios taxonomicos. |
| Seccion -> Publicaciones | `publicaciones.seccion_id` | `SET NULL` | mantiene publicacion sin seccion | Correcto para evitar perdida de contenido. |

## 6. Procedimiento conceptual para backup - ETAPA 92.2

Herramienta oficial inicial: `mysqldump` de MySQL.

Script oficial:

```powershell
cd backend
.\venv\Scripts\python.exe backup_database.py
```

Modulo operativo:

- `app/core/database_backup.py`

Variables requeridas:

- `FEEDGO_MYSQL_DEFAULTS_FILE`: ruta a archivo seguro de credenciales MySQL.

Variables opcionales:

- `FEEDGO_BACKUP_DIR`: directorio de salida. Valor por defecto:
  `backups/mysql`.
- `FEEDGO_BACKUP_RETENTION_DAYS`: dias de retencion local. Valor por defecto:
  `14`.
- `FEEDGO_BACKUP_KEEP_LAST`: minimo de backups recientes a conservar. Valor por
  defecto: `10`.
- `FEEDGO_MYSQLDUMP_BIN`: binario de `mysqldump`. Valor por defecto:
  `mysqldump`.

El archivo de credenciales debe quedar fuera de Git y no debe imprimirse.

El comando construido por el script debe incluir:

- `--defaults-extra-file=<archivo-seguro>`;
- `--host=<host-sin-secreto>`;
- `--single-transaction`;
- `--routines`;
- `--events`;
- `<base>`.

No debe incluir `--databases` en el formato oficial inicial. El dump debe poder
restaurarse sobre una base temporal elegida por el procedimiento de restore, sin
sentencias `CREATE DATABASE` o `USE` que apunten a la base runtime original.

Salida generada:

- archivo `.sql.gz`;
- manifiesto `.sql.gz.json`;
- hash SHA-256 del archivo comprimido;
- duracion;
- tamano;
- restaurabilidad;
- ausencia de sentencias de base de datos;
- conteos de tablas criticas;
- resultado;
- estado de copia externa `prepared_not_implemented`.

Retencion y rotacion:

- se conservan los backups dentro de la retencion configurada;
- se conserva siempre al menos `FEEDGO_BACKUP_KEEP_LAST`;
- el manifiesto asociado se elimina junto con el backup rotado.

El procedimiento debera definir:

- ejecucion desde entorno autorizado;
- credenciales por archivo seguro o variables de entorno, nunca en comandos
  versionados;
- dump transaccional consistente para InnoDB;
- inclusion de estructura, datos, rutinas/eventos si aplican;
- nombre con fecha UTC, entorno y base;
- compresion;
- cifrado;
- salida local temporal fuera del repositorio;
- copia externa fuera del servidor principal;
- retencion y rotacion;
- log operativo sin secretos;
- verificacion de exit code y tamano esperado;
- hash del archivo de backup;
- registro de duracion;
- control de acceso.

Comando conceptual sin secretos:

```powershell
mysqldump --defaults-extra-file=<archivo-seguro> --single-transaction --routines --events <base> | gzip > <ruta-segura>
```

Estado al cierre de 92.2:

- la herramienta esta implementada y testeada con mocks;
- el formato fue ajustado para ser restaurable en bases temporales controladas;
- el manifiesto registra conteos criticos para comparacion posterior;
- se ejecuto backup real contra MySQL local `mitienda` durante 92.4;
- existe evidencia operativa de backup exitoso fuera del repositorio;
- la copia externa queda preparada, no implementada;
- la restauracion real fue validada durante 92.4 sobre base temporal.

## 7. Procedimiento operativo para restore - ETAPA 92.3

Script oficial:

```powershell
cd backend
.\venv\Scripts\python.exe restore_database.py
```

Modulo operativo:

- `app/core/database_restore.py`

Variables requeridas:

- `FEEDGO_RESTORE_BACKUP_FILE`: ruta del archivo `.sql.gz`.
- `FEEDGO_RESTORE_MANIFEST_FILE`: ruta del manifiesto `.json`.
- `FEEDGO_RESTORE_TARGET_DATABASE`: base temporal destino.
- `FEEDGO_MYSQL_DEFAULTS_FILE`: archivo seguro de credenciales MySQL.

Variables opcionales:

- `FEEDGO_RESTORE_EVIDENCE_DIR`: directorio de evidencia. Valor por defecto:
  `restore_tmp/evidence`.
- `FEEDGO_MYSQL_BIN`: binario de cliente MySQL. Valor por defecto: `mysql`.

Reglas implementadas:

- restaurar primero siempre en una base temporal;
- no sobrescribir directamente `mitienda`;
- aceptar solo bases con nombre `feedgo_restore_tmp_*`;
- rechazar bases existentes para no sobrescribir datos;
- validar existencia de backup y manifiesto;
- validar gzip;
- validar SHA-256 contra el manifiesto;
- exigir manifiesto restaurable sin sentencias de base de datos;
- crear la base temporal;
- aplicar dump mediante cliente MySQL;
- ejecutar `check_database_schema.py` de forma read-only sobre el destino;
- comparar conteos de tablas criticas contra el manifiesto;
- medir duracion real de restauracion;
- generar evidencia JSON con resultado, errores, schema, conteos y duracion;
- no limpiar la base temporal automaticamente.

Limpieza explicita:

La base temporal solo se elimina cuando se invoca explicitamente:

```powershell
$env:FEEDGO_RESTORE_CLEANUP_DATABASE="feedgo_restore_tmp_<nombre>"
$env:FEEDGO_RESTORE_CLEANUP_CONFIRMATION="DROP_RESTORE_TEMP_DB"
.\venv\Scripts\python.exe restore_database.py
```

Estado al cierre de 92.3:

- la herramienta esta implementada y testeada con mocks;
- se ejecuto restore real contra MySQL sobre base temporal controlada durante
  92.4;
- existe evidencia operativa de restore exitoso fuera del repositorio;
- PITR con binlogs queda fuera de alcance;
- la limpieza real de bases temporales queda bajo accion explicita.

## 7.1 Arquitectura extensible de backup/restore - ETAPA 92.3A

Objetivo:

Desacoplar los servicios operativos de backup y restore de las herramientas
concretas usadas inicialmente, sin cambiar el comportamiento vigente.

Contratos implementados:

- `BackupProvider`: ejecuta la generacion fisica del backup.
- `RestoreProvider`: ejecuta la aplicacion fisica del backup sobre el destino.
- `BackupStorage`: resuelve almacenamiento, manifiesto y rotacion.

Implementaciones iniciales:

- `MySQLDumpBackupProvider`: conserva `mysqldump` como herramienta inicial.
- `MySQLClientRestoreProvider`: conserva el cliente `mysql` para restore.
- `LocalBackupStorage`: conserva almacenamiento local, manifiestos y rotacion.

Reglas:

- `run_backup` y `restore_backup` siguen siendo los puntos operativos
  compatibles.
- Los servicios de backup y restore orquestan validacion, provider, storage,
  evidencia y conteos.
- Los providers no deben incorporar decisiones de roadmap, copia externa, PITR
  ni politicas de retencion que pertenecen a otros componentes.
- El storage local no equivale a copia externa.

Manifiesto versionado:

El manifiesto nuevo conserva compatibilidad con el formato previo y agrega:

- `format_version`;
- `provider`;
- `storage_provider`;
- `database_engine`;
- `engine_version`;
- `backup_type`;
- timestamps UTC;
- `checksum_algorithm`;
- `checksum`;
- `restore_requirements`;
- `binlog_coordinates` opcional.

Compatibilidad:

- El restore debe aceptar manifiestos previos mientras contengan gzip,
  SHA-256, ausencia de sentencias de base de datos, destino requerido y conteos
  criticos.
- La evolucion futura del manifiesto debe mantener versionado explicito y
  lectores compatibles hacia atras o migraciones documentadas.

Fuera de alcance de 92.3A:

- RDS;
- Percona;
- almacenamiento externo;
- PITR;
- copia externa;
- restore real;
- backup real;
- automatizacion periodica.

Los backups y restores reales fueron ejecutados posteriormente dentro del
alcance de 92.4, sin cambiar los contratos ni providers iniciales.

## 7.2 Arquitectura preparada para evolución

La arquitectura vigente queda preparada para evolucionar mediante contratos
estables y una implementacion concreta inicial por responsabilidad.

Estructura actual:

```text
BackupService
└── BackupProvider
    └── MySQLDumpBackupProvider

RestoreService
└── RestoreProvider
    └── MySQLClientRestoreProvider

BackupStorage
└── LocalBackupStorage

BackupVerifier
├── GzipVerifier
├── ChecksumVerifier
└── ManifestVerifier
```

Estas son las implementaciones iniciales del sistema. No implican que FeedGo
dependa permanentemente de `mysqldump`, del cliente `mysql` o del storage local.

Evolucion futura posible:

- `RdsSnapshotBackupProvider`;
- `PerconaXtraBackupProvider`;
- `RdsRestoreProvider`;
- `PerconaRestoreProvider`;
- `S3BackupStorage`;
- `BackblazeBackupStorage`;
- `AzureBlobBackupStorage`.

Estas implementaciones futuras no forman parte del alcance actual.

Reglas de evolucion:

- incorporar un nuevo provider no debe modificar la logica principal de los
  servicios de backup o restore;
- cada provider debe cumplir el contrato estable correspondiente;
- el manifiesto debe conservar compatibilidad mediante `format_version`;
- storage externo, snapshots administrados, Percona, RDS y PITR requieren etapa
  o decision futura aprobada antes de implementarse;
- la existencia de contratos no autoriza sobreingenieria ni implementaciones
  especulativas.

Controles completados en 92.4:

- ejecutar backup real controlado;
- ejecutar restore real en base temporal;
- verificar constraints, indices, uniques y FKs de forma profunda;
- ejecutar smoke checks de lectura sobre tablas criticas;
- medir tiempos reales de backup y restore;
- registrar evidencia JSON del restore;
- limpiar bases temporales con confirmacion explicita.

Controles diferidos:

- automatizar frecuencia de validacion;
- implementar copia externa cifrada;
- monitorear retencion real;
- evaluar uso de binlogs/PITR para reducir RPO sin reemplazar backups.

No se debe restaurar sobre `mitienda`.

## 7.3 Preparacion de prueba real - ETAPA 92.4A

Antes de ejecutar el primer backup y restore reales, deben quedar resueltos los
controles operativos minimos.

### Credenciales MySQL

FeedGo debe usar `FEEDGO_MYSQL_DEFAULTS_FILE` apuntando a un archivo seguro
fuera del repositorio.

El archivo:

- no debe versionarse;
- no debe ubicarse dentro de `C:\Mitienda`;
- no debe imprimirse en logs ni documentacion;
- debe tener permisos restringidos al usuario operativo local;
- debe poder leerse por `mysqldump` y por el cliente `mysql`;
- debe contener credenciales con privilegios minimos suficientes para backup,
  creacion de base temporal, restore y validaciones read-only.

Ruta recomendada:

```powershell
C:\FeedGoOps\secrets\mysql-backup.cnf
```

Verificacion segura, sin mostrar credenciales:

```powershell
Test-Path $env:FEEDGO_MYSQL_DEFAULTS_FILE
Get-Item $env:FEEDGO_MYSQL_DEFAULTS_FILE | Select-Object FullName,Length
```

No se debe crear este archivo desde codigo versionado.

### Rutas operativas reales

Backups reales:

```powershell
C:\FeedGoOps\backups\mysql
```

Evidencia de restore:

```powershell
C:\FeedGoOps\restore_tmp\evidence
```

Estas rutas quedan fuera del repositorio y deben mantenerse excluidas de Git.

### Controles tecnicos habilitados

- `mysqldump` debe ejecutarse con `--single-transaction` y `--quick`.
- `check_database_schema.py` debe mantenerse estrictamente read-only.
- La verificacion de schema debe comparar tablas, columnas, claves foraneas,
  indices y restricciones unicas.
- El restore real debe apuntar solo a bases `feedgo_restore_tmp_*`.
- La limpieza de la base temporal requiere accion explicita posterior.

## 7.4 Alineacion de schema - ETAPA 92.4C

Antes de la prueba oficial de backup y restore, metadata SQLAlchemy y schema
fisico deben quedar alineados o sus diferencias deben quedar justificadas.

Cambios de metadata aceptados:

- `knowledge_proposals.taxonomy_node_id` referencia `taxonomy_nodes.id`.
- `knowledge_proposals.reviewed_by_usuario_id` referencia `usuarios.id`.
- `knowledge_proposals.applied_by_usuario_id` referencia `usuarios.id`.
- `comercios.ciudad` queda expresado como indice aceptado.
- `secciones.activo` queda expresado como indice aceptado.
- `seguidores.comercio_id` queda expresado como indice aceptado.
- `tokens_revocados.usuario_id` queda expresado como indice aceptado.
- Los indices de `knowledge_proposals` asociados a sus FKs quedan expresados
  por metadata.

El checker debe distinguir indices fisicos implicitos por FK de divergencias
reales. Las FKs se validan como FKs; los indices de soporte de FK no deben
generar deuda duplicada cuando la integridad referencial esta correctamente
representada.

### FK fisica pendiente en `comercios.rubro_id`

La metadata define `comercios.rubro_id -> rubros.id`, pero la base fisica local
puede no contener esa FK. La alineacion fisica debe hacerse con el script
controlado:

```powershell
cd backend
.\venv\Scripts\python.exe add_comercios_rubro_fk.py
```

Ese comando ejecuta solo auditoria y no aplica `ALTER TABLE`.

Para aplicar la FK, primero debe existir un backup precautorio real y luego
debe ejecutarse con confirmacion explicita:

```powershell
$env:FEEDGO_SCHEMA_ALIGN_CONFIRMATION="ADD_COMERCIOS_RUBRO_FK"
.\venv\Scripts\python.exe add_comercios_rubro_fk.py
```

Reglas del script:

- no se ejecuta al importarlo;
- informa destino sin credenciales;
- verifica si la FK ya existe;
- verifica huérfanos inmediatamente antes del `ALTER`;
- aborta si hay inconsistencias;
- no borra ni modifica datos;
- no ejecuta `ALTER TABLE` sin confirmacion explicita.

Procedimiento obligatorio:

1. Alinear metadata.
2. Ejecutar tests.
3. Generar backup precautorio real.
4. Verificar huérfanos.
5. Ejecutar el script con confirmacion explicita.
6. Revalidar schema profundo.
7. Continuar con la prueba real de backup/restore solo si el checker queda
   consistente.

## 7.5 Prueba real de backup, alineacion y restore - ETAPA 92.4D

Estado: cerrada.

Entorno validado:

- Motor: MySQL local.
- Base runtime: `mitienda`.
- Metadata SQLAlchemy: 27 tablas.
- Base fisica: 27 tablas.
- Destino de backups: `C:\FeedGoOps\backups\mysql`.
- Destino de evidencia de restore: `C:\FeedGoOps\restore_tmp\evidence`.
- Credenciales: archivo externo referenciado por `FEEDGO_MYSQL_DEFAULTS_FILE`,
  sin versionar ni exponer secretos.

Backup precautorio:

- Se genero un backup precautorio valido antes de modificar schema fisico.
- El backup precautorio no debe eliminarse ni reemplazarse como evidencia de
  seguridad previa a la alineacion.

Alineacion fisica:

- Se verifico `comercios.rubro_id`.
- Se verifico que no existieran comercios huerfanos por rubro.
- Se agrego la FK fisica `comercios.rubro_id -> rubros.id` con el script
  controlado `add_comercios_rubro_fk.py` y confirmacion explicita.
- No se borraron ni modificaron datos de negocio.

Checker posterior:

- Tablas metadata: 27.
- Tablas fisicas: 27.
- Diferencias de columnas: ninguna.
- Diferencias de FKs: ninguna.
- Diferencias de indices: ninguna.
- Diferencias de uniques: ninguna.
- Exit code: 0.

Backup oficial:

- Archivo:
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz`.
- Manifiesto:
  `C:\FeedGoOps\backups\mysql\mitienda_20260801T181443Z.sql.gz.json`.
- Tamano: 147405 bytes.
- SHA-256:
  `70c7bd53002c6ac646891a989b1da96181cc1cdde3bef9d5f6b47e9667119970`.
- Duracion observada: 0.444 s.
- Resultado del manifiesto: `ok`.

Restore real temporal:

- Base temporal: `feedgo_restore_tmp_20260801_183100`.
- Evidencia:
  `C:\FeedGoOps\restore_tmp\evidence\feedgo_restore_tmp_20260801_183100_20260801T182747Z_restore.json`.
- Resultado: `ok`.
- Schema profundo: OK.
- Conteos criticos: coincidentes con manifiesto.
- Smoke checks de lectura: OK.
- RTO observado: 3.336 s.
- Antiguedad observada del punto recuperado al iniciar el restore: ~13 minutos.
  No debe declararse como RPO garantizado.

Limpieza:

- La base temporal se elimino con confirmacion explicita despues de aprobar las
  validaciones.
- No quedaron bases temporales activas.
- `mitienda` quedo intacta.

Riesgos diferidos:

- automatizacion periodica de backups;
- copia externa cifrada y verificada;
- retencion operativa real y monitoreada;
- PITR/binlogs;
- providers RDS, Percona o cloud;
- pruebas recurrentes de restore;
- monitoreo y alertas de ejecucion.

## 8. Seguridad de secretos y artefactos

Reglas:

- `.env` no debe versionarse.
- Dumps, backups, logs de backup y bases temporales no deben versionarse.
- Ningun comando documentado debe incluir contrasenas.
- Los scripts no deben imprimir credenciales.
- Los backups deben cifrarse antes de salir del servidor principal.
- El acceso a backups debe ser limitado y auditable.

Patrones que deben permanecer ignorados por Git:

- `*.sql`
- `*.sql.gz`
- `*.dump`
- `backups/`
- `restore_tmp/`

## 9. Validacion read-only de schema

La herramienta oficial inicial es:

```powershell
cd backend
.\venv\Scripts\python.exe check_database_schema.py
```

Debe informar:

- destino sin credenciales;
- cantidad de tablas en metadata;
- cantidad de tablas fisicas;
- tablas faltantes;
- tablas extra;
- diferencias de columnas;
- diferencias de claves foraneas;
- diferencias de indices;
- diferencias de restricciones unicas.

Debe finalizar con codigo distinto de cero si detecta diferencias.

No debe ejecutar `create_all`, `drop_all`, `ALTER`, `DROP`, `TRUNCATE`,
`DELETE`, backups ni restores.
