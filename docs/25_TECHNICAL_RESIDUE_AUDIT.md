# Auditoria integral de residuos tecnicos - ETAPA 95.7-B

Estado: completada. Este documento registra el gate de residuos de ETAPA 95;
no autoriza refactors generales ni cierra la etapa.

## 1. Alcance y evidencia

La auditoria partio de 479 archivos del repositorio (excluidos dependencias,
entornos virtuales, caches y artefactos reproducibles) y finalizo con 477 luego
de cuatro eliminaciones y dos evidencias permanentes nuevas. Relevo 370 archivos
de codigo productivo, 49 archivos de tests y 1.091 declaraciones/exportaciones
de nivel superior. Tambien clasifico cada archivo no versionado y reviso cada
archivo modificado del working tree.

La evidencia combino inventario Git, busquedas de referencias e imports,
barrels, rutas y carga indirecta, configuracion, tests, hashes de assets y una
consulta read-only de datos fisicos para `color_fondo`. Una coincidencia textual
ausente no se considero por si sola prueba suficiente para borrar codigo.

## 2. Clasificacion y acciones

### Conservar

- Los 49 tests protegen contratos permanentes; no se encontro un test temporal.
- `core/theme`, tokens, primitives, `interactive-bubble`, ActiveLayer,
  GeographicContext, geocoding y los documentos 18-24 tienen consumidores o
  valor contractual permanente.
- `backend/validate_geoapify_argentina.py` es una prueba operativa reproducible,
  no imprime secretos y valida el proveedor real con direcciones publicas.
- El service worker y manifest son scaffolding consumido por la aplicacion y
  pertenecen a ETAPA 96; no se adelanta su implementacion.
- CSS fisico de HistoriasViewer, scrims multimedia, branding de contenido y
  estilos del mapa son excepciones deliberadas, no residuos de tema.

### Mover / reubicar

- El transporte directo residual de perfil/publicaciones y la ubicacion de
  MainLayout ya registrados en `24_FRONTEND_OWNERSHIP_AUDIT` deben tratarse en
  un refactor de ownership con pruebas, no como limpieza destructiva.
- Branding visible historico `MiPlaza`/`MiTienda` en shell, manifest y mensajes
  debe resolverse desde owners de producto/PWA. Tiene consumidores reales y no
  admite reemplazo ciego durante este gate.

### Documentar

- `backend/migrate_comercios_location_visibility.py` es historial migratorio
  necesario en un repositorio sin Alembic: tiene upgrade/downgrade, modo
  audit-only y cobertura automatizada. Haber sido ejecutada no la vuelve
  descartable.
- Los aliases historicos de credencial y storage conservan compatibilidad de
  sesiones; retirarlos requiere una migracion explicita.
- Query keys literales de legal, availability y Explore/Seguidos debilitan el
  owner canonico, pero consolidarlas cambia invalidaciones y Cache-First.
- `color_fondo` ya no es editable desde ProfilePage, pero sigue en model,
  schemas y service backend. La base fisica contiene 3 valores no nulos sobre
  12 usuarios; retirarlo requiere cambio de contrato y migracion de datos.
- El manifest aun referencia `vite.svg`; es deuda de PWA, no un asset huerfano.
- Los cuatro warnings de hooks restantes requieren pruebas funcionales antes
  de cambiar dependencias: AuthContext, ProfilePage, RankingPage y
  PerfilComercioPage.
- El chunk principal, Browserslist y Leaflet permanecen como deuda de build,
  no como residuos eliminables.

### Eliminar

| Elemento | Evidencia | Accion / riesgo |
| --- | --- | --- |
| `public/favicon.png` | cero referencias; hash identico a `icon-180.png` | eliminado; reemplazo productivo existente |
| `public/logo_miplaza.png` | cero consumidores; hash identico a `icon-180.png` | eliminado; sin impacto runtime |
| `public/logo_miplaza2.png` | cero consumidores | eliminado; sin impacto runtime |
| `src/assets/react.svg` | cero imports; asset starter de Vite | eliminado; sin impacto runtime |
| log de registro exitoso del SW | solo debugging de exito | eliminado; se conserva error operativo |
| handlers install/activate del SW | solo imprimian logs, sin efecto de cache | eliminados; fetch/scaffold preservado |
| export `horariosAtencionQueryKeys` | sus tres consumidores estan en el mismo modulo | convertido a constante privada |

Todos los residuos categoria D encontrados fueron retirados. Quedan cero
residuos reales demostrados pendientes; las entradas documentadas son deuda o
compatibilidad con consumidores reales, no residuos silenciosamente tolerados.

## 3. Geocoding y migraciones

No existe codigo activo de Nominatim. Sus unicas referencias son historia,
documentacion y pruebas antirregresion. El flujo productivo unico es frontend
`geocoding_service` -> backend -> provider configurado; Geoapify permanece
activo, desacoplado y probado.

La migracion de privacidad de ubicacion debe permanecer versionada. Su script y
tests son el mecanismo reproducible para auditar metadata/base fisica y no se
absorben en un `create_all` destructivo.

## 4. Barrels, helpers, logs y nombres

El barrel Auth ya habia cerrado su export interno en 95.7-A. En 95.7-B se
redujo solamente la exportacion accidental demostrable de availability; los
demas `export *` sostienen APIs publicas o consumo indirecto y no se reducen por
preferencia estilistica.

No se encontraron helpers/componentes sin consumidores con evidencia suficiente
para eliminarlos, TODO/FIXME nuevos, dumps, capturas, mocks temporales ni codigo
comentado de diagnostico. Los `print` de scripts CLI y logs de error/seguridad
son salidas operativas justificadas. Los nombres historicos se clasifican como
compatibilidad o deuda de producto, no se reemplazan masivamente.

## 5. Archivos no versionados y veredicto

Los 79 archivos `??` finales fueron clasificados: 77 se conservan como
implementacion, tests o documentacion permanente y 2 se conservan documentados como herramienta
operativa/migratoria (`validate_geoapify_argentina.py` y
`migrate_comercios_location_visibility.py`). No se encontro un `??` temporal.

El gate de residuos de 95.7-B queda satisfecho: evidencia completa, residuos D
limpiados, compatibilidad preservada y deuda trazada. 95.7-C confronto esta
evidencia y confirmo cero residuos categoria D pendientes para el cierre de
ETAPA 95, sin convertir las deudas de riesgo en refactors automaticos. La
Correccion y Pulido Visual del Frontend queda como ETAPA 98 futura, posterior a
PWA.
