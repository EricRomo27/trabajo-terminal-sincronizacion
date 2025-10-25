import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st
from scipy.signal import find_peaks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.peak_matching import resumir_desfases
from utils.ui import (
    aplicar_estilos_generales,
    boton_descarga_plotly,
    mostrar_encabezado,
    runtime_activo,
)

if runtime_activo():
    st.set_page_config(layout="wide", page_title="Matriz de Sincronía")
    aplicar_estilos_generales()

@st.cache_data
def cargar_datos():
    with sqlite3.connect('contaminantes.db') as conn:
        df = pd.read_sql_query("SELECT * FROM calidad_aire", conn, parse_dates=['Fecha'], index_col='Fecha')
    return df

@st.cache_data
def calcular_matriz(df, metrica):
    contaminantes = df.columns
    matriz = pd.DataFrame(index=contaminantes, columns=contaminantes, dtype=float)

    # Precalculamos series suavizadas, derivadas y picos por contaminante para reutilizarlos
    series_originales = {contaminante: df[contaminante] for contaminante in contaminantes}
    series_suavizadas = {
        contaminante: series_originales[contaminante].rolling(30, center=True, min_periods=1).mean()
        for contaminante in contaminantes
    }
    derivadas_suavizadas = {
        contaminante: series_suavizadas[contaminante]
        .rolling(15, center=True)
        .mean()
        .pct_change(fill_method=None)
        for contaminante in contaminantes
    }
    picos_indices = {}
    picos_fechas = {}
    for contaminante, serie_suavizada in series_suavizadas.items():
        indices, _ = find_peaks(
            serie_suavizada,
            distance=30,
            height=serie_suavizada.mean(),
        )
        picos_indices[contaminante] = indices
        picos_fechas[contaminante] = serie_suavizada.index[indices]

    for c1 in contaminantes:
        for c2 in contaminantes:
            if c1 == c2:
                if metrica == 'tendencia': matriz.loc[c1, c2] = 100
                elif metrica == 'varianza': matriz.loc[c1, c2] = 0
                elif metrica == 'desfase': matriz.loc[c1, c2] = 0
                continue

            s1_suavizada = series_suavizadas[c1]
            s2_suavizada = series_suavizadas[c2]

            if metrica == 'tendencia':
                derivada1 = derivadas_suavizadas[c1]
                derivada2 = derivadas_suavizadas[c2]
                valor = np.mean(np.sign(derivada1) == np.sign(derivada2)) * 100

            elif metrica == 'varianza':
                fechas_picos1 = picos_fechas[c1]
                fechas_picos2 = picos_fechas[c2]
                resumen = resumir_desfases(
                    fechas_picos1,
                    fechas_picos2,
                    ventana_busqueda=90,
                    ventana_confiable=45,
                )
                valor = resumen["varianza"]

            elif metrica == 'desfase':
                # --- NUEVO CÁLCULO: Correlación Cruzada para encontrar el mejor lag ---
                max_corr, mejor_lag = -1, 0
                serie1_original = series_originales[c1]
                serie2_original = series_originales[c2]
                for lag in range(-60, 61): # Rango de +/- 60 días
                    corr = serie1_original.corr(serie2_original.shift(lag))
                    if corr > max_corr:
                        max_corr = corr
                        mejor_lag = lag
                valor = mejor_lag
            
            matriz.loc[c1, c2] = valor
            
    return matriz

if runtime_activo():
    mostrar_encabezado(
        "Matriz de sincronía global",
        "Revisa de un vistazo cómo interactúan los contaminantes: tendencias compartidas,"
        " desfases entre picos y liderazgo temporal.",
        "🌐",
    )

    df_datos = cargar_datos()

    matriz_tendencia = calcular_matriz(df_datos, 'tendencia')
    tendencia_values = matriz_tendencia.to_numpy(dtype=float)
    tendencia_text = np.empty_like(tendencia_values, dtype=object)
    mask_tendencia = ~np.isnan(tendencia_values)
    tendencia_text[mask_tendencia] = np.vectorize(lambda v: f"{v:.1f}%")(tendencia_values[mask_tendencia])
    tendencia_text[~mask_tendencia] = ""

    matriz_varianza = calcular_matriz(df_datos, 'varianza')
    varianza_values = matriz_varianza.to_numpy(dtype=float)
    varianza_text = np.empty_like(varianza_values, dtype=object)
    mask_varianza = ~np.isnan(varianza_values)
    varianza_text[mask_varianza] = np.vectorize(lambda v: f"{v:.1f}")(varianza_values[mask_varianza])
    varianza_text[~mask_varianza] = ""
    magma_reversed = sns.color_palette("magma", as_cmap=False, n_colors=256)[::-1]
    magma_colorscale = [
        (i / (len(magma_reversed) - 1), f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})")
        for i, (r, g, b) in enumerate(magma_reversed)
    ]

    matriz_desfase = calcular_matriz(df_datos, 'desfase')
    desfase_values = matriz_desfase.to_numpy(dtype=float)
    desfase_text = np.empty_like(desfase_values, dtype=object)
    mask_desfase = ~np.isnan(desfase_values)
    desfase_text[mask_desfase] = np.vectorize(lambda v: f"{v:.0f}")(desfase_values[mask_desfase])
    desfase_text[~mask_desfase] = ""
    vlag_palette = sns.color_palette("vlag", as_cmap=False, n_colors=256)
    vlag_colorscale = [
        (i / (len(vlag_palette) - 1), f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})")
        for i, (r, g, b) in enumerate(vlag_palette)
    ]

    pestañas = st.tabs([
        "Sincronía de tendencia",
        "Varianza del desfase",
        "Desfase óptimo",
    ])

    with pestañas[0]:
        fig1 = go.Figure(
            data=[
                go.Heatmap(
                    z=tendencia_values,
                    x=matriz_tendencia.columns,
                    y=matriz_tendencia.index,
                    colorscale="Viridis",
                    text=tendencia_text,
                    texttemplate="%{text}",
                    textfont=dict(color="black"),
                    hovertemplate=(
                        "Contaminante fila: %{y}<br>Contaminante columna: %{x}<br>"
                        "Sincronía: %{z:.1f}%<extra></extra>"
                    ),
                    colorbar=dict(title="%"),
                    zmin=np.nanmin(tendencia_values),
                    zmax=np.nanmax(tendencia_values),
                )
            ]
        )
        fig1.update_layout(
            title="Porcentaje de tiempo con la misma dirección de cambio",
            xaxis_title="Contaminante (columna)",
            yaxis_title="Contaminante (fila)",
        )
        st.plotly_chart(fig1, use_container_width=True)
        boton_descarga_plotly(
            fig1,
            "matriz_sincronia_tendencia.png",
            etiqueta="📥 Descargar matriz de tendencia",
        )
        st.caption(
            "Valores cercanos al 100% indican respuestas sincronizadas; usa esta pestaña para detectar"
            " pares con comportamientos muy similares."
        )

    with pestañas[1]:
        fig2 = go.Figure(
            data=[
                go.Heatmap(
                    z=varianza_values,
                    x=matriz_varianza.columns,
                    y=matriz_varianza.index,
                    colorscale=magma_colorscale,
                    text=varianza_text,
                    texttemplate="%{text}",
                    textfont=dict(color="black"),
                    hovertemplate=(
                        "Contaminante fila: %{y}<br>Contaminante columna: %{x}<br>"
                        "Varianza del desfase: %{z:.1f} días²<extra></extra>"
                    ),
                    colorbar=dict(title="días²"),
                )
            ]
        )
        fig2.update_layout(
            title="Dispersión de desfases entre picos emparejados",
            xaxis_title="Contaminante (columna)",
            yaxis_title="Contaminante (fila)",
        )
        st.plotly_chart(fig2, use_container_width=True)
        boton_descarga_plotly(
            fig2,
            "matriz_varianza_desfase.png",
            etiqueta="📥 Descargar matriz de varianza",
        )
        st.caption(
            "Revisa esta matriz para identificar pares con desfases elevados que requieran análisis"
            " detallado en la vista comparativa."
        )

    with pestañas[2]:
        fig3 = go.Figure(
            data=[
                go.Heatmap(
                    z=desfase_values,
                    x=matriz_desfase.columns,
                    y=matriz_desfase.index,
                    colorscale=vlag_colorscale,
                    zmid=0,
                    text=desfase_text,
                    texttemplate="%{text}",
                    textfont=dict(color="black"),
                    hovertemplate=(
                        "Contaminante fila: %{y}<br>Contaminante columna: %{x}<br>"
                        "Desfase óptimo: %{z:.0f} días<extra></extra>"
                    ),
                    colorbar=dict(title="días"),
                )
            ]
        )
        fig3.update_layout(
            title="Desfase que maximiza la correlación",
            xaxis_title="Contaminante (columna)",
            yaxis_title="Contaminante (fila)",
        )
        st.plotly_chart(fig3, use_container_width=True)
        boton_descarga_plotly(
            fig3,
            "matriz_desfase_optimo.png",
            etiqueta="📥 Descargar matriz de desfase",
        )
        st.caption(
            "Valores positivos indican que la serie en columnas se atrasa respecto a la fila; valores"
            " negativos implican que se adelanta."
        )

    st.subheader("Sugerencias de análisis")
    st.markdown(
        "- Combina la sincronía de tendencia con la varianza para distinguir pares simultáneos de aquellos con desfases amplios.\n"
        "- Investiga en el análisis comparativo los pares con varianza alta para revisar los picos específicos que la provocan.\n"
        "- La matriz de desfase óptimo te ayuda a identificar liderazgos potenciales y periodos de atraso entre contaminantes."
    )
