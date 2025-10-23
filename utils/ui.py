"""Herramientas de estilo y componentes reutilizables para Streamlit.

Este módulo centraliza los estilos personalizados que dan una apariencia
consistente y más atractiva a toda la aplicación, además de ofrecer
componentes ligeros (como tarjetas de métricas) que pueden reutilizarse
en las distintas páginas sin repetir código HTML.
"""

from __future__ import annotations

import html
import re
from typing import Iterable, Mapping, Sequence

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
            :root {
                --sincronia-primary: #005d8f;
                --sincronia-primary-light: #0f8ecf;
                --sincronia-bg-soft: #f2f7fb;
            }

            .block-container {
                padding-top: 2.2rem !important;
                padding-bottom: 3rem !important;
                max-width: 1200px;
            }

            .sincronia-hero {
                background: linear-gradient(135deg, rgba(0, 93, 143, 0.12), rgba(15, 142, 207, 0.28));
                border: 1px solid rgba(0, 93, 143, 0.12);
                border-radius: 20px;
                padding: 1.8rem 2rem;
                margin-bottom: 1rem;
                display: flex;
                gap: 1.2rem;
                align-items: center;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.04);
            }

            .sincronia-hero-icon {
                font-size: 2.8rem;
            }

            .sincronia-hero-body h1 {
                font-size: clamp(1.8rem, 3vw, 2.4rem);
                margin-bottom: 0.4rem;
                color: #03344f;
            }

            .sincronia-hero-body p {
                margin: 0;
                font-size: 1rem;
                line-height: 1.5;
                color: #1f2a33;
            }

            .sincronia-metric-card {
                background: white;
                border-radius: 16px;
                padding: 1.2rem 1.4rem;
                border: 1px solid rgba(3, 52, 79, 0.08);
                box-shadow: 0 10px 24px rgba(3, 52, 79, 0.06);
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
                margin-bottom: 1rem;
            }

            .sincronia-metric-card .stMetric {
                background: transparent;
            }

            .sincronia-metric-card .metric-delta {
                font-size: 0.85rem;
                margin: 0;
            }

            .sincronia-metric-card .metric-delta.neutral {
                color: #315b7d;
            }

            .sincronia-metric-card .metric-delta.positive {
                color: #207a3c;
            }

            .sincronia-metric-card .metric-delta.negative {
                color: #ba1a1a;
            }

            .sincronia-metric-card .metric-description {
                color: #485a6b;
                font-size: 0.88rem;
                margin: 0;
                line-height: 1.45;
            }

            .sincronia-info-card {
                background: var(--sincronia-bg-soft);
                border-radius: 16px;
                padding: 1.2rem 1.4rem;
                border: 1px solid rgba(0, 93, 143, 0.12);
                box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
                height: 100%;
            }

            .sincronia-info-card h3 {
                margin-top: 0.6rem;
                margin-bottom: 0.4rem;
                font-size: 1.05rem;
                color: #03344f;
            }

            .sincronia-info-card p {
                margin: 0;
                color: #334655;
                font-size: 0.95rem;
                line-height: 1.5;
            }

            .sincronia-info-card .sincronia-info-icon {
                font-size: 1.8rem;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.6rem;
            }

            .stTabs [data-baseweb="tab"] {
                background: rgba(3, 52, 79, 0.06);
                border-radius: 999px;
                padding: 0.4rem 1.2rem;
            }

            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: rgba(0, 93, 143, 0.18);
                color: #03344f;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_texto_rico(texto: str) -> str:
    """Convierte un subconjunto sencillo de Markdown a HTML seguro."""

    texto_escape = html.escape(texto)
    texto_escape = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto_escape)
    texto_escape = re.sub(r"\*(.+?)\*", r"<em>\1</em>", texto_escape)
    return texto_escape.replace("\n", "<br>")


def mostrar_encabezado(titulo: str, descripcion: str, emoji: str = "") -> None:
    """Renderiza un encabezado tipo *hero* con icono y descripción."""

    if not _runtime_activo():
        return

    titulo_html = _render_texto_rico(titulo)
    descripcion_html = _render_texto_rico(descripcion) if descripcion else ""
    emoji_html = html.escape(emoji)

    st.markdown(
        f"""
        <div class="sincronia-hero">
            <div class="sincronia-hero-icon">{emoji_html}</div>
            <div class="sincronia-hero-body">
                <h1>{titulo_html}</h1>
                {f"<p>{descripcion_html}</p>" if descripcion_html else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    metricas_secuencia: Sequence[Mapping[str, object]] = list(metricas)

    for indice_inicio in range(0, len(metricas_secuencia), columnas):
        fila = metricas_secuencia[indice_inicio : indice_inicio + columnas]
        cols = st.columns(len(fila))

        for col, metric in zip(cols, fila):
            icono = metric.get("icono") or ""
            titulo = str(metric.get("titulo", ""))
            valor = str(metric.get("valor", ""))
            descripcion = metric.get("descripcion")
            delta = metric.get("delta") if isinstance(metric.get("delta"), Mapping) else None
            delta_texto = str(delta.get("texto", "")) if delta else ""
            delta_tipo = (delta.get("tipo", "").lower() if delta else "").strip()

            with col:
                with st.container():
                    st.markdown("<div class='sincronia-metric-card'>", unsafe_allow_html=True)
                    etiqueta = f"{icono} {titulo}".strip()
                    delta_para_metric = delta_texto if delta_tipo in {"positive", "negative"} else None
                    st.metric(label=etiqueta or " ", value=valor, delta=delta_para_metric)

                    if delta_texto:
                        indicador = {
                            "positive": "🟢",
                            "negative": "🔻",
                            "neutral": "ℹ️",
                        }.get(delta_tipo or "neutral", "ℹ️")
                        st.markdown(
                            f"<p class='metric-delta {delta_tipo or 'neutral'}'>{indicador} {html.escape(delta_texto)}</p>",
                            unsafe_allow_html=True,
                        )

                    if descripcion:
                        st.markdown(
                            f"<p class='metric-description'>{_render_texto_rico(str(descripcion))}</p>",
                            unsafe_allow_html=True,
                        )

                    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_tarjetas_descriptivas(
    tarjetas: Iterable[Mapping[str, object]], *, columnas: int = 3
) -> None:
    """Renderiza tarjetas de texto para resúmenes o listados de herramientas."""

    if not _runtime_activo():
        return

    tarjetas_lista: Sequence[Mapping[str, object]] = list(tarjetas)
    if not tarjetas_lista:
        return

    columnas = max(1, min(columnas, 3))

    for indice_inicio in range(0, len(tarjetas_lista), columnas):
        fila = tarjetas_lista[indice_inicio : indice_inicio + columnas]
        cols = st.columns(len(fila))

        for col, tarjeta in zip(cols, fila):
            icono = html.escape(str(tarjeta.get("icono", "")))
            titulo = _render_texto_rico(str(tarjeta.get("titulo", "")))
            descripcion = _render_texto_rico(str(tarjeta.get("descripcion", "")))

            with col:
                st.markdown(
                    f"""
                    <div class="sincronia-info-card">
                        <div class="sincronia-info-icon">{icono}</div>
                        <h3>{titulo}</h3>
                        <p>{descripcion}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
