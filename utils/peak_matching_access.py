"""Utilidades de acceso resiliente para helpers de emparejamiento de picos."""
from __future__ import annotations

import importlib
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

import utils.peak_matching as _peak_matching


_Pareja = Tuple[pd.Timestamp, pd.Timestamp, int]


def _calcular_metricas(desfases: Iterable[int]) -> Tuple[float, float, float]:
    arr = np.array(list(desfases), dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    if arr.size == 1:
        valor = float(arr[0])
        return 0.0, valor, 0.0
    return float(np.var(arr)), float(np.mean(arr)), float(np.std(arr))


def _resumir_desfases_fallback(
    calcular_desfases: Callable[..., List[int]],
    fechas_maestro: Iterable[pd.Timestamp],
    fechas_esclavo: Iterable[pd.Timestamp],
    *,
    ventana_busqueda: int = 90,
    ventana_confiable: Optional[int] = 45,
) -> Dict[str, object]:
    ventana_busqueda = max(0, int(ventana_busqueda))
    if ventana_confiable is not None:
        ventana_confiable = max(0, int(ventana_confiable))
        ventana_confiable = min(ventana_confiable, ventana_busqueda)

    pares: List[_Pareja] = []
    desfases: List[int] = []
    try:
        resultado = calcular_desfases(
            fechas_maestro,
            fechas_esclavo,
            ventana_maxima_dias=ventana_busqueda,
            return_pares=True,
        )
    except TypeError:
        desfases = list(
            calcular_desfases(
                fechas_maestro,
                fechas_esclavo,
                ventana_maxima_dias=ventana_busqueda,
            )
        )
    else:
        if isinstance(resultado, tuple) and len(resultado) == 2:
            desfases, pares = resultado
        else:
            desfases = list(resultado)

    if ventana_confiable is None or not pares:
        pares_validos = pares
        pares_descartados: List[_Pareja] = []
        desfases_validos = list(desfases)
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

    varianza, desfase_medio, desviacion = _calcular_metricas(desfases_validos)

    return {
        "desfases": list(desfases),
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


def obtener_resumir_desfases() -> Callable[..., Dict[str, object]]:
    """Recupera ``resumir_desfases`` asegurando recarga del módulo base."""

    modulo = importlib.reload(_peak_matching)
    funcion = getattr(modulo, "resumir_desfases", None)
    if callable(funcion):
        return funcion

    calcular = getattr(modulo, "calcular_desfases_entre_picos", None)
    if not callable(calcular):
        raise ImportError(
            "utils.peak_matching no expone calcular_desfases_entre_picos tras recarga"
        )

    def _fallback(*args, **kwargs) -> Dict[str, object]:
        return _resumir_desfases_fallback(calcular, *args, **kwargs)

    return _fallback


def resumir_desfases_seguro(*args, **kwargs) -> Dict[str, object]:
    """Proxy que delega en ``resumir_desfases`` recargado o en un fallback."""

    funcion = obtener_resumir_desfases()
    return funcion(*args, **kwargs)
