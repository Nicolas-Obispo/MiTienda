"""
Servicios de horarios habituales de atencion.

El Sistema de Disponibilidad modela unicamente franjas semanales habituales.
No contempla agenda, reservas, feriados ni excepciones por fecha.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.modules.availability.models.horarios_atencion_models import (
    ComercioHorarioAtencion,
)
from app.modules.availability.schemas.horarios_atencion_schemas import (
    EstadoHorario,
    EstadoHorarioResponse,
    HorarioAtencionFranjaEntrada,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.users.models.usuarios_models import Usuario


ZONA_HORARIA_DISPONIBILIDAD = "America/Argentina/Buenos_Aires"
_ZONA_HORARIA_FALLBACK = timezone(timedelta(hours=-3))
_DIAS_SEMANA = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)


class ComercioNoEncontradoError(ValueError):
    pass


class FranjasSolapadasError(ValueError):
    pass


def _zona_horaria(zona_horaria: str = ZONA_HORARIA_DISPONIBILIDAD):
    try:
        return ZoneInfo(zona_horaria)
    except ZoneInfoNotFoundError:
        if zona_horaria == ZONA_HORARIA_DISPONIBILIDAD:
            return _ZONA_HORARIA_FALLBACK
        raise


def _normalizar_referencia(
    referencia: datetime | None,
    zona_horaria: str,
) -> datetime:
    tz = _zona_horaria(zona_horaria)

    if referencia is None:
        return datetime.now(tz)

    if referencia.tzinfo is None:
        # Las referencias naive se interpretan en la zona configurada.
        return referencia.replace(tzinfo=tz)

    return referencia.astimezone(tz)


def _datetime_en_zona(
    base: datetime,
    dias_offset: int,
    hora: time,
) -> datetime:
    fecha = (base + timedelta(days=dias_offset)).date()
    return datetime.combine(fecha, hora, tzinfo=base.tzinfo)


def _hora_hhmm(valor: time) -> str:
    return valor.strftime("%H:%M")


def _ordenar_franjas(franjas) -> list:
    return sorted(
        franjas,
        key=lambda franja: (
            franja.dia_semana,
            franja.hora_apertura,
            franja.hora_cierre,
        ),
    )


def validar_franjas_sin_solapamientos(
    franjas: list[HorarioAtencionFranjaEntrada],
) -> None:
    franjas_por_dia: dict[int, list[HorarioAtencionFranjaEntrada]] = defaultdict(list)

    for franja in franjas:
        franjas_por_dia[franja.dia_semana].append(franja)

    for dia, franjas_dia in franjas_por_dia.items():
        ordenadas = sorted(
            franjas_dia,
            key=lambda franja: (franja.hora_apertura, franja.hora_cierre),
        )

        for anterior, siguiente in zip(ordenadas, ordenadas[1:]):
            if siguiente.hora_apertura < anterior.hora_cierre:
                raise FranjasSolapadasError(
                    f"Hay franjas solapadas para dia_semana={dia}"
                )


def obtener_horarios_atencion(
    db: Session,
    comercio_id: int,
) -> list[ComercioHorarioAtencion]:
    return (
        db.query(ComercioHorarioAtencion)
        .filter(ComercioHorarioAtencion.comercio_id == comercio_id)
        .order_by(
            ComercioHorarioAtencion.dia_semana.asc(),
            ComercioHorarioAtencion.hora_apertura.asc(),
            ComercioHorarioAtencion.hora_cierre.asc(),
        )
        .all()
    )


def reemplazar_horarios_atencion(
    db: Session,
    comercio: Comercio | None,
    usuario: Usuario,
    franjas: list[HorarioAtencionFranjaEntrada],
) -> list[ComercioHorarioAtencion]:
    if comercio is None:
        raise ComercioNoEncontradoError("Comercio no encontrado")

    if comercio.usuario_id != usuario.id:
        raise PermissionError("No tenes permiso para modificar este comercio")

    comercio_id = comercio.id
    validar_franjas_sin_solapamientos(franjas)

    try:
        horarios_actuales = (
            db.query(ComercioHorarioAtencion)
            .filter(ComercioHorarioAtencion.comercio_id == comercio_id)
            .all()
        )
        for horario in horarios_actuales:
            db.delete(horario)
        db.flush()

        nuevos_horarios = [
            ComercioHorarioAtencion(
                comercio_id=comercio_id,
                dia_semana=franja.dia_semana,
                hora_apertura=franja.hora_apertura,
                hora_cierre=franja.hora_cierre,
            )
            for franja in _ordenar_franjas(franjas)
        ]

        db.add_all(nuevos_horarios)
        db.commit()

        for horario in nuevos_horarios:
            db.refresh(horario)

        return _ordenar_franjas(nuevos_horarios)
    except Exception:
        db.rollback()
        raise


def calcular_estado_horario(
    franjas,
    referencia: datetime | None = None,
    zona_horaria: str = ZONA_HORARIA_DISPONIBILIDAD,
) -> EstadoHorarioResponse:
    evaluado_en = _normalizar_referencia(referencia, zona_horaria)
    franjas_ordenadas = _ordenar_franjas(list(franjas))

    if not franjas_ordenadas:
        return EstadoHorarioResponse(
            estado=EstadoHorario.sin_horarios,
            texto="No hay horarios declarados",
            zona_horaria=zona_horaria,
            evaluado_en=evaluado_en,
            cierre_actual=None,
            proxima_apertura=None,
        )

    dia_actual = evaluado_en.weekday()
    hora_actual = evaluado_en.time()

    for franja in franjas_ordenadas:
        if (
            franja.dia_semana == dia_actual
            and franja.hora_apertura <= hora_actual < franja.hora_cierre
        ):
            cierre_actual = _datetime_en_zona(evaluado_en, 0, franja.hora_cierre)
            return EstadoHorarioResponse(
                estado=EstadoHorario.abierto,
                texto=f"Abierto · Hasta las {_hora_hhmm(franja.hora_cierre)}",
                zona_horaria=zona_horaria,
                evaluado_en=evaluado_en,
                cierre_actual=cierre_actual,
                proxima_apertura=None,
            )

    proxima_apertura = _buscar_proxima_apertura(franjas_ordenadas, evaluado_en)
    if proxima_apertura is None:
        return EstadoHorarioResponse(
            estado=EstadoHorario.cerrado,
            texto="Cerrado",
            zona_horaria=zona_horaria,
            evaluado_en=evaluado_en,
            cierre_actual=None,
            proxima_apertura=None,
        )

    apertura_dt, dias_offset = proxima_apertura
    hora_texto = _hora_hhmm(apertura_dt.time())

    if dias_offset == 0:
        texto = f"Cerrado · Abre a las {hora_texto}"
    elif dias_offset == 1:
        texto = f"Cerrado · Abre mañana a las {hora_texto}"
    else:
        dia_texto = _DIAS_SEMANA[apertura_dt.weekday()]
        texto = f"Cerrado · Abre el {dia_texto} a las {hora_texto}"

    return EstadoHorarioResponse(
        estado=EstadoHorario.cerrado,
        texto=texto,
        zona_horaria=zona_horaria,
        evaluado_en=evaluado_en,
        cierre_actual=None,
        proxima_apertura=apertura_dt,
    )


def _buscar_proxima_apertura(
    franjas: list,
    evaluado_en: datetime,
) -> tuple[datetime, int] | None:
    dia_actual = evaluado_en.weekday()
    hora_actual = evaluado_en.time()

    for dias_offset in range(0, 8):
        dia = (dia_actual + dias_offset) % 7
        franjas_dia = [
            franja
            for franja in franjas
            if franja.dia_semana == dia
        ]

        for franja in sorted(franjas_dia, key=lambda item: item.hora_apertura):
            if dias_offset == 0 and franja.hora_apertura <= hora_actual:
                continue

            return (
                _datetime_en_zona(evaluado_en, dias_offset, franja.hora_apertura),
                dias_offset,
            )

    return None


def calcular_estado_horario_comercio(
    db: Session,
    comercio_id: int,
    referencia: datetime | None = None,
    zona_horaria: str = ZONA_HORARIA_DISPONIBILIDAD,
) -> EstadoHorarioResponse:
    franjas = obtener_horarios_atencion(db, comercio_id)
    return calcular_estado_horario(
        franjas,
        referencia=referencia,
        zona_horaria=zona_horaria,
    )


def calcular_estados_horarios_lote(
    db: Session,
    comercio_ids: list[int],
    referencia: datetime | None = None,
    zona_horaria: str = ZONA_HORARIA_DISPONIBILIDAD,
) -> dict[int, EstadoHorarioResponse]:
    ids_unicos = list(dict.fromkeys(comercio_ids))
    evaluado_en = _normalizar_referencia(referencia, zona_horaria)

    if not ids_unicos:
        return {}

    filas = (
        db.query(ComercioHorarioAtencion)
        .filter(ComercioHorarioAtencion.comercio_id.in_(ids_unicos))
        .order_by(
            ComercioHorarioAtencion.comercio_id.asc(),
            ComercioHorarioAtencion.dia_semana.asc(),
            ComercioHorarioAtencion.hora_apertura.asc(),
            ComercioHorarioAtencion.hora_cierre.asc(),
        )
        .all()
    )

    franjas_por_comercio: dict[int, list[ComercioHorarioAtencion]] = {
        comercio_id: []
        for comercio_id in ids_unicos
    }

    for fila in filas:
        franjas_por_comercio[fila.comercio_id].append(fila)

    return {
        comercio_id: calcular_estado_horario(
            franjas,
            referencia=evaluado_en,
            zona_horaria=zona_horaria,
        )
        for comercio_id, franjas in franjas_por_comercio.items()
    }
