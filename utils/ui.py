"""Herramientas de estilo y componentes reutilizables para Streamlit.

Este módulo centraliza los estilos personalizados que dan una apariencia
consistente y más atractiva a toda la aplicación, además de ofrecer
componentes ligeros (como tarjetas de métricas) que pueden reutilizarse
en las distintas páginas sin repetir código HTML.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import streamlit as st


def _runtime_activo() -> bool:
    """Indica si la app se está ejecutando dentro del runtime de Streamlit."""

    try:
        return st.runtime.exists()
    except Exception:  # pragma: no cover - protección ante cambios de API
        return False


def aplicar_estilos_generales() -> None:
    """Inyecta estilos globales una sola vez por sesión de Streamlit.

    Se utiliza ``st.session_state`` para evitar que el bloque CSS se
    duplique en cada reinvocación de la página.
    """

    if not _runtime_activo():
        return

    clave_estado = "_estilos_sincronia_aplicados"
    if st.session_state.get(clave_estado):
        return

    st.session_state[clave_estado] = True
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2.2rem !important;
            padding-bottom: 3rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado(titulo: str, descripcion: str, emoji: str = "") -> None:
    """Renderiza un encabezado tipo *hero* con icono y descripción."""

    if not _runtime_activo():
        return

    encabezado = f"{emoji} {titulo}".strip()
    st.title(encabezado)
    if descripcion:
        st.caption(descripcion)


def mostrar_tarjetas_metricas(metricas: Iterable[Mapping[str, object]]) -> None:
    """Muestra una cuadrícula de tarjetas con métricas clave.

    Cada métrica debe incluir al menos las llaves ``titulo``, ``valor`` y
    ``descripcion``. Opcionalmente puede contener ``icono`` y una
    estructura ``delta`` con ``texto`` y ``tipo`` (`positive`,
    `negative` o `neutral`).
    """

    if not _runtime_activo():
        return

    if not metricas:
        return

    columnas = min(3, len(metricas))
    cols = st.columns(columnas)

    for indice, metric in enumerate(metricas):
        col = cols[indice % columnas]
        icono = metric.get("icono") or ""
        titulo = str(metric.get("titulo", ""))
        valor = str(metric.get("valor", ""))
        descripcion = metric.get("descripcion")
        delta = metric.get("delta") if isinstance(metric.get("delta"), Mapping) else None
        delta_texto = str(delta.get("texto", "")) if delta else ""
        delta_tipo = (delta.get("tipo", "").lower() if delta else "").strip()

        with col:
            etiqueta = f"{icono} {titulo}".strip()
            delta_para_metric = delta_texto if delta_tipo in {"positive", "negative"} else None
            st.metric(label=etiqueta or " ", value=valor, delta=delta_para_metric)

            if delta_texto:
                indicador = {
                    "positive": "🟢",
                    "negative": "🔻",
                    "neutral": "ℹ️",
                }.get(delta_tipo or "neutral", "ℹ️")
                st.caption(f"{indicador} {delta_texto}")

            if descripcion:
                st.caption(str(descripcion))
