"""
rubros_services.py
------------------
Lógica de negocio para Rubros.

- Los rubros son de solo lectura
- No se crean ni editan desde la app
"""

from sqlalchemy.orm import Session
from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.products.models.rubros_models import Rubro


CATALOGO_RUBROS_DESCRIPCIONES = {
    "Gastronomía": (
        "Bares, restaurantes, pizzerías, cafeterías, heladerías, comida, "
        "bebidas, delivery, cena, almuerzo y locales gastronómicos."
    ),
    "Ropa y Calzado": (
        "Indumentaria, prendas, vestimenta, moda, ropa, calzado, zapatos, "
        "zapatillas, accesorios y tiendas de vestir."
    ),
    "Servicios Profesionales": (
        "Servicios profesionales, abogados, contadores, gestores, "
        "consultores, asesoramiento legal, contable, administrativo y "
        "empresarial."
    ),
    "Salud y Bienestar": (
        "Salud, bienestar, centros médicos, gimnasios, estética, cuidado "
        "personal, nutrición, terapias y actividad física."
    ),
    "Automotor": (
        "Autos, motos, talleres mecánicos, repuestos, neumáticos, "
        "mantenimiento, reparación y servicios automotores."
    ),
    "Hogar y Construcción": (
        "Hogar, construcción, obra, reformas, ferreterías, materiales, "
        "revestimientos, pintura, mantenimiento y reparación del hogar."
    ),
    "Tecnología": (
        "Tecnología, computación, celulares, electrónica, informática, "
        "reparación técnica, accesorios, software y servicios digitales."
    ),
    "Mascotas": (
        "Mascotas, veterinarias, pet shops, alimentos para animales, "
        "accesorios, peluquería canina y servicios para mascotas."
    ),
    "Educación": (
        "Educación, institutos, academias, cursos, formación, capacitación, "
        "clases, talleres y apoyo escolar."
    ),
    "Inmobiliario": (
        "Inmobiliarias, alquileres, ventas, propiedades, casas, "
        "departamentos, terrenos y servicios inmobiliarios."
    ),
    "Kiosco": (
        "Kiosco, maxikiosco, golosinas, bebidas, snacks, cigarrillos, "
        "almacén pequeño, productos rápidos y compras al paso."
    ),
    "Supermercado": (
        "Supermercado, almacén, despensa, alimentos, bebidas, limpieza, "
        "perfumería, productos del hogar y compras diarias."
    ),
    "Tienda de ropa": (
        "Tienda de ropa, prendas, vestimenta, indumentaria, moda, remeras, "
        "pantalones, camperas, vestidos, accesorios y ropa urbana."
    ),
    "Zapatería": (
        "Zapatería, calzado, zapatos, zapatillas, sandalias, botas, ojotas, "
        "calzado deportivo, calzado urbano y accesorios de calzado."
    ),
    "Deportes": (
        "Deportes, artículos deportivos, indumentaria deportiva, zapatillas "
        "deportivas, gimnasios, entrenamiento, fitness, clubes y accesorios "
        "deportivos."
    ),
    "Servicios de limpieza": (
        "Servicios de limpieza, limpieza de hogares, oficinas, comercios, "
        "mantenimiento, higiene, desinfección y productos de limpieza."
    ),
    "Servicios de construcción": (
        "Obra, albañilería, reformas, colocación de revestimientos, "
        "revestimientos para paredes y pisos, cerámicos, porcelanatos, "
        "materiales de construcción, pintura, mantenimiento y reparaciones."
    ),
    "Estudio contable": (
        "Estudio contable, contador, impuestos, balances, monotributo, "
        "sueldos, administración, asesoramiento contable y trámites fiscales."
    ),
    "Estudio jurídico / abogado": (
        "Estudio jurídico, abogado, asesoramiento legal, derecho laboral, "
        "civil, comercial, contratos, reclamos y trámites legales."
    ),
    "Inmobiliaria": (
        "Inmobiliaria, alquileres, ventas, propiedades, casas, "
        "departamentos, terrenos, tasaciones y administración de inmuebles."
    ),
}


CATALOGO_RUBROS_INICIAL = list(CATALOGO_RUBROS_DESCRIPCIONES.keys())


DESCRIPCIONES_RUBROS_ANTERIORES = {
    "Bares, restaurantes, cafeterías y comida en general",
    "Indumentaria, moda y accesorios",
    "Abogados, contadores, gestores, consultores",
    "Centros médicos, gimnasios, estética y bienestar",
    "Autos, motos, talleres, repuestos y servicios",
    "Ferreterías, materiales, reformas y mantenimiento",
    "Computación, celulares, electrónica y servicios técnicos",
    "Veterinarias, pet shops y servicios para mascotas",
    "Institutos, academias y formación",
    "Inmobiliarias, alquileres y servicios relacionados",
    (
        "Servicios de construcción, obra, albañilería, reformas, "
        "revestimientos, colocación, materiales, mantenimiento, pintura y "
        "reparaciones."
    ),
    (
        "Servicios de construcción, obra, albañilería, reformas, colocación "
        "de revestimientos, revestimientos para paredes y pisos, cerámicos, "
        "porcelanatos, materiales de construcción, pintura, mantenimiento y "
        "reparaciones."
    ),
}


def asegurar_catalogo_rubros(db: Session) -> None:
    """
    Crea o reactiva los rubros base sin borrar ni renombrar datos existentes.
    """
    rubros_existentes = {
        rubro.nombre.strip().lower(): rubro
        for rubro in db.query(Rubro).all()
        if rubro.nombre
    }

    hubo_cambios = False

    for nombre in CATALOGO_RUBROS_INICIAL:
        key = nombre.strip().lower()
        rubro = rubros_existentes.get(key)
        descripcion = CATALOGO_RUBROS_DESCRIPCIONES.get(nombre)

        if rubro:
            if not rubro.activo:
                rubro.activo = True
                hubo_cambios = True
            descripcion_actual = (rubro.descripcion or "").strip()
            if (
                descripcion
                and (
                    not descripcion_actual
                    or descripcion_actual in DESCRIPCIONES_RUBROS_ANTERIORES
                )
                and descripcion_actual != descripcion
            ):
                rubro.descripcion = descripcion
                hubo_cambios = True
            continue

        db.add(Rubro(nombre=nombre, descripcion=descripcion, activo=True))
        hubo_cambios = True

    if hubo_cambios:
        db.commit()


def listar_rubros(db: Session) -> list[Rubro]:
    """
    Devuelve todos los rubros activos.
    """
    return (
        db.query(Rubro)
        .filter(Rubro.activo == True)
        .order_by(Rubro.nombre.asc())
        .all()
    )


def obtener_rubro_por_id(db: Session, rubro_id: int) -> Rubro | None:
    """
    Devuelve un rubro por ID si está activo.
    """
    return (
        db.query(Rubro)
        .filter(
            Rubro.id == rubro_id,
            Rubro.activo == True
        )
        .first()
    )


def listar_especialidades_por_rubro(
    db: Session,
    rubro_id: int,
) -> list[TaxonomyNode] | None:
    """
    Devuelve especialidades Discovery hijas del rubro principal.
    """
    rubro_principal = obtener_rubro_por_id(db, rubro_id)
    if not rubro_principal:
        return None

    assignment_principal = (
        db.query(TaxonomyAssignment)
        .filter(TaxonomyAssignment.entity_type == "rubro")
        .filter(TaxonomyAssignment.entity_id == rubro_id)
        .first()
    )
    if not assignment_principal:
        return []

    return (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.parent_id == assignment_principal.taxonomy_node_id)
        .filter(TaxonomyNode.type == "especialidad")
        .filter(TaxonomyNode.activo == True)
        .order_by(TaxonomyNode.orden.asc(), TaxonomyNode.nombre.asc())
        .all()
    )


def _agregar_descendientes_rubro(
    *,
    nodes_by_parent: dict[int | None, list[TaxonomyNode]],
    parent_id: int | None,
    prioridad: int,
    node_id_a_prioridad: dict[int, int],
) -> None:
    pendientes = list(nodes_by_parent.get(parent_id, []))

    while pendientes:
        node = pendientes.pop(0)
        if node.type == "rubro":
            prioridad_actual = node_id_a_prioridad.get(node.id)
            if prioridad_actual is None or prioridad < prioridad_actual:
                node_id_a_prioridad[node.id] = prioridad

        pendientes.extend(nodes_by_parent.get(node.id, []))


def listar_rubros_secundarios_sugeridos(
    db: Session,
    rubro_id: int,
) -> list[Rubro] | None:
    """
    Devuelve rubros secundarios coherentes segun la relacion Discovery.
    """
    rubro_principal = obtener_rubro_por_id(db, rubro_id)
    if not rubro_principal:
        return None

    assignment_principal = (
        db.query(TaxonomyAssignment)
        .filter(TaxonomyAssignment.entity_type == "rubro")
        .filter(TaxonomyAssignment.entity_id == rubro_id)
        .first()
    )
    if not assignment_principal:
        return []

    node_principal = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.id == assignment_principal.taxonomy_node_id)
        .filter(TaxonomyNode.activo == True)
        .first()
    )
    if not node_principal:
        return []

    nodes = (
        db.query(TaxonomyNode)
        .filter(TaxonomyNode.activo == True)
        .all()
    )
    nodes_by_parent: dict[int | None, list[TaxonomyNode]] = {}
    nodes_by_id = {node.id: node for node in nodes}

    for node in nodes:
        nodes_by_parent.setdefault(node.parent_id, []).append(node)

    node_id_a_prioridad: dict[int, int] = {}

    if node_principal.parent_id is not None:
        for node in nodes_by_parent.get(node_principal.parent_id, []):
            if node.type == "rubro":
                node_id_a_prioridad[node.id] = 0

        _agregar_descendientes_rubro(
            nodes_by_parent=nodes_by_parent,
            parent_id=node_principal.parent_id,
            prioridad=1,
            node_id_a_prioridad=node_id_a_prioridad,
        )

        parent_node = nodes_by_id.get(node_principal.parent_id)
        if parent_node and parent_node.parent_id is not None:
            _agregar_descendientes_rubro(
                nodes_by_parent=nodes_by_parent,
                parent_id=parent_node.parent_id,
                prioridad=2,
                node_id_a_prioridad=node_id_a_prioridad,
            )

    node_id_a_prioridad.pop(node_principal.id, None)
    node_ids_relacionados = list(node_id_a_prioridad.keys())
    if not node_ids_relacionados:
        return []

    rubro_assignments = (
        db.query(TaxonomyAssignment)
        .filter(TaxonomyAssignment.entity_type == "rubro")
        .filter(TaxonomyAssignment.taxonomy_node_id.in_(node_ids_relacionados))
        .all()
    )
    if not rubro_assignments:
        return []

    rubro_id_a_prioridad: dict[int, int] = {}
    for assignment in rubro_assignments:
        prioridad = node_id_a_prioridad.get(assignment.taxonomy_node_id)
        if prioridad is None:
            continue

        prioridad_actual = rubro_id_a_prioridad.get(assignment.entity_id)
        if prioridad_actual is None or prioridad < prioridad_actual:
            rubro_id_a_prioridad[assignment.entity_id] = prioridad

    rubro_ids = [
        entity_id
        for entity_id in rubro_id_a_prioridad
        if entity_id != rubro_id
    ]
    if not rubro_ids:
        return []

    rubros = (
        db.query(Rubro)
        .filter(Rubro.activo == True)
        .filter(Rubro.id.in_(rubro_ids))
        .all()
    )

    return sorted(
        rubros,
        key=lambda rubro: (
            rubro_id_a_prioridad.get(rubro.id, 99),
            (rubro.nombre or "").lower(),
        ),
    )
