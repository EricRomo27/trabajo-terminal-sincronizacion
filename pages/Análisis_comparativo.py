import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import find_peaks
import io

from utils.peak_matching import calcular_desfases_entre_picos

if st.runtime.exists():
    st.set_page_config(layout="wide", page_title="Análisis Comparativo")

@st.cache_data
def cargar_datos():
    with sqlite3.connect('contaminantes.db') as conn:
        df = pd.read_sql_query("SELECT * FROM calidad_aire", conn, parse_dates=['Fecha'], index_col='Fecha')
    return df

def realizar_analisis_completo(serie_maestro, serie_esclavo, df_index):
    # (Cálculos de suavizado, picos, varianza, etc. no cambian)
    s_maestro_suavizada = serie_maestro.rolling(30, center=True, min_periods=1).mean()
    s_esclavo_suavizada = serie_esclavo.rolling(30, center=True, min_periods=1).mean()

    picos_maestro, _ = find_peaks(s_maestro_suavizada, distance=30, height=s_maestro_suavizada.mean())
    picos_esclavo, _ = find_peaks(s_esclavo_suavizada, distance=30, height=s_esclavo_suavizada.mean())
    
    fechas_picos_maestro = s_maestro_suavizada.index[picos_maestro]
    fechas_picos_esclavo = s_esclavo_suavizada.index[picos_esclavo]
    
    desfases = calcular_desfases_entre_picos(
        fechas_picos_maestro,
        fechas_picos_esclavo,
        ventana_maxima_dias=90,
    )
    desfases_np = np.array(desfases, dtype=float)
    varianza_desfase = np.var(desfases_np) if len(desfases) > 0 else np.nan
    desfase_medio = np.mean(desfases_np) if len(desfases) > 0 else np.nan

    derivada_maestro = s_maestro_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
    derivada_esclavo = s_esclavo_suavizada.rolling(15, center=True).mean().pct_change(fill_method=None)
    mascara_validos = (~derivada_maestro.isna()) & (~derivada_esclavo.isna())
    if mascara_validos.any():
        sincronia_tendencia = (
            np.mean(
                np.sign(derivada_maestro[mascara_validos]) == np.sign(derivada_esclavo[mascara_validos])
            )
            * 100
        )
    else:
        sincronia_tendencia = np.nan
    
    max_corr, mejor_lag = -1, 0
    for lag in range(-90, 91):
        corr = serie_maestro.corr(serie_esclavo.shift(lag))
        if corr > max_corr: max_corr, mejor_lag = corr, lag

    # --- NUEVO: Cálculo de Ciclos Acumulados ---
    ciclos_maestro_acum = pd.Series(np.arange(1, len(fechas_picos_maestro) + 1), index=fechas_picos_maestro)
    ciclos_esclavo_acum = pd.Series(np.arange(1, len(fechas_picos_esclavo) + 1), index=fechas_picos_esclavo)
    
    # Rellenar para tener una serie continua en el tiempo
    ciclos_maestro_continuo = ciclos_maestro_acum.reindex(df_index, method='ffill').fillna(0)
    ciclos_esclavo_continuo = ciclos_esclavo_acum.reindex(df_index, method='ffill').fillna(0)

    # --- Creación de Gráficas ---
    # (Se mantiene la figura anterior y se crea una nueva para el análisis de fase)
    fig_comparativa = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Método 1: Detección de Picos", "Método 2: Derivadas (Tendencia)"))
    fig_comparativa.add_trace(go.Scatter(x=s_maestro_suavizada.index, y=s_maestro_suavizada, name=serie_maestro.name, line=dict(color='dodgerblue')), row=1, col=1)
    fig_comparativa.add_trace(go.Scatter(x=s_esclavo_suavizada.index, y=s_esclavo_suavizada, name=serie_esclavo.name, line=dict(color='darkorange')), row=1, col=1)
    fig_comparativa.add_trace(go.Scatter(x=fechas_picos_maestro, y=s_maestro_suavizada[fechas_picos_maestro], mode='markers', name=f'Picos {serie_maestro.name}', marker=dict(color='red', symbol='x', size=8)), row=1, col=1)
    fig_comparativa.add_trace(go.Scatter(x=fechas_picos_esclavo, y=s_esclavo_suavizada[fechas_picos_esclavo], mode='markers', name=f'Picos {serie_esclavo.name}', marker=dict(color='purple', symbol='circle-open', size=8)), row=1, col=1)
    fig_comparativa.add_trace(go.Scatter(x=derivada_maestro.index, y=derivada_maestro, name=f'Tendencia {serie_maestro.name}', line=dict(color='dodgerblue'), opacity=0.7), row=2, col=1)
    fig_comparativa.add_trace(go.Scatter(x=derivada_esclavo.index, y=derivada_esclavo, name=f'Tendencia {serie_esclavo.name}', line=dict(color='darkorange'), opacity=0.7), row=2, col=1)
    fig_comparativa.update_layout(height=700, title_text=f'Análisis Comparativo: {serie_maestro.name} vs {serie_esclavo.name}', legend_traceorder="grouped")

    # --- NUEVO: Creación de Gráfica de Fase ---
    fig_fase = make_subplots(rows=1, cols=2, subplot_titles=("Ciclos Acumulados vs. Tiempo", f"Fase Esclavo vs. Fase Maestro"))
    fig_fase.add_trace(go.Scatter(x=ciclos_maestro_continuo.index, y=ciclos_maestro_continuo, name=f'Ciclos {serie_maestro.name}', line=dict(color='dodgerblue')), row=1, col=1)
    fig_fase.add_trace(go.Scatter(x=ciclos_esclavo_continuo.index, y=ciclos_esclavo_continuo, name=f'Ciclos {serie_esclavo.name}', line=dict(color='darkorange')), row=1, col=1)
    
    # Para la gráfica de fase vs fase, necesitamos alinear los conteos.
    df_fases = pd.DataFrame({'maestro': ciclos_maestro_continuo, 'esclavo': ciclos_esclavo_continuo}).dropna()
    fig_fase.add_trace(go.Scatter(x=df_fases['maestro'], y=df_fases['esclavo'], mode='lines', name='Relación de Fase', line=dict(color='green')), row=1, col=2)
    # Línea de sincronía perfecta para referencia
    fig_fase.add_trace(go.Scatter(x=[0, df_fases['maestro'].max()], y=[0, df_fases['maestro'].max()], mode='lines', name='Sincronía 1:1', line=dict(color='black', dash='dash')), row=1, col=2)
    fig_fase.update_xaxes(title_text="Ciclos Acumulados (Maestro)", row=1, col=2)
    fig_fase.update_yaxes(title_text="Ciclos Acumulados (Esclavo)", row=1, col=2)
    fig_fase.update_layout(height=500, title_text="Análisis de Dinámica de Fase")

    return {"sincronia_tendencia": sincronia_tendencia, "varianza_desfase": varianza_desfase, "desfase_medio": desfase_medio, "max_corr": max_corr, "mejor_lag": mejor_lag, "fig_comparativa": fig_comparativa, "fig_fase": fig_fase}

if st.runtime.exists():
    # --- Construcción de la Interfaz ---
    st.title("🔬 Análisis Comparativo entre Contaminantes")
    df_datos = cargar_datos()
    lista_contaminantes = df_datos.columns.tolist()

    st.sidebar.header("Panel de Control")
    contaminante_maestro = st.sidebar.selectbox("Contaminante Maestro (Referencia):", lista_contaminantes, index=4)
    contaminante_esclavo = st.sidebar.selectbox("Contaminante Esclavo (Comparación):", lista_contaminantes, index=5)

    if contaminante_maestro and contaminante_esclavo:
        resultados = realizar_analisis_completo(df_datos[contaminante_maestro], df_datos[contaminante_esclavo], df_datos.index)

        st.markdown("---")
        st.header("Resultados Cuantitativos")
        col1, col2, col3, col4 = st.columns(4)
        # (Métricas sin cambios...)
        sync_tend = resultados['sincronia_tendencia']
        var_desfase = resultados['varianza_desfase']
        desfase_medio = resultados['desfase_medio']

        sync_display = "N/D" if np.isnan(sync_tend) else f"{sync_tend:.1f}%"
        sync_delta = None if np.isnan(sync_tend) else f"{sync_tend - 50:.1f}%"
        col1.metric(
            "Sincronía de Tendencia",
            sync_display,
            delta=sync_delta,
            help="Porcentaje de instantes en los que las tendencias (derivadas suavizadas) de ambas series apuntan en la misma dirección.",
        )

        var_display = "N/D" if np.isnan(var_desfase) else f"{var_desfase:.2f}"
        var_delta = None if np.isnan(var_desfase) else f"{-var_desfase:.2f}"
        col2.metric(
            "Varianza de Desfase",
            var_display,
            delta=var_delta,
            delta_color="inverse",
            help="Dispersión (en días²) de los desfases calculados entre picos emparejados; valores altos implican picos que no ocurren sincronizados.",
        )

        desfase_display = "N/D" if np.isnan(desfase_medio) else f"{desfase_medio:.1f} días"
        col3.metric(
            "Desfase Medio",
            desfase_display,
            help="Promedio (en días) de los desfases entre cada pico maestro y su pico esclavo más cercano dentro de la ventana analizada.",
        )
        col4.metric(
            "Correlación Máxima",
            f"{resultados['max_corr']:.2f}",
            help="Mayor coeficiente de correlación de Pearson entre las series al desplazar la serie esclavo dentro de ±90 días; indica el alineamiento global de ambas curvas.",
        )

        if sync_tend > 80 and var_desfase < 20:
            st.success(f"**Conclusión:** Se observa una **SINCRONIZACIÓN FUERTE** entre {contaminante_maestro} y {contaminante_esclavo}.")
        # (Interpretación sin cambios...)

        st.markdown("---")
        st.header("Análisis Gráfico Interactivo")
        st.plotly_chart(resultados['fig_comparativa'], use_container_width=True)

        # --- NUEVA SECCIÓN DE GRÁFICAS DE FASE ---
        st.markdown("---")
        st.header("Análisis de Dinámica de Fase (Ciclos Acumulados)")
        st.plotly_chart(resultados['fig_fase'], use_container_width=True)

        # (Botón de descarga sin cambios...)
        buffer = io.BytesIO()
        resultados['fig_comparativa'].write_image(file=buffer, format="png")
        st.download_button(label="📥 Descargar Gráfica Comparativa", data=buffer, file_name=f"analisis_{contaminante_maestro}_vs_{contaminante_esclavo}.png", mime="image/png")
