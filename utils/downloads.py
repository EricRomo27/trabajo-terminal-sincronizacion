"""Helpers para exponer botones de descarga de gráficas."""

from __future__ import annotations

import io
from typing import Optional

import streamlit as st

from .runtime import runtime_activo


def _mostrar_advertencia(mensaje: str) -> None:
    """Muestra una advertencia si el runtime está disponible."""

    if runtime_activo():
        st.warning(mensaje)


def _kaleido_disponible() -> bool:
    """Detecta si Kaleido está instalado para exportar imágenes de Plotly."""

    try:  # pragma: no cover - la disponibilidad depende del entorno de ejecución
        import kaleido  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def _descarga_plotly_como_png(
    figura: "plotly.graph_objects.Figure",
    *,
    formato: str,
) -> Optional[io.BytesIO]:
    """Intenta exportar la figura como imagen y regresa el buffer listo para descargar."""

    buffer = io.BytesIO()
    try:  # pragma: no cover - depende de Kaleido instalado
        figura.write_image(buffer, format=formato)
    except Exception:
        return None

    buffer.seek(0)
    return buffer


def boton_descarga_plotly(
    figura: "plotly.graph_objects.Figure",
    nombre_archivo: str,
    *,
    etiqueta: str = "📥 Descargar gráfica",
    formato: str = "png",
    etiqueta_fallback: str = "📥 Descargar versión interactiva",
) -> None:
    """Renderiza un botón de descarga para gráficas de Plotly.

    * Si Kaleido está disponible, genera una imagen en el formato indicado.
    * En entornos sin Kaleido, ofrece un HTML interactivo para que la descarga
      nunca falle ni oculte la visualización original.
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
        _mostrar_advertencia(
            "La descarga solo está disponible para objetos plotly.graph_objects.Figure."
        )
        return

    buffer = None
    if _kaleido_disponible():
        buffer = _descarga_plotly_como_png(figura, formato=formato)

    if buffer is not None:
        st.download_button(
            label=etiqueta,
            data=buffer,
            file_name=nombre_archivo,
            mime=f"image/{formato}",
        )
        return

    # Fallback: generar un HTML interactivo para no bloquear la descarga.
    try:
        contenido_html = figura.to_html(include_plotlyjs="cdn")
    except Exception:  # pragma: no cover - depende de la configuración del gráfico
        _mostrar_advertencia(
            "No se pudo preparar la gráfica para descarga."
        )
        return

    nombre_html = nombre_archivo.rsplit(".", 1)[0] + ".html"
    st.download_button(
        label=etiqueta_fallback,
        data=contenido_html,
        file_name=nombre_html,
        mime="text/html",
    )
    st.caption(
        "Se generó una versión interactiva en HTML porque Kaleido no está disponible en el entorno."
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

    grafico_valido = False

    if hasattr(alt, "TopLevelMixin"):
        grafico_valido = isinstance(grafica, alt.TopLevelMixin)

    if not grafico_valido and hasattr(grafica, "to_html"):
        grafico_valido = True

    if not grafico_valido:
        _mostrar_advertencia(
            "No fue posible preparar la gráfica para su descarga."
        )
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
