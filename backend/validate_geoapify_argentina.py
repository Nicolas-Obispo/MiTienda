"""Validacion controlada de Geoapify con ubicaciones publicas argentinas.

Requiere GEOAPIFY_API_KEY en backend/.env. Nunca imprime la credencial.
"""

import time

from app.modules.geocoding.schemas.geocoding_schemas import (
    ForwardGeocodingRequest,
    ReverseGeocodingRequest,
)
from app.modules.geocoding.services.geocoding_services import get_geocoding_service


CASES = {
    "Rafaela": [
        "Moreno 8",
        "Moreno 8, Rafaela",
        "Sgto. Cabral 159",
        "Sargento Cabral 159",
        "Sargento Cabral",
        "Sargento Cabral 160",
        "Morreno 8",
        "Municipalidad de Rafaela",
    ],
    "Sunchales": [
        "Av. Belgrano 103",
        "Avenida Belgrano 103",
        "Av Belgrano 103",
        "Avenida Belgrano",
        "Avenida Belgrano 105",
        "Belgranno 103",
        "Municipalidad de Sunchales",
    ],
}


def main():
    service = get_geocoding_service()
    reverse_points = []
    reverse_points_by_city = {city: 0 for city in CASES}
    request_count = 0
    latencies = []
    errors = []
    for city, queries in CASES.items():
        print(f"[{city}]")
        for query_index, query in enumerate(queries):
            started_at = time.perf_counter()
            try:
                response = service.forward(
                    ForwardGeocodingRequest(
                        query=query,
                        ciudad=city,
                        provincia="Santa Fe",
                        pais="Argentina",
                        limit=5,
                    )
                )
                elapsed_ms = round((time.perf_counter() - started_at) * 1000)
                latencies.append(elapsed_ms)
                request_count += 1
                print(query, f"latency_ms={elapsed_ms}", [item.model_dump() for item in response.alternativas])
                if (
                    response.alternativas
                    and query_index in {0, 3}
                    and reverse_points_by_city[city] < 2
                ):
                    first = response.alternativas[0]
                    reverse_points.append((city, first.latitud, first.longitud))
                    reverse_points_by_city[city] += 1
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000)
                request_count += 1
                errors.append(type(exc).__name__)
                print(query, f"latency_ms={elapsed_ms}", f"error={type(exc).__name__}")
            time.sleep(0.22)

    print("[Reverse]")
    for city, latitude, longitude in reverse_points:
        started_at = time.perf_counter()
        try:
            response = service.reverse(
                ReverseGeocodingRequest(latitud=latitude, longitud=longitude)
            )
            elapsed_ms = round((time.perf_counter() - started_at) * 1000)
            latencies.append(elapsed_ms)
            request_count += 1
            print(city, f"latency_ms={elapsed_ms}", response.propuesta.model_dump() if response.propuesta else None)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000)
            request_count += 1
            errors.append(type(exc).__name__)
            print(city, f"latency_ms={elapsed_ms}", f"error={type(exc).__name__}")
        time.sleep(0.22)

    print(
        "[Summary]",
        f"requests={request_count}",
        f"latency_min_ms={min(latencies) if latencies else 'n/a'}",
        f"latency_avg_ms={round(sum(latencies) / len(latencies)) if latencies else 'n/a'}",
        f"latency_max_ms={max(latencies) if latencies else 'n/a'}",
        f"errors={errors}",
    )


if __name__ == "__main__":
    main()
