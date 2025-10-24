import sqlite3
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.ui import (
    aplicar_estilos_generales,
    boton_descarga_altair,
    mostrar_encabezado,
    mostrar_tarjetas_metricas,
    runtime_activo,
)


@st.cache_data
def cargar_datos():
    with sqlite3.connect("contaminantes.db") as conn:
        df = pd.read_sql_query(
            "SELECT * FROM calidad_aire",
            conn,
            parse_dates=["Fecha"],
            index_col="Fecha",
        )
    return df.sort_index()


if runtime_activo():
    st.set_page_config(layout="wide", page_title="Exploración de tendencias")
    aplicar_estilos_generales()

    df_datos = cargar_datos()

    mostrar_encabezado(
        "Exploración de tendencias y patrones",
        "Complementa la sincronía con estadísticas descriptivas, perfiles estacionales y correlaciones"
        " en un solo lugar.",
        "🔎",
    )

    if df_datos.empty:
        st.error("No se encontraron datos en la base de calidad_aire.")
        st.stop()

    lista_contaminantes = df_datos.columns.tolist()

    st.sidebar.header("Opciones de exploración")
    defecto = lista_contaminantes[: min(3, len(lista_contaminantes))]
    seleccionados = st.sidebar.multiselect(
        "Selecciona contaminantes a analizar", lista_contaminantes, default=defecto
    )

    if not seleccionados:
        st.warning("Selecciona al menos un contaminante para continuar.")
        st.stop()

    min_fecha = df_datos.index.min().date()
    max_fecha = df_datos.index.max().date()

    rango = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_fecha, max_fecha),
        min_value=min_fecha,
        max_value=max_fecha,
    )

    if isinstance(rango, (tuple, list)):
        if len(rango) != 2:
            st.warning("Selecciona un rango de fechas válido.")
            st.stop()
        inicio, fin = sorted(rango)
    else:
        inicio = fin = rango

    if inicio > fin:
        inicio, fin = fin, inicio

    filtro = (df_datos.index >= pd.Timestamp(inicio)) & (df_datos.index <= pd.Timestamp(fin))
    df_filtrado = df_datos.loc[filtro, seleccionados]

    if df_filtrado.empty:
        st.warning("No hay datos en el rango seleccionado. Prueba con otro intervalo.")
        st.stop()

    resumen = df_filtrado.agg(["mean", "median", "std", "max", "min"]).T
    resumen = resumen.rename(
        columns={
            "mean": "Media",
            "median": "Mediana",
            "std": "Desviación estándar",
            "max": "Máximo",
            "min": "Mínimo",
        }
    )

    media_periodo = df_filtrado.mean().sort_values(ascending=False)
    desviacion_periodo = df_filtrado.std().sort_values(ascending=False)

    metricas = [
        {
            "icono": "🧮",
            "titulo": "Registros analizados",
            "valor": f"{len(df_filtrado):,}".replace(",", " "),
            "descripcion": "Número de observaciones disponibles en el rango seleccionado.",
        }
    ]

    if not media_periodo.empty:
        metricas.append(
            {
                "icono": "🏆",
                "titulo": "Mayor concentración promedio",
                "valor": f"{media_periodo.index[0]} ({media_periodo.iloc[0]:.2f})",
                "descripcion": "Contaminante con el valor medio más alto en el periodo actual.",
            }
        )

    if not desviacion_periodo.empty:
        metricas.append(
            {
                "icono": "📉",
                "titulo": "Mayor variabilidad",
                "valor": f"{desviacion_periodo.index[0]} ({desviacion_periodo.iloc[0]:.2f})",
                "descripcion": "Serie con mayor dispersión diaria (desviación estándar).",
            }
        )

    metricas.append(
        {
            "icono": "🗓️",
            "titulo": "Periodo analizado",
            "valor": f"{pd.to_datetime(inicio).strftime('%d %b %Y')} – {pd.to_datetime(fin).strftime('%d %b %Y')}",
            "descripcion": "Intervalo temporal aplicado a todos los cálculos y gráficos.",
        }
    )

    mostrar_tarjetas_metricas(metricas)

    pestañas = st.tabs([
        "Resumen estadístico",
        "Evolución temporal",
        "Patrones estacionales",
        "Correlaciones",
    ])

    with pestañas[0]:
        st.dataframe(resumen.round(2), use_container_width=True)
        st.caption("Ordena y filtra la tabla para comparar contaminantes según cada indicador estadístico.")

    with pestañas[1]:
        st.markdown("**Series diarias suavizadas**")
        df_lineas = (
            df_filtrado.reset_index()
            .rename(columns={"Fecha": "fecha"})
            .melt("fecha", var_name="Contaminante", value_name="Valor")
        )
        grafica_evolucion = (
            alt.Chart(df_lineas)
            .mark_line()
            .encode(
                x="fecha:T",
                y=alt.Y("Valor:Q", title="Concentración"),
                color="Contaminante:N",
                tooltip=["fecha:T", "Contaminante:N", alt.Tooltip("Valor:Q", format=".2f")],
            )
            .interactive()
        )
        st.altair_chart(grafica_evolucion, use_container_width=True)
        boton_descarga_altair(
            grafica_evolucion,
            "exploracion_tendencias_series.html",
            etiqueta="📥 Descargar gráfica en HTML",
        )
        st.caption("Observa tendencias generales y coincidencias de picos antes de pasar al análisis de sincronía.")

    nombre_meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    perfil_mensual = df_filtrado.groupby(df_filtrado.index.month).mean()
    perfil_mensual.index = [nombre_meses.get(i, str(i)) for i in perfil_mensual.index]

    promedios_anuales = df_filtrado.resample("Y").mean()
    promedios_anuales.index = promedios_anuales.index.year
    variacion_interanual = promedios_anuales.pct_change().dropna() * 100

    with pestañas[2]:
        st.markdown("**Promedios mensuales y anuales**")
        st.dataframe(perfil_mensual.round(2), use_container_width=True)
        st.caption("Los promedios mensuales ayudan a detectar patrones estacionales recurrentes.")

        st.dataframe(promedios_anuales.round(2), use_container_width=True)
        if not variacion_interanual.empty:
            st.dataframe(variacion_interanual.round(2), use_container_width=True)
            st.caption("Variación interanual (%) respecto al año previo.")

    with pestañas[3]:
        if len(seleccionados) < 2:
            st.info("Selecciona al menos dos contaminantes para calcular correlaciones.")
        else:
            correlacion = df_filtrado.corr()
            st.dataframe(correlacion.round(2), use_container_width=True)
            st.caption(
                "Las correlaciones cercanas a ±1 indican respuesta conjunta frente a los mismos eventos o condiciones."
            )

    st.subheader("Consejos de exploración")
    st.markdown(
        "- Combina este resumen con el análisis comparativo para profundizar en pares concretos de contaminantes.\n"
        "- Revisa la variación interanual para detectar años atípicos que merezcan un análisis de eventos específico.\n"
        "- Guarda tus combinaciones de filtros desde la barra lateral para documentar hallazgos relevantes."
    )
