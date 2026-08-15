from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import obtener_usuario_actual
from app.modules.geocoding.schemas.geocoding_schemas import (
    ForwardGeocodingRequest,
    ForwardGeocodingResponse,
    ReverseGeocodingRequest,
    ReverseGeocodingResponse,
    TerritoryResolutionResponse,
)
from app.modules.geocoding.services.geocoding_services import (
    GeocodingProviderError,
    GeocodingProviderRateLimitError,
    GeocodingProviderTimeoutError,
    GeocodingService,
    GeocodingUnavailableError,
    get_geocoding_service,
)
from app.modules.search.services.territorial_search_services import TerritorialContext


router = APIRouter(prefix="/geocoding", tags=["Geocoding"])


def _execute(operation):
    try:
        return operation()
    except GeocodingUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio geografico no disponible.",
        ) from exc
    except GeocodingProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El servicio geografico no respondio a tiempo.",
        ) from exc
    except GeocodingProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Servicio geografico temporalmente limitado.",
        ) from exc
    except GeocodingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio geografico no pudo procesar la solicitud.",
        ) from exc


@router.post("/forward", response_model=ForwardGeocodingResponse)
def forward_geocoding(
    payload: ForwardGeocodingRequest,
    _usuario=Depends(obtener_usuario_actual),
    service: GeocodingService = Depends(get_geocoding_service),
):
    return _execute(lambda: service.forward(payload))


@router.post("/reverse", response_model=ReverseGeocodingResponse)
def reverse_geocoding(
    payload: ReverseGeocodingRequest,
    _usuario=Depends(obtener_usuario_actual),
    service: GeocodingService = Depends(get_geocoding_service),
):
    return _execute(lambda: service.reverse(payload))


@router.post("/territory", response_model=TerritoryResolutionResponse)
def resolve_territory(
    payload: ReverseGeocodingRequest,
    service: GeocodingService = Depends(get_geocoding_service),
):
    """Resuelve solo territorio seguro para busqueda publica, sin domicilio."""

    response = _execute(lambda: service.reverse(payload))
    proposal = response.propuesta
    if proposal is None or not proposal.ciudad or not proposal.provincia:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fue posible determinar el territorio.",
        )
    try:
        context = TerritorialContext.build(
            city_key=proposal.ciudad,
            province_code=proposal.provincia,
            country_code=proposal.pais or "Argentina",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El territorio obtenido no es compatible.",
        ) from exc
    return TerritoryResolutionResponse(
        city_key=context.city_key,
        province_code=context.province_code,
        country_code=context.country_code,
        city=proposal.ciudad,
        province=proposal.provincia,
        attribution=response.attribution,
    )
