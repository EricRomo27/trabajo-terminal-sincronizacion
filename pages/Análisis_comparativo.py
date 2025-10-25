import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy.signal import find_peaks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.peak_matching_access import resumir_desfases_seguro as resumir_desfases
from utils.ui import (
    aplicar_estilos_generales,
    boton_descarga_plotly,
    mostrar_encabezado,
    mostrar_tarjetas_metricas,
    runtime_activo,
)

if runtime_activo():
    st.set_page_config(layout="wide", page_title="Análisis Comparativo")
    aplicar_estilos_generales()

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
    
    resumen_desfases = resumir_desfases(
        fechas_picos_maestro,
        fechas_picos_esclavo,
        ventana_busqueda=90,
        ventana_confiable=45,
    )
    varianza_desfase = resumen_desfases["varianza"]
    desfase_medio = resumen_desfases["desfase_medio"]

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

    return {
        "sincronia_tendencia": sincronia_tendencia,
        "varianza_desfase": varianza_desfase,
        "desfase_medio": desfase_medio,
        "max_corr": max_corr,
        "mejor_lag": mejor_lag,
        "fig_comparativa": fig_comparativa,
        "fig_fase": fig_fase,
        "pares_picos": resumen_desfases["pares_validos"],
        "pares_descartados": resumen_desfases["pares_descartados"],
        "ventana_confiable": resumen_desfases["ventana_confiable"],
    }

if runtime_activo():
    # --- Construcción de la Interfaz ---
    mostrar_encabezado(
        "Análisis comparativo entre contaminantes",
        "Contrasta dos series para evaluar sincronía de tendencias, desfases entre picos"
        " y comportamiento de fase en un entorno interactivo.",
        "🔬",
    )
    df_datos = cargar_datos()
    lista_contaminantes = df_datos.columns.tolist()

    st.sidebar.header("Panel de Control")
    contaminante_maestro = st.sidebar.selectbox("Contaminante Maestro (Referencia):", lista_contaminantes, index=4)
    contaminante_esclavo = st.sidebar.selectbox("Contaminante Esclavo (Comparación):", lista_contaminantes, index=5)

    if contaminante_maestro and contaminante_esclavo:
        resultados = realizar_analisis_completo(df_datos[contaminante_maestro], df_datos[contaminante_esclavo], df_datos.index)

        # --- Tarjetas de métricas clave ---
        sync_tend = resultados['sincronia_tendencia']
        var_desfase = resultados['varianza_desfase']
        desfase_medio = resultados['desfase_medio']

        metricas = []
        if np.isnan(sync_tend):
            sync_valor = "N/D"
            sync_delta = None
        else:
            sync_valor = f"{sync_tend:.1f}%"
            diferencia = sync_tend - 50
            sync_delta = {
                "texto": f"{diferencia:+.1f} pts vs. azar",
                "tipo": "positive" if diferencia >= 0 else "negative",
            }

        if np.isnan(var_desfase):
            var_valor = "N/D"
        else:
            var_valor = f"{var_desfase:.2f} días²"

        metricas.append(
            {
                "icono": "🎯",
                "titulo": "Sincronía de tendencia",
                "valor": sync_valor,
                "descripcion": "Porcentaje de instantes en los que ambas series comparten la misma dirección de cambio tras el suavizado.",
                "delta": sync_delta,
            }
        )
        metricas.append(
            {
                "icono": "⏱️",
                "titulo": "Varianza del desfase",
                "valor": var_valor,
                "descripcion": "Dispersión de los desfases entre picos emparejados (días²). Valores pequeños indican ocurrencias casi simultáneas.",
                "delta": {"texto": "Ideal: cercana a 0", "tipo": "neutral"},
            }
        )
        metricas.append(
            {
                "icono": "🧭",
                "titulo": "Desfase medio",
                "valor": "N/D" if np.isnan(desfase_medio) else f"{desfase_medio:.1f} días",
                "descripcion": "Promedio del desplazamiento temporal necesario para alinear cada pico maestro con su contraparte.",
                "delta": {"texto": "Referencia: 0 días", "tipo": "neutral"},
            }
        )
        metricas.append(
            {
                "icono": "🔗",
                "titulo": "Correlación máxima",
                "valor": f"{resultados['max_corr']:.2f}",
                "descripcion": "Coeficiente de correlación más alto al desplazar la serie esclavo dentro de ±90 días.",
                "delta": {"texto": f"Lag óptimo: {resultados['mejor_lag']} días", "tipo": "neutral"},
            }
        )

        mostrar_tarjetas_metricas(metricas)

        if resultados["pares_descartados"]:
            st.caption(
                "Se descartaron {0} coincidencias por superar ±{1} días de diferencia."
                .format(
                    len(resultados["pares_descartados"]),
                    resultados["ventana_confiable"],
                )
            )

        if not np.isnan(sync_tend) and not np.isnan(var_desfase):
            if sync_tend > 80 and var_desfase < 20:
                st.success(
                    f"**Conclusión:** Los indicadores apuntan a una sincronización **fuerte** entre"
                    f" {contaminante_maestro} y {contaminante_esclavo}."
                )
            elif sync_tend < 55 and var_desfase > 80:
                st.info(
                    "Los contaminantes muestran respuestas poco sincronizadas; considera acotar el periodo"
                    " o revisar eventos que hayan provocado desfases notorios."
                )

        st.subheader("Visualizaciones clave")

        pestañas = st.tabs(["Series y picos", "Dinámica de fase"])
        with pestañas[0]:
            st.plotly_chart(resultados['fig_comparativa'], use_container_width=True)
            boton_descarga_plotly(
                resultados['fig_comparativa'],
                f"analisis_{contaminante_maestro}_vs_{contaminante_esclavo}.png",
                etiqueta="📥 Descargar gráfica comparativa",
            )

        with pestañas[1]:
            st.plotly_chart(resultados['fig_fase'], use_container_width=True)
            st.caption(
                "La diagonal punteada indica sincronía ideal (relación 1:1). Alejamientos sostenidos sugieren"
                " cambios en liderazgo o frecuencia de picos."
            )
            boton_descarga_plotly(
                resultados['fig_fase'],
                f"dinamica_fase_{contaminante_maestro}_vs_{contaminante_esclavo}.png",
                etiqueta="📥 Descargar gráfica de fase",
            )

        st.subheader("Cómo interpretar estos resultados")
        st.markdown(
            "- **Sincronía alta + varianza baja**: respuestas casi simultáneas ante los mismos eventos.\n"
            "- **Varianza elevada**: revisa los picos emparejados para detectar desfases puntuales que estén inflando la métrica.\n"
            "- **Correlación alta**: confirma patrones globales similares incluso si los picos ocurren con cierto desfase."
        )
