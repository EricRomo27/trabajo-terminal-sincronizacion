import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="Exploración de tendencias")


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


df_datos = cargar_datos()

st.title("🔎 Exploración de tendencias y patrones")
st.markdown(
    "Esta vista resume el comportamiento general de los contaminantes disponibles y complementa "
    "el análisis específico del periodo de COVID-19. Ajusta el rango temporal y los contaminantes "
    "para descubrir tendencias, cambios estacionales y relaciones entre variables."
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

if isinstance(rango, tuple) or isinstance(rango, list):
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

st.subheader("Resumen estadístico del periodo seleccionado")
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
st.dataframe(resumen.round(2), use_container_width=True)

col1, col2 = st.columns(2)
media_periodo = df_filtrado.mean().sort_values(ascending=False)
desviacion_periodo = df_filtrado.std().sort_values(ascending=False)

if not media_periodo.empty:
    contaminante_top = media_periodo.index[0]
    col1.metric(
        "Mayor concentración promedio",
        contaminante_top,
        f"{media_periodo.iloc[0]:.2f}",
    )

if not desviacion_periodo.empty:
    contaminante_variable = desviacion_periodo.index[0]
    col2.metric(
        "Mayor variabilidad",
        contaminante_variable,
        f"{desviacion_periodo.iloc[0]:.2f}",
    )

st.subheader("Evolución diaria")
st.line_chart(df_filtrado, use_container_width=True)

st.subheader("Comportamiento estacional promedio")
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
st.dataframe(perfil_mensual.round(2), use_container_width=True)

st.subheader("Promedios por año")
promedios_anuales = df_filtrado.resample("Y").mean()
promedios_anuales.index = promedios_anuales.index.year
st.dataframe(promedios_anuales.round(2), use_container_width=True)

variacion_interanual = promedios_anuales.pct_change().dropna() * 100
if not variacion_interanual.empty:
    st.caption("Variación interanual (%) respecto al año previo")
    st.dataframe(variacion_interanual.round(2), use_container_width=True)

if len(seleccionados) >= 2:
    st.subheader("Correlación entre contaminantes")
    correlacion = df_filtrado.corr()
    st.dataframe(correlacion.round(2), use_container_width=True)
    st.caption(
        "Utiliza la correlación para identificar contaminantes que responden de forma similar ante los mismos eventos."
    )

st.caption(
    "Consejo: guarda combinaciones de contaminantes y rangos de fechas desde la barra lateral para documentar hallazgos relevantes."
)

