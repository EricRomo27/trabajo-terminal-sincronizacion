from __future__ import annotations

from dataclasses import dataclass
from typing import List

import altair as alt
import pandas as pd
import sqlite3
import streamlit as st

from utils.ui import (
    aplicar_estilos_generales,
    boton_descarga_altair,
    mostrar_encabezado,
    mostrar_tarjetas_metricas,
)


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    with sqlite3.connect("contaminantes.db") as conn:
        df = pd.read_sql_query(
            "SELECT * FROM calidad_aire", conn, parse_dates=["Fecha"], index_col="Fecha"
        )
    return df.sort_index()


@dataclass
class Episodio:
    inicio: pd.Timestamp
    fin: pd.Timestamp
    duracion: int
    maximo: float
    promedio: float
    exceso_acumulado: float


def detectar_episodios(serie: pd.Series, umbral: float) -> List[Episodio]:
    serie = serie.dropna()
    if serie.empty:
        return []

    episodios: List[Episodio] = []
    en_evento = False
    inicio_actual: pd.Timestamp | None = None

    for fecha, valor in serie.items():
        if valor > umbral:
            if not en_evento:
                en_evento = True
                inicio_actual = fecha
        elif en_evento:
            fin_actual = fecha - pd.Timedelta(days=1)
            ventana = serie.loc[inicio_actual:fin_actual]
            episodios.append(
                Episodio(
                    inicio=inicio_actual,
                    fin=fin_actual,
                    duracion=(fin_actual - inicio_actual).days + 1,
                    maximo=float(ventana.max()),
                    promedio=float(ventana.mean()),
                    exceso_acumulado=float((ventana - umbral).clip(lower=0).sum()),
                )
            )
            en_evento = False
            inicio_actual = None

    if en_evento and inicio_actual is not None:
        fin_actual = serie.index.max()
        ventana = serie.loc[inicio_actual:fin_actual]
        episodios.append(
            Episodio(
                inicio=inicio_actual,
                fin=fin_actual,
                duracion=(fin_actual - inicio_actual).days + 1,
                maximo=float(ventana.max()),
                promedio=float(ventana.mean()),
                exceso_acumulado=float((ventana - umbral).clip(lower=0).sum()),
            )
        )

    return episodios


def filtrar_episodios(episodios: List[Episodio], min_dias: int) -> List[Episodio]:
    if min_dias <= 1:
        return episodios
    return [ep for ep in episodios if ep.duracion >= min_dias]


st.set_page_config(layout="wide", page_title="Episodios críticos")
aplicar_estilos_generales()
mostrar_encabezado(
    "Episodios críticos y superaciones de umbral",
    "Ajusta umbrales dinámicos para identificar periodos prolongados de concentración elevada"
    " y analizar su severidad.",
    "🚨",
)

df_datos = cargar_datos()

if df_datos.empty:
    st.error("No hay datos cargados en la base. Verifica la conexión a la base de contaminantes.")
    st.stop()

st.sidebar.header("Parámetros del análisis")
contaminante = st.sidebar.selectbox("Contaminante", df_datos.columns.tolist())

serie_objetivo = df_datos[contaminante].dropna()
if serie_objetivo.empty:
    st.warning("El contaminante seleccionado no tiene datos disponibles.")
    st.stop()

metodo_umbral = st.sidebar.radio("Método para definir el umbral", ["Percentil histórico", "Valor manual"])

if metodo_umbral == "Percentil histórico":
    percentil = st.sidebar.slider("Percentil", min_value=80, max_value=99, value=95)
    umbral = float(serie_objetivo.quantile(percentil / 100))
else:
    umbral = st.sidebar.number_input(
        "Valor de umbral", value=float(serie_objetivo.quantile(0.9)), min_value=0.0, step=1.0
    )

min_dias = st.sidebar.slider("Duración mínima del episodio (días)", min_value=1, max_value=14, value=2)

episodios = filtrar_episodios(detectar_episodios(serie_objetivo, umbral), min_dias)

superaciones_diarias = (serie_objetivo > umbral).astype(int)
conteo_mensual = superaciones_diarias.groupby(pd.Grouper(freq="M")).sum()
conteo_mensual.index = conteo_mensual.index.strftime("%Y-%m")

metricas = [
    {
        "icono": "📍",
        "titulo": "Episodios detectados",
        "valor": len(episodios),
        "descripcion": "Cantidad de periodos consecutivos que superan el umbral seleccionado.",
    },
    {
        "icono": "⏳",
        "titulo": "Mayor duración",
        "valor": 0 if not episodios else f"{max(ep.duracion for ep in episodios)} días",
        "descripcion": "Duración del episodio más prolongado encontrado en el intervalo analizado.",
    },
    {
        "icono": "🔥",
        "titulo": "Exceso acumulado",
        "valor": f"{sum(ep.exceso_acumulado for ep in episodios):.1f}",
        "descripcion": "Suma del excedente por encima del umbral durante todos los episodios detectados.",
        "delta": {"texto": "Valores altos implican eventos más severos", "tipo": "neutral"},
    },
]

mostrar_tarjetas_metricas(metricas)


def _episodios_a_dataframe(episodios: List[Episodio]) -> pd.DataFrame:
    if not episodios:
        return pd.DataFrame(
            columns=["Inicio", "Fin", "Duración (días)", "Máximo", "Promedio", "Exceso acumulado"]
        )
    return pd.DataFrame(
        [
            {
                "Inicio": ep.inicio.date(),
                "Fin": ep.fin.date(),
                "Duración (días)": ep.duracion,
                "Máximo": ep.maximo,
                "Promedio": ep.promedio,
                "Exceso acumulado": ep.exceso_acumulado,
            }
            for ep in episodios
        ]
    )


contenedores = st.tabs([
    "Episodios identificados",
    "Evolución temporal",
    "Intensidad mensual",
])

with contenedores[0]:
    st.dataframe(_episodios_a_dataframe(episodios), use_container_width=True)
    st.caption(
        "Los periodos listados conservan únicamente los días consecutivos que exceden el umbral"
        " configurado en la barra lateral."
    )

with contenedores[1]:
    st.markdown("**Serie diaria con umbral aplicado**")
    df_grafica = serie_objetivo.reset_index().rename(columns={"Fecha": "fecha", contaminante: "valor"})
    lineas = (
        alt.Chart(df_grafica)
        .mark_line(color="#1f77b4")
        .encode(x="fecha:T", y=alt.Y("valor:Q", title="Concentración"))
    )

    umbral_chart = (
        alt.Chart(pd.DataFrame({"fecha": df_grafica["fecha"], "umbral": umbral}))
        .mark_line(color="red", strokeDash=[6, 3])
        .encode(x="fecha:T", y="umbral:Q")
    )

    grafica_series = lineas + umbral_chart
    st.altair_chart(grafica_series, use_container_width=True)
    st.caption("La línea punteada resalta el umbral que define las superaciones críticas.")
    boton_descarga_altair(
        grafica_series,
        f"episodios_{contaminante}_serie.html",
        etiqueta="📥 Descargar gráfica en HTML",
    )

with contenedores[2]:
    heatmap_df = conteo_mensual.reset_index()
    heatmap_df.columns = ["Mes", "Días por encima del umbral"]

    heatmap = (
        alt.Chart(heatmap_df)
        .mark_bar()
        .encode(
            x="Mes:O",
            y=alt.Y("Días por encima del umbral:Q", title="Días"),
            tooltip=["Mes", "Días por encima del umbral"],
            color=alt.Color(
                "Días por encima del umbral:Q",
                scale=alt.Scale(scheme="oranges"),
            ),
        )
    )

    st.altair_chart(heatmap, use_container_width=True)
    st.caption(
        "Identifica temporadas con mayor recurrencia de episodios críticos al observar la concentración de barras."
    )
    boton_descarga_altair(
        heatmap,
        f"episodios_{contaminante}_heatmap.html",
        etiqueta="📥 Descargar gráfica en HTML",
    )

st.subheader("¿Cómo aprovechar esta vista?")
st.markdown(
    "- Ajusta el percentil o valor manual para alinear el umbral con tus criterios de alerta.\n"
    "- Prioriza los episodios más extensos o con mayor exceso acumulado para focalizar acciones.\n"
    "- Utiliza la intensidad mensual para detectar temporadas donde conviene reforzar monitoreos."
)
