from bisect import bisect_left
from typing import Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def _ordenar_fechas(fechas: Iterable[pd.Timestamp]) -> List[pd.Timestamp]:
    """Devuelve una lista ordenada de fechas como objetos Timestamp."""
    return sorted(pd.to_datetime(list(fechas)))


def calcular_desfases_entre_picos(
    fechas_maestro: Iterable[pd.Timestamp],
    fechas_esclavo: Iterable[pd.Timestamp],
    ventana_maxima_dias: int = 90,
    *,
    return_pares: bool = False,
) -> Union[List[int], Tuple[List[int], List[Tuple[pd.Timestamp, pd.Timestamp, int]]]]:
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
        return ([], []) if return_pares else []

    fechas_maestro_ordenadas = _ordenar_fechas(fechas_maestro_lista)
    fechas_esclavo_restantes = _ordenar_fechas(fechas_esclavo_lista)

    desfases: List[int] = []
    pares: List[Tuple[pd.Timestamp, pd.Timestamp, int]] = []

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
            pares.append((fecha_maestro, fecha_candidata, desfase_dias))
            del fechas_esclavo_restantes[indice_seleccionado]

    if return_pares:
        return desfases, pares
    return desfases


def resumir_desfases(
    fechas_maestro: Iterable[pd.Timestamp],
    fechas_esclavo: Iterable[pd.Timestamp],
    *,
    ventana_busqueda: int = 90,
    ventana_confiable: Optional[int] = 45,
) -> dict:
    """Calcula métricas de desfase entre dos conjuntos de picos.

    Devuelve la lista completa de emparejamientos encontrados dentro de la
    ``ventana_busqueda`` así como un subconjunto "confiable" limitado por la
    ``ventana_confiable``. Las métricas (varianza, desfase medio y desviación
    estándar) se calculan únicamente con los emparejamientos confiables para
    evitar que coincidencias muy lejanas distorsionen el resultado.
    """

    ventana_busqueda = max(0, int(ventana_busqueda))
    if ventana_confiable is not None:
        ventana_confiable = max(0, int(ventana_confiable))
        ventana_confiable = min(ventana_confiable, ventana_busqueda)

    desfases, pares = calcular_desfases_entre_picos(
        fechas_maestro,
        fechas_esclavo,
        ventana_maxima_dias=ventana_busqueda,
        return_pares=True,
    )

    if ventana_confiable is None:
        pares_validos = pares
        pares_descartados: List[Tuple[pd.Timestamp, pd.Timestamp, int]] = []
    else:
        pares_validos = [
            (maestro, esclavo, desfase)
            for maestro, esclavo, desfase in pares
            if abs(desfase) <= ventana_confiable
        ]
        pares_descartados = [
            (maestro, esclavo, desfase)
            for maestro, esclavo, desfase in pares
            if abs(desfase) > ventana_confiable
        ]

    desfases_validos = [desfase for _, _, desfase in pares_validos]
    arr = np.array(desfases_validos, dtype=float)

    if arr.size == 0:
        varianza = np.nan
        desfase_medio = np.nan
        desviacion = np.nan
    elif arr.size == 1:
        varianza = 0.0
        desfase_medio = float(arr[0])
        desviacion = 0.0
    else:
        varianza = float(np.var(arr))
        desfase_medio = float(np.mean(arr))
        desviacion = float(np.std(arr))

    return {
        "desfases": desfases,
        "pares": pares,
        "desfases_validos": desfases_validos,
        "pares_validos": pares_validos,
        "pares_descartados": pares_descartados,
        "varianza": varianza,
        "desfase_medio": desfase_medio,
        "desviacion_estandar": desviacion,
        "ventana_busqueda": ventana_busqueda,
        "ventana_confiable": ventana_confiable,
    }
