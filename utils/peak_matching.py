from bisect import bisect_left
from typing import Iterable, List

import pandas as pd


def _ordenar_fechas(fechas: Iterable[pd.Timestamp]) -> List[pd.Timestamp]:
    """Devuelve una lista ordenada de fechas como objetos Timestamp."""
    return sorted(pd.to_datetime(list(fechas)))


def calcular_desfases_entre_picos(
    fechas_maestro: Iterable[pd.Timestamp],
    fechas_esclavo: Iterable[pd.Timestamp],
    ventana_maxima_dias: int = 90,
) -> List[int]:
    """Calcula los desfases (en días) entre los picos maestro y esclavo.

    Alinea cada pico maestro con el pico esclavo temporalmente más cercano
    sin reutilizar coincidencias previas. Solo se consideran coincidencias
    dentro de la ``ventana_maxima_dias`` indicada.
    """
    if ventana_maxima_dias < 0:
        raise ValueError("ventana_maxima_dias debe ser no negativa")

    fechas_maestro_lista = list(fechas_maestro)
    fechas_esclavo_lista = list(fechas_esclavo)

    if len(fechas_maestro_lista) == 0 or len(fechas_esclavo_lista) == 0:
        return []

    fechas_maestro_ordenadas = _ordenar_fechas(fechas_maestro_lista)
    fechas_esclavo_restantes = _ordenar_fechas(fechas_esclavo_lista)

    desfases: List[int] = []

    for fecha_maestro in fechas_maestro_ordenadas:
        if not fechas_esclavo_restantes:
            break

        posicion = bisect_left(fechas_esclavo_restantes, fecha_maestro)
        candidatos = []
        if posicion < len(fechas_esclavo_restantes):
            candidatos.append((posicion, fechas_esclavo_restantes[posicion]))
        if posicion > 0:
            indice_previo = posicion - 1
            candidatos.append((indice_previo, fechas_esclavo_restantes[indice_previo]))

        if not candidatos:
            continue

        indice_seleccionado, fecha_candidata = min(
            candidatos,
            key=lambda item: (
                abs((item[1] - fecha_maestro).days),
                (item[1] - fecha_maestro).days,
            ),
        )

        desfase_dias = (fecha_candidata - fecha_maestro).days
        if abs(desfase_dias) <= ventana_maxima_dias:
            desfases.append(desfase_dias)
            del fechas_esclavo_restantes[indice_seleccionado]

    return desfases
