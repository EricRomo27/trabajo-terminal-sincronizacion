"""Helpers para exponer botones de descarga de gráficas."""

from __future__ import annotations

import io

import streamlit as st

from .runtime import runtime_activo


def _mostrar_advertencia(mensaje: str) -> None:
    """Muestra una advertencia si el runtime está disponible."""

    if runtime_activo():
        st.warning(mensaje)


def boton_descarga_plotly(
    figura: "plotly.graph_objects.Figure",
    nombre_archivo: str,
    *,
    etiqueta: str = "📥 Descargar gráfica",
    formato: str = "png",
) -> None:
    """Renderiza un botón para descargar una figura de Plotly como imagen.

    La función es segura de invocar fuera del runtime de Streamlit: simplemente
    no realiza ninguna acción en ese escenario. Si la figura no puede
    exportarse (por ejemplo, por falta de Kaleido), se muestra una advertencia
    amigable en la interfaz.
    """

    if not runtime_activo():
        return

    try:
        from plotly.graph_objects import Figure  # importación perezosa
    except ImportError:
        _mostrar_advertencia(
            "Plotly no está disponible para exportar la gráfica. Instala 'plotly' y 'kaleido' para habilitar esta función."
        )
        return

    if not isinstance(figura, Figure):
        _mostrar_advertencia("La descarga solo está disponible para objetos plotly.graph_objects.Figure.")
        return

    buffer = io.BytesIO()
    try:
        figura.write_image(buffer, format=formato)
    except Exception:  # pragma: no cover - depende de Kaleido instalado
        _mostrar_advertencia(
            "No fue posible generar la descarga de la gráfica (verifica que Kaleido esté correctamente instalado)."
        )
        return

    buffer.seek(0)
    st.download_button(
        label=etiqueta,
        data=buffer,
        file_name=nombre_archivo,
        mime=f"image/{formato}",
    )


def boton_descarga_altair(
    grafica: "altair.Chart",
    nombre_archivo: str,
    *,
    etiqueta: str = "📥 Descargar gráfica (HTML)",
) -> None:
    """Renderiza un botón para descargar gráficos de Altair como archivo HTML interactivo."""

    if not runtime_activo():
        return

    try:
        import altair as alt  # importación perezosa
    except ImportError:
        _mostrar_advertencia("Altair no está disponible para exportar la gráfica.")
        return

    if not isinstance(grafica, alt.Chart):
        _mostrar_advertencia("La descarga solo está disponible para objetos altair.Chart.")
        return

    try:
        contenido_html = grafica.to_html()
    except Exception:  # pragma: no cover - depende de la configuración del gráfico
        _mostrar_advertencia("No se pudo generar el archivo HTML de la gráfica para su descarga.")
        return

    st.download_button(
        label=etiqueta,
        data=contenido_html,
        file_name=nombre_archivo,
        mime="text/html",
    )


__all__ = ["boton_descarga_plotly", "boton_descarga_altair"]
