import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import seaborn as sns
import plotly.graph_objects as go
from scipy.signal import find_peaks

st.set_page_config(layout="wide", page_title="Matriz de Sincronía")

@st.cache_data
def cargar_datos():
    with sqlite3.connect('contaminantes.db') as conn:
        df = pd.read_sql_query("SELECT * FROM calidad_aire", conn, parse_dates=['Fecha'], index_col='Fecha')
    return df

@st.cache_data
def calcular_matriz(df, metrica):
    contaminantes = df.columns
    matriz = pd.DataFrame(index=contaminantes, columns=contaminantes, dtype=float)
    
    # Usamos las series originales para la correlación cruzada
    df_original = df
    
    for c1 in contaminantes:
        for c2 in contaminantes:
            if c1 == c2:
                if metrica == 'tendencia': matriz.loc[c1, c2] = 100
                elif metrica == 'varianza': matriz.loc[c1, c2] = 0
                elif metrica == 'desfase': matriz.loc[c1, c2] = 0
                continue
            
            s1_suavizada = df[c1].rolling(30, center=True, min_periods=1).mean()
            s2_suavizada = df[c2].rolling(30, center=True, min_periods=1).mean()

            if metrica == 'tendencia':
                derivada1 = s1_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
                derivada2 = s2_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
                mascara_validos = (~derivada1.isna()) & (~derivada2.isna())
                if mascara_validos.any():
                    valor = (
                        np.mean(
                            np.sign(derivada1[mascara_validos]) == np.sign(derivada2[mascara_validos])
                        )
                        * 100
                    )
                else:
                    valor = np.nan
            
            elif metrica == 'varianza':
                picos1, _ = find_peaks(s1_suavizada, distance=30, height=s1_suavizada.mean())
                picos2, _ = find_peaks(s2_suavizada, distance=30, height=s2_suavizada.mean())
                fechas_picos1 = s1_suavizada.index[picos1]
                fechas_picos2 = s2_suavizada.index[picos2]
                desfases = []
                for fecha_pico_maestro in fechas_picos1:
                    picos_esclavo_posteriores = fechas_picos2[fechas_picos2 > fecha_pico_maestro]
                    if not picos_esclavo_posteriores.empty:
                        pico_esclavo_cercano = picos_esclavo_posteriores[0]
                        desfase = (pico_esclavo_cercano - fecha_pico_maestro).days
                        desfases.append(desfase)
                valor = np.var(np.array(desfases)) if len(desfases) > 0 else np.nan
            
            elif metrica == 'desfase':
                # --- NUEVO CÁLCULO: Correlación Cruzada para encontrar el mejor lag ---
                max_corr, mejor_lag = -1, 0
                serie1_original = df_original[c1]
                serie2_original = df_original[c2]
                for lag in range(-60, 61): # Rango de +/- 60 días
                    corr = serie1_original.corr(serie2_original.shift(lag))
                    if corr > max_corr:
                        max_corr = corr
                        mejor_lag = lag
                valor = mejor_lag
            
            matriz.loc[c1, c2] = valor
            
    return matriz

st.title("🌐 Matriz de Sincronía Global")
st.markdown("Esta sección proporciona una visión global de las interrelaciones entre todos los contaminantes.")

df_datos = cargar_datos()

# --- Visualización de las primeras dos matrices ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Sincronía de Tendencia (%)")
    matriz_tendencia = calcular_matriz(df_datos, 'tendencia')
    tendencia_values = matriz_tendencia.to_numpy(dtype=float)
    tendencia_text = np.empty_like(tendencia_values, dtype=object)
    mask_tendencia = ~np.isnan(tendencia_values)
    tendencia_text[mask_tendencia] = np.vectorize(lambda v: f"{v:.1f}%")(tendencia_values[mask_tendencia])
    tendencia_text[~mask_tendencia] = ""
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
        title="Porcentaje de Tiempo con la Misma Tendencia",
        xaxis_title="Contaminante (columna)",
        yaxis_title="Contaminante (fila)",
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Varianza de Desfase entre Picos")
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
        title="Varianza del Desfase (días²)",
        xaxis_title="Contaminante (columna)",
        yaxis_title="Contaminante (fila)",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- NUEVA VISUALIZACIÓN: Matriz de Desfase ---
st.header("Análisis de Liderazgo (Maestro-Esclavo)")
st.subheader("Matriz de Desfase Óptimo (días)")
st.markdown("""
Esta matriz muestra el número de días de desfase que maximiza la correlación entre dos contaminantes.
- **Valores positivos (rojo):** El contaminante de la columna se **atrasa** respecto al de la fila (el de la fila es el **maestro**).
- **Valores negativos (azul):** El contaminante de la columna se **adelanta** respecto al de la fila (el de la columna es el **maestro**).
- **Valores cercanos a 0 (blanco):** La relación es prácticamente **simultánea**.
""")

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
    title="Desfase para Correlación Máxima (días)",
    xaxis_title="Contaminante (columna)",
    yaxis_title="Contaminante (fila)",
)
st.plotly_chart(fig3, use_container_width=True)
