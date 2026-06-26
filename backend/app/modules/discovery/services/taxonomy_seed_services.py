"""
taxonomy_seed_services.py
-------------------------
Seed idempotente de la taxonomia inicial de FeedGo.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.discovery.models.taxonomy_models import TaxonomyNode
from app.modules.discovery.services.taxonomy_assignment_services import (
    AssignmentSyncResult,
    sincronizar_assignments_desde_rubros,
)


@dataclass(frozen=True)
class TaxonomyNodeSeed:
    slug: str
    nombre: str
    type: str
    descripcion: str
    parent_slug: str | None = None
    orden: int = 0


@dataclass
class TaxonomySeedResult:
    nodos_creados: int = 0
    nodos_actualizados: int = 0
    nodos_existentes: int = 0
    assignments: AssignmentSyncResult | None = None


TAXONOMY_NODES_SEED: tuple[TaxonomyNodeSeed, ...] = (
    TaxonomyNodeSeed(
        slug="retail",
        nombre="Retail",
        type="sector",
        descripcion="Comercios de venta minorista, tiendas, moda, calzado y productos.",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="servicios",
        nombre="Servicios",
        type="sector",
        descripcion="Prestadores de servicios profesionales, tecnicos, obra y mantenimiento.",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="consumo",
        nombre="Consumo",
        type="sector",
        descripcion="Comida, compras diarias, kioscos, supermercados y consumo frecuente.",
        orden=30,
    ),
    TaxonomyNodeSeed(
        slug="bienestar",
        nombre="Bienestar",
        type="sector",
        descripcion="Salud, cuidado personal, deportes, actividad fisica y calidad de vida.",
        orden=40,
    ),
    TaxonomyNodeSeed(
        slug="hogar",
        nombre="Hogar",
        type="sector",
        descripcion="Hogar, vivienda, construccion, reformas, mascotas e inmobiliario.",
        orden=50,
    ),
    TaxonomyNodeSeed(
        slug="conocimiento",
        nombre="Conocimiento",
        type="sector",
        descripcion="Educacion, capacitacion, tecnologia y servicios digitales.",
        orden=60,
    ),
    TaxonomyNodeSeed(
        slug="movilidad",
        nombre="Movilidad",
        type="sector",
        descripcion="Autos, motos, talleres, repuestos y servicios automotores.",
        orden=70,
    ),
    TaxonomyNodeSeed(
        slug="moda",
        nombre="Moda",
        type="categoria",
        descripcion="Indumentaria, vestimenta, prendas, accesorios, calzado y tiendas de vestir.",
        parent_slug="retail",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="indumentaria",
        nombre="Indumentaria",
        type="subcategoria",
        descripcion="Ropa, remeras, pantalones, camperas, vestidos, prendas y moda urbana.",
        parent_slug="moda",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="calzado",
        nombre="Calzado",
        type="subcategoria",
        descripcion="Zapatos, zapatillas, botas, sandalias, calzado urbano y deportivo.",
        parent_slug="moda",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="tienda-ropa",
        nombre="Tienda de ropa",
        type="rubro",
        descripcion="Comercios de ropa, prendas, indumentaria, remeras, pantalones y camperas.",
        parent_slug="indumentaria",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="ropa-calzado",
        nombre="Ropa y Calzado",
        type="rubro",
        descripcion="Rubro general de moda, ropa, vestimenta, indumentaria, zapatos y zapatillas.",
        parent_slug="moda",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="zapateria",
        nombre="Zapateria",
        type="rubro",
        descripcion="Comercios de zapatos, zapatillas, botas, sandalias y accesorios de calzado.",
        parent_slug="calzado",
        orden=30,
    ),
    TaxonomyNodeSeed(
        slug="deportes-bienestar",
        nombre="Deportes",
        type="categoria",
        descripcion="Deportes, entrenamiento, fitness, clubes, gimnasios e indumentaria deportiva.",
        parent_slug="bienestar",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="deportes",
        nombre="Deportes",
        type="rubro",
        descripcion="Articulos deportivos, zapatillas deportivas, fitness, entrenamiento y clubes.",
        parent_slug="deportes-bienestar",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="salud-bienestar",
        nombre="Salud y Bienestar",
        type="rubro",
        descripcion="Salud, bienestar, estetica, cuidado personal, nutricion y actividad fisica.",
        parent_slug="bienestar",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="gastronomia-categoria",
        nombre="Gastronomia",
        type="categoria",
        descripcion="Comida, restaurantes, bares, cafeterias, pizzerias y delivery.",
        parent_slug="consumo",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="comida-preparada",
        nombre="Comida preparada",
        type="subcategoria",
        descripcion="Restaurantes, pizzerias, cafeterias, heladerias, bares, almuerzo y cena.",
        parent_slug="gastronomia-categoria",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="gastronomia",
        nombre="Gastronomia",
        type="rubro",
        descripcion="Locales gastronomicos, bares, restaurantes, pizzerias, cafeterias y delivery.",
        parent_slug="comida-preparada",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="compras-diarias",
        nombre="Compras diarias",
        type="categoria",
        descripcion="Kioscos, supermercados, almacenes, despensas, alimentos y bebidas.",
        parent_slug="consumo",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="kiosco",
        nombre="Kiosco",
        type="rubro",
        descripcion="Kioscos, maxikioscos, golosinas, snacks, bebidas y compras al paso.",
        parent_slug="compras-diarias",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="supermercado",
        nombre="Supermercado",
        type="rubro",
        descripcion="Supermercados, almacenes, despensas, alimentos, bebidas y limpieza.",
        parent_slug="compras-diarias",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="construccion",
        nombre="Construccion",
        type="categoria",
        descripcion="Obra, reformas, construccion, ferreteria, materiales y mantenimiento.",
        parent_slug="hogar",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="obra-revestimientos",
        nombre="Obra y revestimientos",
        type="subcategoria",
        descripcion="Revestimientos, ceramicos, porcelanatos, pintura, obra y reformas.",
        parent_slug="construccion",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="hogar-construccion",
        nombre="Hogar y Construccion",
        type="rubro",
        descripcion="Hogar, construccion, obra, reformas, ferreterias, materiales y pintura.",
        parent_slug="construccion",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="servicios-construccion",
        nombre="Servicios de construccion",
        type="rubro",
        descripcion="Servicios de obra, albanileria, reformas, revestimientos y reparaciones.",
        parent_slug="obra-revestimientos",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="servicios-profesionales",
        nombre="Servicios Profesionales",
        type="categoria",
        descripcion="Servicios profesionales, legales, contables, administrativos y consultoria.",
        parent_slug="servicios",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="estudio-contable",
        nombre="Estudio contable",
        type="rubro",
        descripcion="Contadores, impuestos, balances, monotributo y asesoramiento contable.",
        parent_slug="servicios-profesionales",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="estudio-juridico-abogado",
        nombre="Estudio juridico / abogado",
        type="rubro",
        descripcion="Abogados, estudios juridicos, asesoramiento legal, contratos y reclamos.",
        parent_slug="servicios-profesionales",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="servicios-limpieza",
        nombre="Servicios de limpieza",
        type="rubro",
        descripcion="Limpieza de hogares, oficinas, comercios, higiene y desinfeccion.",
        parent_slug="servicios",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="tecnologia",
        nombre="Tecnologia",
        type="rubro",
        descripcion="Computacion, celulares, electronica, informatica, software y servicios digitales.",
        parent_slug="conocimiento",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="educacion",
        nombre="Educacion",
        type="rubro",
        descripcion="Cursos, institutos, academias, formacion, capacitacion y apoyo escolar.",
        parent_slug="conocimiento",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="mascotas",
        nombre="Mascotas",
        type="rubro",
        descripcion="Veterinarias, pet shops, alimentos, accesorios y servicios para mascotas.",
        parent_slug="hogar",
        orden=30,
    ),
    TaxonomyNodeSeed(
        slug="inmobiliario",
        nombre="Inmobiliario",
        type="categoria",
        descripcion="Alquileres, ventas, propiedades, casas, departamentos y terrenos.",
        parent_slug="hogar",
        orden=40,
    ),
    TaxonomyNodeSeed(
        slug="inmobiliario-rubro",
        nombre="Inmobiliario",
        type="rubro",
        descripcion="Servicios inmobiliarios, alquileres, ventas, propiedades y terrenos.",
        parent_slug="inmobiliario",
        orden=10,
    ),
    TaxonomyNodeSeed(
        slug="inmobiliaria",
        nombre="Inmobiliaria",
        type="rubro",
        descripcion="Inmobiliarias, tasaciones, administracion de inmuebles, alquileres y ventas.",
        parent_slug="inmobiliario",
        orden=20,
    ),
    TaxonomyNodeSeed(
        slug="automotor",
        nombre="Automotor",
        type="rubro",
        descripcion="Autos, motos, talleres mecanicos, repuestos, neumaticos y mantenimiento.",
        parent_slug="movilidad",
        orden=10,
    ),
)


RUBRO_NOMBRE_A_TAXONOMY_SLUG = {
    "gastronomía": "gastronomia",
    "gastronomia": "gastronomia",
    "ropa y calzado": "ropa-calzado",
    "servicios profesionales": "servicios-profesionales",
    "salud y bienestar": "salud-bienestar",
    "automotor": "automotor",
    "hogar y construcción": "hogar-construccion",
    "hogar y construccion": "hogar-construccion",
    "tecnología": "tecnologia",
    "tecnologia": "tecnologia",
    "mascotas": "mascotas",
    "educación": "educacion",
    "educacion": "educacion",
    "inmobiliario": "inmobiliario-rubro",
    "kiosco": "kiosco",
    "supermercado": "supermercado",
    "tienda de ropa": "tienda-ropa",
    "zapatería": "zapateria",
    "zapateria": "zapateria",
    "deportes": "deportes",
    "servicios de limpieza": "servicios-limpieza",
    "servicios de construcción": "servicios-construccion",
    "servicios de construccion": "servicios-construccion",
    "estudio contable": "estudio-contable",
    "estudio jurídico / abogado": "estudio-juridico-abogado",
    "estudio juridico / abogado": "estudio-juridico-abogado",
    "inmobiliaria": "inmobiliaria",
}


def asegurar_taxonomia_base(db: Session) -> TaxonomySeedResult:
    result = TaxonomySeedResult()

    nodes_by_slug = {
        node.slug: node
        for node in db.query(TaxonomyNode)
        .filter(TaxonomyNode.slug.in_([seed.slug for seed in TAXONOMY_NODES_SEED]))
        .all()
    }

    for seed in TAXONOMY_NODES_SEED:
        node = nodes_by_slug.get(seed.slug)

        parent_id = None
        if seed.parent_slug:
            parent = nodes_by_slug.get(seed.parent_slug)
            if parent:
                parent_id = parent.id

        if node is None:
            node = TaxonomyNode(
                slug=seed.slug,
                nombre=seed.nombre,
                type=seed.type,
                descripcion=seed.descripcion,
                parent_id=parent_id,
                activo=True,
                orden=seed.orden,
            )
            db.add(node)
            db.flush()
            nodes_by_slug[seed.slug] = node
            result.nodos_creados += 1
            continue

        actualizado = False
        campos = {
            "nombre": seed.nombre,
            "type": seed.type,
            "descripcion": seed.descripcion,
            "parent_id": parent_id,
            "activo": True,
            "orden": seed.orden,
        }
        for campo, valor in campos.items():
            if getattr(node, campo) != valor:
                setattr(node, campo, valor)
                actualizado = True

        if actualizado:
            result.nodos_actualizados += 1
        else:
            result.nodos_existentes += 1

    result.assignments = sincronizar_assignments_desde_rubros(
        db,
        RUBRO_NOMBRE_A_TAXONOMY_SLUG,
    )
    db.commit()
    return result
