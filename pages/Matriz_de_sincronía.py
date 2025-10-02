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
    
    for c1 in contaminantes:
        for c2 in contaminantes:
            if c1 == c2:
                matriz.loc[c1, c2] = 100 if metrica == 'tendencia' else 0
                continue
            
            s1_suavizada = df[c1].rolling(30, center=True, min_periods=1).mean()
            s2_suavizada = df[c2].rolling(30, center=True, min_periods=1).mean()

            if metrica == 'tendencia':
                derivada1 = s1_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
                derivada2 = s2_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
                valor = np.mean(np.sign(derivada1) == np.sign(derivada2)) * 100
            
            elif metrica == 'varianza':
                picos1, _ = find_peaks(s1_suavizada, distance=30, height=s1_suavizada.mean())
                picos2, _ = find_peaks(s2_suavizada, distance=30, height=s2_suavizada.mean())
                fechas_picos1 = s1_suavizada.index[picos1]
                fechas_picos2 = s2_suavizada.index[picos2]
                
                # --- LÓGICA DE DESFASE CORREGIDA ---
                desfases = []
                for fecha_pico_maestro in fechas_picos1:
                    picos_esclavo_posteriores = fechas_picos2[fechas_picos2 > fecha_pico_maestro]
                    if not picos_esclavo_posteriores.empty:
                        pico_esclavo_cercano = picos_esclavo_posteriores[0]
                        desfase = (pico_esclavo_cercano - fecha_pico_maestro).days
                        desfases.append(desfase)
                
                valor = np.var(np.array(desfases)) if len(desfases) > 0 else np.nan
            
            matriz.loc[c1, c2] = valor
            
    return matriz

st.title("🌐 Matriz de Sincronía Global")
st.markdown("Esta sección proporciona una visión global de las interrelaciones entre todos los contaminantes.")

df_datos = cargar_datos()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sincronía de Tendencia (%)")
    matriz_tendencia = calcular_matriz(df_datos, 'tendencia')
    fig1, ax1 = plt.subplots(figsize=(10, 8))
    sns.heatmap(matriz_tendencia, ax=ax1, annot=True, fmt=".1f", cmap="viridis", linewidths=.5)
    ax1.set_title("Porcentaje de Tiempo con la Misma Tendencia", fontsize=16)
    st.pyplot(fig1)

with col2:
    st.subheader("Varianza de Desfase entre Picos")
    matriz_varianza = calcular_matriz(df_datos, 'varianza')
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    sns.heatmap(matriz_varianza, ax=ax2, annot=True, fmt=".1f", cmap="magma_r", linewidths=.5)
    ax2.set_title("Varianza del Desfase (días²)", fontsize=16)
    st.pyplot(fig2)