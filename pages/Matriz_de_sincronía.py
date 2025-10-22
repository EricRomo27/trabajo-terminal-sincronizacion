import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
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
    anotaciones_tendencia = matriz_tendencia.applymap(lambda v: "N/D" if pd.isna(v) else f"{v:.1f}")
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    sns.heatmap(matriz_tendencia, ax=ax1, annot=anotaciones_tendencia, fmt="", cmap="viridis", linewidths=.5)
    ax1.set_title("Porcentaje de Tiempo con la Misma Tendencia")
    st.pyplot(fig1)

with col2:
    st.subheader("Varianza de Desfase entre Picos")
    matriz_varianza = calcular_matriz(df_datos, 'varianza')
    anotaciones_varianza = matriz_varianza.applymap(lambda v: "N/D" if pd.isna(v) else f"{v:.1f}")
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    sns.heatmap(matriz_varianza, ax=ax2, annot=anotaciones_varianza, fmt="", cmap="magma_r", linewidths=.5)
    ax2.set_title("Varianza del Desfase (días²)")
    st.pyplot(fig2)

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
fig3, ax3 = plt.subplots(figsize=(10, 8))
# Usamos un mapa de color divergente ('vlag') para distinguir positivo/negativo
sns.heatmap(matriz_desfase, ax=ax3, annot=True, fmt=".0f", cmap="vlag", center=0, linewidths=.5)
ax3.set_title("Desfase para Correlación Máxima (días)")
st.pyplot(fig3)
