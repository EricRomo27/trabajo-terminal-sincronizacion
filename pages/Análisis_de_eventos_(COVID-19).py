import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
from scipy.signal import find_peaks

st.set_page_config(layout="wide", page_title="Análisis de Eventos")

@st.cache_data
def cargar_datos():
    with sqlite3.connect('contaminantes.db') as conn:
        df = pd.read_sql_query("SELECT * FROM calidad_aire", conn, parse_dates=['Fecha'], index_col='Fecha')
    return df

def calcular_metricas_periodo(df_periodo, c1, c2):
    s1 = df_periodo[c1]
    s2 = df_periodo[c2]
    
    if s1.empty or s2.empty:
        return {"sync_tend": np.nan, "var_desfase": np.nan}
        
    s1_suavizada = s1.rolling(30, center=True, min_periods=1).mean().dropna()
    s2_suavizada = s2.rolling(30, center=True, min_periods=1).mean().dropna()

    derivada1 = s1_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
    derivada2 = s2_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
    sync_tend = np.mean(np.sign(derivada1) == np.sign(derivada2)) * 100

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
    
    var_desfase = np.var(np.array(desfases)) if len(desfases) > 0 else np.nan
    
    return {"sync_tend": sync_tend, "var_desfase": var_desfase}


st.title("🗓️ Análisis de Eventos: Impacto del COVID-19")
st.markdown("Analiza cómo cambiaron las relaciones de sincronía durante la pandemia.")

df_datos = cargar_datos()
lista_contaminantes = df_datos.columns.tolist()

st.sidebar.header("Panel de Control")
contaminante1 = st.sidebar.selectbox("Selecciona el Contaminante Maestro:", lista_contaminantes, index=2) # NENO2 por defecto
contaminante2 = st.sidebar.selectbox("Selecciona el Contaminante Esclavo:", lista_contaminantes, index=0) # NEO3 por defecto

periodos = {
    "Pre-Pandemia (Ene-Mar 2020)": ('2020-01-01', '2020-03-31'),
    "Confinamiento (Abr-Jun 2020)": ('2020-04-01', '2020-06-30'),
    "Nueva Normalidad (2021-2022)": ('2021-01-01', '2022-12-31'),
    "Post-Pandemia (2023+)": ('2023-01-01', '2025-12-31')
}

st.header(f"Comparación de Sincronía: {contaminante1} vs {contaminante2}")

resultados_df = pd.DataFrame(columns=["Sincronía de Tendencia (%)", "Varianza de Desfase"])

for nombre, (inicio, fin) in periodos.items():
    df_filtrado = df_datos[(df_datos.index >= inicio) & (df_datos.index <= fin)]
    if not df_filtrado.empty:
        metricas = calcular_metricas_periodo(df_filtrado, contaminante1, contaminante2)
        resultados_df.loc[nombre] = [f"{metricas['sync_tend']:.1f}", f"{metricas['var_desfase']:.2f}"]

st.dataframe(resultados_df)

st.markdown("---")
st.subheader("Visualización de la Serie Completa")
st.line_chart(df_datos[[contaminante1, contaminante2]])
st.caption("Usa el gráfico para observar visualmente los cambios de comportamiento a lo largo del tiempo.")