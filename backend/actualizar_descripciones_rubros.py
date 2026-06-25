"""
actualizar_descripciones_rubros.py
----------------------------------
Completa descripciones semanticas del catalogo de rubros.

Reglas:
- Crea rubros del catalogo si faltan.
- Activa rubros del catalogo si estaban inactivos.
- Actualiza descripcion solo si esta vacia o si coincide con una descripcion
  vieja conocida del catalogo.
- No pisa descripciones personalizadas.
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.services.rubros_services import (
    CATALOGO_RUBROS_DESCRIPCIONES,
    DESCRIPCIONES_RUBROS_ANTERIORES,
)


def actualizar_descripciones_rubros() -> None:
    creados = 0
    actualizados = 0
    reactivados = 0
    omitidos = 0

    with SessionLocal() as db:
        rubros_existentes = {
            rubro.nombre.strip().lower(): rubro
            for rubro in db.query(Rubro).all()
            if rubro.nombre
        }

        for nombre, descripcion in CATALOGO_RUBROS_DESCRIPCIONES.items():
            key = nombre.strip().lower()
            rubro = rubros_existentes.get(key)

            if rubro is None:
                db.add(Rubro(nombre=nombre, descripcion=descripcion, activo=True))
                creados += 1
                continue

            if not rubro.activo:
                rubro.activo = True
                reactivados += 1

            descripcion_actual = (rubro.descripcion or "").strip()
            if not descripcion_actual or descripcion_actual in DESCRIPCIONES_RUBROS_ANTERIORES:
                if descripcion_actual != descripcion:
                    rubro.descripcion = descripcion
                    actualizados += 1
                continue

            omitidos += 1

        if creados or actualizados or reactivados:
            db.commit()

    print(
        "Rubros procesados: "
        f"creados={creados}, "
        f"actualizados={actualizados}, "
        f"reactivados={reactivados}, "
        f"omitidos={omitidos}"
    )


if __name__ == "__main__":
    actualizar_descripciones_rubros()
