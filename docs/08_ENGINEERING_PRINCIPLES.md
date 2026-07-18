# Principios de Ingeniería

Este documento registra los principios permanentes de ingeniería utilizados para desarrollar FeedGo.

No contiene decisiones de producto.

No contiene roadmap.

No contiene changelog.

No contiene implementaciones.

## 1. Backend First

Toda la lógica de negocio pertenece al backend.

Nunca al frontend.

## 2. Frontend liviano

El frontend únicamente:

- interactúa;
- renderiza;
- consume APIs.

Nunca implementa:

- reglas de negocio;
- búsqueda;
- ranking;
- IA.

## 3. Reutilizar antes de crear

Antes de crear componentes nuevos:

- auditar;
- buscar reutilización;
- extender lo existente.

Duplicar código es el último recurso.

## 4. Auditar antes de implementar

Toda implementación debe comenzar con auditoría y evidencia.

La auditoría debe permitir comprender el sistema antes de diseñar o modificar.

Nunca al revés.

## 5. No realizar refactors masivos

Modificar únicamente el alcance necesario.

Evitar reescrituras completas.

Mantener estabilidad.

## 6. Limpieza residual obligatoria

Toda implementación debe finalizar eliminando:

- código muerto;
- imports innecesarios;
- variables sin uso;
- funciones obsoletas;
- comentarios temporales;
- lógica reemplazada;
- archivos temporales.

No dejar código residual que complique el mantenimiento.

La limpieza forma parte de la implementación.

No constituye un refactor masivo.

## 7. Arquitectura por capas

Mantener siempre:

Frontend

↓

Services

↓

API

↓

Backend Services

↓

Dominio

↓

Persistencia

Nunca saltar capas.

## 8. Fuente única de verdad

Cada dato debe tener un único propietario.

Evitar múltiples fuentes oficiales para la misma información.

Las tablas derivadas, caches, indices, embeddings, snapshots y eventos nunca
pueden transformarse en fuente oficial del dominio.

La documentacion tecnica de cada capacidad debe declarar explicitamente que
tablas son:

- fuente de verdad;
- derivadas;
- analiticas;
- indices;
- historicas;
- cache.

## 9. Todo derivado debe ser regenerable

Aplica para:

- Documento de Índice;
- Knowledge Graph proyectado;
- Índices Sintetizados;
- cualquier representación derivada.

Nunca depender de edición manual.

## 10. Runtime liviano

Todo cálculo pesado debe realizarse durante indexación.

El runtime únicamente consume.

## 11. Cache First

Mostrar información inmediatamente.

Actualizar en segundo plano.

Nunca bloquear la experiencia del usuario por cálculos pesados.

## 12. El usuario carga poco

FeedGo enriquece la información.

No obliga al usuario a completar decenas de campos.

## 13. El conocimiento se construye

El usuario aporta datos.

El sistema construye conocimiento.

## 14. No copiar información

Preferir:

- referencias;
- proyecciones;
- documentos derivados.

Evitar duplicación innecesaria.

## 15. Implementaciones pequeñas

Cada implementación debe resolver una responsabilidad concreta.

Evitar cambios gigantes.

## 16. Documentar antes de continuar

Toda decisión arquitectónica aprobada debe quedar registrada en `/docs` antes de continuar implementando.

## 17. El código sigue a la arquitectura

Nunca adaptar la arquitectura al código.

Siempre adaptar el código a la arquitectura aprobada.

## 18. Diseñar para evolucionar

Cada componente debe poder crecer sin romper la arquitectura.

Evitar soluciones pensadas únicamente para el caso actual.

## 19. Evidencia antes que opinión

Las decisiones deben basarse en:

- auditorías;
- evidencia;
- lectura del código;
- validaciones.

No únicamente en intuición.

## 20. FeedGo es una plataforma de descubrimiento

Nunca diseñar componentes pensando únicamente en un marketplace tradicional.

## 21. Responsabilidad única

Cada módulo debe tener una única responsabilidad claramente definida.

Evitar componentes que hagan múltiples tareas.

## 22. Evitar arquitecturas con excepciones

Si una solución necesita demasiadas excepciones para funcionar, probablemente la arquitectura es incorrecta.

Preferir rediseñar antes que seguir agregando casos especiales.

## 23. Consistencia antes que velocidad

Es preferible avanzar un poco más lento manteniendo una arquitectura consistente que avanzar rápido generando deuda técnica.

## 24. Calidad antes de cerrar una etapa

Antes de considerar terminada una implementación debe verificarse:

- funcionamiento;
- limpieza residual;
- documentación;
- CHANGELOG antes del commit;
- consistencia arquitectónica.

Una etapa no termina únicamente porque el código funciona.

## 25. Integraciones desacopladas

Toda capacidad externa o complementaria debe integrarse mediante contratos claros y adaptadores.

Ejemplos:

- facturación;
- pagos;
- mensajería;
- reservas;
- logística;
- proveedores de IA;
- servicios de terceros.

Reglas:

- FeedGo conserva toda la lógica del dominio.
- Los sistemas externos no forman parte del núcleo del backend.
- No acoplar modelos ni reglas de negocio a un proveedor específico.
- Toda integración debe poder reemplazarse sin reescribir el dominio principal.
- Preferir interfaces, adapters, gateways y servicios de integración.
- Los nuevos componentes deben diseñarse desacoplados cuando exista una frontera clara de dominio.
- Desacoplado no significa duplicado; significa integrado mediante contratos explícitos.

Esquema conceptual:

FeedGo

↓

Contrato de Integración

↓

Adaptador

↓

Sistema Externo

## 26. Seguridad por diseño

Toda funcionalidad debe diseñarse considerando seguridad desde el inicio.

La seguridad nunca debe agregarse únicamente al finalizar una implementación.

Debe formar parte del análisis, diseño, implementación y validación.

## 27. Defensa en profundidad

FeedGo debe diseñarse bajo el principio de defensa en profundidad.

La arquitectura debe asumir que:

- cualquier entrada puede ser maliciosa;
- cualquier integración externa puede fallar;
- cualquier dependencia puede verse comprometida.

La arquitectura debe minimizar el impacto de esos escenarios.

Nunca depender de un único mecanismo de protección.

## 28. Secure by Default

Toda funcionalidad, módulo, endpoint o integración debe nacer en el estado más seguro posible.

Por defecto:

- acceso denegado;
- recursos privados;
- integraciones deshabilitadas;
- mínimo privilegio;
- configuración segura.

Toda excepción debe habilitarse explícitamente.

Nunca al revés.

## 29. Mínimo privilegio

Todo componente, integración o servicio debe operar únicamente con los permisos mínimos necesarios.

Nunca otorgar privilegios superiores por comodidad.

## 30. Toda entrada es no confiable

Toda información recibida desde:

- usuarios;
- APIs;
- archivos;
- integraciones;
- webhooks;
- servicios externos;

debe considerarse no confiable hasta ser validada.

## 31. Seguridad en integraciones

Reglas permanentes:

- validar autenticidad;
- validar autorización;
- validar formato;
- validar origen;
- verificar firmas cuando corresponda;
- proteger secretos;
- no exponer credenciales;
- utilizar HTTPS;
- aplicar límites;
- registrar auditoría;
- poder revocar integraciones rápidamente.

Nunca almacenar secretos en código, frontend, repositorio o logs.

## 32. Fallar de manera segura

Cuando exista incertidumbre o error, debe prevalecer la protección del sistema.

Nunca conceder permisos por defecto.

Nunca asumir datos válidos.

Antes de cerrar cualquier implementación deben revisarse también los aspectos de seguridad.

No solamente funcionamiento.

## 33. Calidad arquitectónica

### Responsabilidad única

Cada módulo debe tener una única responsabilidad claramente definida.

Evitar componentes que hagan múltiples tareas.

### Evitar arquitecturas basadas en excepciones

Si una solución requiere demasiadas excepciones para funcionar, probablemente la arquitectura necesita rediseñarse.

Preferir mejorar el diseño antes que seguir agregando casos especiales.

## 34. La documentación también evoluciona arquitectónicamente

La documentación oficial forma parte de la arquitectura del proyecto.

Debe mantenerse:

- organizada;
- clasificada;
- sin duplicaciones;
- sin contradicciones;
- escalable.

Toda modificación importante deberá mantener la coherencia del sistema documental.

## 35. El conocimiento pertenece al proyecto

La inteligencia documental debe residir en la documentación oficial.

Los prompts deben permanecer simples.

El Sistema de Gobierno define el comportamiento esperado de cualquier IA.

Evitar duplicar reglas en prompts y documentación.

Toda evolución del proceso debe incorporarse al Sistema de Gobierno.

## 36. Prompts sin duplicación documental

Los prompts de continuidad deben ser instrucciones operativas breves.

No deben duplicar documentación oficial.

No deben convertirse en una segunda fuente de verdad.

El contexto, la arquitectura, el roadmap y las decisiones permanentes deben reconstruirse desde `/docs`.

## 37. Gobierno del Modelo de Datos

Antes de crear cualquier tabla nueva debe realizarse una auditoria del modelo
de datos existente.

La auditoria debe demostrar obligatoriamente:

- que no existe una tabla propietaria natural del dato;
- que agregar columnas o relaciones a una tabla existente no seria una solucion
  mas correcta;
- que la nueva tabla tendra una unica responsabilidad;
- que la nueva tabla no generara una segunda fuente de verdad;
- que la incorporacion esta alineada con la arquitectura enterprise de FeedGo.

Crear una tabla nueva sin esta evidencia queda fuera del flujo oficial de
trabajo.

## 38. Compatibilidad hacia atras

Toda nueva funcionalidad debe auditar su impacto sobre funcionalidades
existentes antes de ser aprobada o cerrada.

La auditoria debe verificar:

- que endpoints existentes se modifican;
- que servicios pasan a depender del nuevo modulo;
- que tablas nuevas se vuelven obligatorias;
- que contratos backend/frontend cambian;
- que pantallas existentes pueden verse afectadas.

No puede cerrarse una etapa sin demostrar que la implementacion nueva no rompio
funcionalidades anteriores.

## 39. Validacion obligatoria de schema

Antes de cerrar una etapa que agregue o use tablas nuevas debe verificarse:

- `Base.metadata`;
- tablas reales de MySQL;
- diferencias entre metadata y base fisica;
- imports necesarios para registrar modelos en metadata;
- ausencia de tablas usadas por runtime que no existan fisicamente.

Si existe una diferencia que afecte runtime, la etapa no puede cerrarse.

## 40. Clasificacion oficial de tablas

La documentacion tecnica debe clasificar explicitamente cada tabla relevante
como:

- fuente de verdad;
- relacion;
- configuracion;
- indice;
- IA;
- evento;
- historica;
- cache;
- analitica.

La clasificacion no cambia el modelo por si misma; define propiedad,
responsabilidad y riesgo de cada dato.

## 41. Design System oficial

Toda nueva pantalla, componente o flujo visible debe respetar el Design System
oficial de FeedGo.

Los botones secundarios deben mantener un estilo uniforme:

- sin borde, capsula ni marco permanente;
- icono, cuando corresponda, y texto como estado normal;
- fondo suave o resaltado solo en hover, focus o interaccion;
- area de click comoda y accesible;
- transiciones suaves y consistentes.

Esta regla aplica a acciones de navegacion, perfil, busqueda, publicaciones,
historias, comercios y futuras funcionalidades.

Los botones primarios pueden conservar una jerarquia visual distinta cuando el
producto lo justifique.

No deben incorporarse nuevos estilos de botones sin justificacion
arquitectonica o de producto.
