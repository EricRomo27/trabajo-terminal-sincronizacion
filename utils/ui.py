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
        :root {
            --color-primario: #2f80ed;
            --color-secundario: #56ccf2;
            --color-fondo-claro: rgba(255, 255, 255, 0.82);
            --color-texto-principal: #0f2d4a;
            --color-texto-secundario: #46607a;
            --color-exito: #0b7a75;
            --color-alerta: #d65a31;
            --color-neutro: #6b7a99;
            --sombra-suave: 0 18px 40px rgba(15, 45, 74, 0.12);
            --borde-suave: 1px solid rgba(15, 45, 74, 0.08);
        }

        .stApp {
            background: linear-gradient(180deg, rgba(47,128,237,0.10) 0%, rgba(236,248,255,0.65) 100%);
        }

        .block-container {
            padding-top: 2.8rem !important;
            padding-bottom: 4rem !important;
            max-width: 1200px;
        }

        .app-hero {
            background: linear-gradient(135deg, rgba(47,128,237,0.95) 0%, rgba(86,204,242,0.85) 100%);
            border-radius: 22px;
            padding: 2.2rem 2.6rem;
            color: white;
            display: flex;
            align-items: center;
            gap: 1.8rem;
            margin-bottom: 2.2rem;
            box-shadow: var(--sombra-suave);
        }

        .app-hero h1 {
            font-size: 2.2rem;
            line-height: 1.15;
            margin: 0;
            font-weight: 700;
        }

        .app-hero p {
            margin: 0.4rem 0 0;
            font-size: 1.05rem;
            color: rgba(255, 255, 255, 0.95);
        }

        .hero-icon {
            font-size: 3rem;
            filter: drop-shadow(0 10px 18px rgba(15, 45, 74, 0.35));
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.2rem;
            margin: 1.4rem 0 2rem;
        }

        .metric-card {
            background: var(--color-fondo-claro);
            border-radius: 18px;
            padding: 1.4rem 1.5rem;
            border: var(--borde-suave);
            box-shadow: var(--sombra-suave);
            position: relative;
            overflow: hidden;
        }

        .metric-card::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(145deg, rgba(47,128,237,0.08), rgba(86,204,242,0.12));
            z-index: 0;
        }

        .metric-content {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .metric-icon {
            font-size: 1.8rem;
            align-self: flex-start;
            filter: drop-shadow(0 6px 16px rgba(47,128,237,0.35));
        }

        .metric-label {
            font-weight: 600;
            color: var(--color-texto-principal);
            font-size: 1.02rem;
        }

        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            color: var(--color-primario);
        }

        .metric-delta {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .metric-delta.positive { color: var(--color-exito); }
        .metric-delta.negative { color: var(--color-alerta); }
        .metric-delta.neutral { color: var(--color-neutro); }

        .metric-description {
            margin: 0;
            color: var(--color-texto-secundario);
            font-size: 0.95rem;
            line-height: 1.4;
        }

        .app-section {
            background: var(--color-fondo-claro);
            border-radius: 20px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.8rem;
            border: var(--borde-suave);
            box-shadow: var(--sombra-suave);
        }

        .app-section h3 {
            margin-top: 0;
            color: var(--color-texto-principal);
        }

        .app-section p, .app-section ul, .app-section li {
            color: var(--color-texto-secundario);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(47, 128, 237, 0.12);
            border-radius: 999px;
            color: var(--color-texto-principal);
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(47,128,237,0.24) !important;
            color: var(--color-texto-principal) !important;
        }

        .stAlert {
            border-radius: 16px !important;
        }

        .app-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.2rem;
            margin-top: 1.2rem;
        }

        .app-card {
            background: rgba(255, 255, 255, 0.88);
            border-radius: 18px;
            padding: 1.6rem;
            border: var(--borde-suave);
            box-shadow: var(--sombra-suave);
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }

        .app-card h4 {
            margin: 0;
            font-size: 1.1rem;
            color: var(--color-texto-principal);
        }

        .app-card p {
            margin: 0;
            font-size: 0.95rem;
        }

        .app-card span {
            font-weight: 600;
            color: var(--color-texto-principal);
        }

        .stDataFrame div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px;
        }

        .stDownloadButton button {
            border-radius: 999px;
            padding: 0.6rem 1.6rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado(titulo: str, descripcion: str, emoji: str = "") -> None:
    """Renderiza un encabezado tipo *hero* con icono y descripción."""

    if not _runtime_activo():
        return

    icono_html = f'<div class="hero-icon">{emoji}</div>' if emoji else ""
    st.markdown(
        f"""
        <div class="app-hero">
            {icono_html}
            <div>
                <h1>{titulo}</h1>
                <p>{descripcion}</p>
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

    tarjetas = []
    for metric in metricas:
        icono = metric.get("icono", "") or ""
        titulo = metric.get("titulo", "")
        valor = metric.get("valor", "")
        descripcion = metric.get("descripcion", "")
        delta = metric.get("delta")

        if isinstance(delta, Mapping):
            delta_texto = str(delta.get("texto", ""))
            delta_tipo = str(delta.get("tipo", "neutral"))
            delta_html = (
                f'<span class="metric-delta {delta_tipo}">{delta_texto}</span>'
                if delta_texto
                else ""
            )
        else:
            delta_html = ""

        tarjetas.append(
            f"""
            <div class="metric-card">
                <div class="metric-content">
                    <div class="metric-icon">{icono}</div>
                    <span class="metric-label">{titulo}</span>
                    <span class="metric-value">{valor}</span>
                    {delta_html}
                    <p class="metric-description">{descripcion}</p>
                </div>
            </div>
            """
        )

    if not tarjetas:
        return

    st.markdown(
        f"<div class='metric-grid'>{''.join(tarjetas)}</div>", unsafe_allow_html=True
    )
