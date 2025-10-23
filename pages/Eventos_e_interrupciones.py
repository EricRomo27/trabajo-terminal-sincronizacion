from datetime import date
from typing import Dict, Tuple

import altair as alt
import numpy as np
import pandas as pd
import sqlite3
import streamlit as st
from scipy.signal import find_peaks

from utils.peak_matching import calcular_desfases_entre_picos

st.set_page_config(layout="wide", page_title="Eventos e interrupciones")


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    with sqlite3.connect("contaminantes.db") as conn:
        df = pd.read_sql_query(
            "SELECT * FROM calidad_aire", conn, parse_dates=["Fecha"], index_col="Fecha"
        )
    return df.sort_index()


def _normalizar_intervalo(inicio: pd.Timestamp, fin: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    if inicio > fin:
        inicio, fin = fin, inicio
    return inicio.normalize(), fin.normalize()


def _calcular_metricas_sincronia(df_periodo: pd.DataFrame, c1: str, c2: str) -> Dict[str, float]:
    if df_periodo.empty:
        return {"sync_tend": np.nan, "var_desfase": np.nan}

    s1 = df_periodo[c1].rolling(30, center=True, min_periods=1).mean().dropna()
    s2 = df_periodo[c2].rolling(30, center=True, min_periods=1).mean().dropna()

    if s1.empty or s2.empty:
        return {"sync_tend": np.nan, "var_desfase": np.nan}

    derivada1 = s1.rolling(15, center=True).mean().pct_change(fill_method=None)
    derivada2 = s2.rolling(15, center=True).mean().pct_change(fill_method=None)
    mascara_validos = (~derivada1.isna()) & (~derivada2.isna())
    if mascara_validos.any():
        sync_tend = (
            np.mean(
                np.sign(derivada1[mascara_validos]) == np.sign(derivada2[mascara_validos])
            )
            * 100
        )
    else:
        sync_tend = np.nan

    picos1, _ = find_peaks(s1, distance=30, height=s1.mean())
    picos2, _ = find_peaks(s2, distance=30, height=s2.mean())
    desfases = calcular_desfases_entre_picos(s1.index[picos1], s2.index[picos2])
    var_desfase = float(np.var(desfases)) if desfases else np.nan

    return {"sync_tend": float(sync_tend), "var_desfase": var_desfase}


def _resumen_periodo(df_periodo: pd.DataFrame, contaminante: str) -> Dict[str, float]:
    serie = df_periodo[contaminante]
    if serie.empty:
        return {"media": np.nan, "mediana": np.nan, "maximo": np.nan}
    return {
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "maximo": float(serie.max()),
    }


def _periodo_referencia(
    df: pd.DataFrame, inicio_evento: pd.Timestamp, fin_evento: pd.Timestamp, modo: str
) -> pd.DataFrame:
    duracion = (fin_evento - inicio_evento).days + 1

    if modo == "Periodo anterior":
        fin_ref = inicio_evento - pd.Timedelta(days=1)
        inicio_ref = fin_ref - pd.Timedelta(days=duracion - 1)
    elif modo == "Periodo posterior":
        inicio_ref = fin_evento + pd.Timedelta(days=1)
        fin_ref = inicio_ref + pd.Timedelta(days=duracion - 1)
    else:  # "Mismo periodo año previo"
        inicio_ref = inicio_evento - pd.DateOffset(years=1)
        fin_ref = fin_evento - pd.DateOffset(years=1)

    return df.loc[inicio_ref:fin_ref]


df_datos = cargar_datos()
lista_contaminantes = df_datos.columns.tolist()
min_fecha = df_datos.index.min().date() if not df_datos.empty else date.today()
max_fecha = df_datos.index.max().date() if not df_datos.empty else date.today()

if not df_datos.empty:
    default_inicio = max(
        min_fecha,
        (pd.Timestamp(max_fecha) - pd.Timedelta(days=90)).date(),
    )
    default_intervalo = (default_inicio, max_fecha)
else:
    default_intervalo = (max_fecha, max_fecha)

st.title("🗓️ Analizador de eventos e interrupciones")
st.markdown(
    "Explora cualquier episodio relevante —como confinamientos, contingencias ambientales o cambios"
    " operativos— y compara sus métricas con un periodo de referencia configurable."
)

st.sidebar.header("Panel de control")
contaminante_maestro = st.sidebar.selectbox(
    "Contaminante maestro", lista_contaminantes, index=min(2, len(lista_contaminantes) - 1)
)
contaminante_esclavo = st.sidebar.selectbox(
    "Contaminante de contraste", lista_contaminantes, index=0
)

intervalo_evento = st.sidebar.date_input(
    "Intervalo del evento",
    value=default_intervalo,
    min_value=min_fecha,
    max_value=max_fecha,
)

if isinstance(intervalo_evento, tuple) and len(intervalo_evento) == 2:
    inicio_evento, fin_evento = _normalizar_intervalo(
        pd.to_datetime(intervalo_evento[0]), pd.to_datetime(intervalo_evento[1])
    )
else:
    inicio_evento = pd.to_datetime(intervalo_evento)
    fin_evento = inicio_evento

nombre_evento = f"Evento ({inicio_evento.date()} – {fin_evento.date()})"

modo_referencia = st.sidebar.selectbox(
    "Comparar contra", ["Periodo anterior", "Mismo periodo año previo", "Periodo posterior"]
)

if inicio_evento < df_datos.index.min() or fin_evento > df_datos.index.max():
    st.warning(
        "El intervalo seleccionado cae parcialmente fuera del rango de datos disponible."
    )

df_evento = df_datos.loc[inicio_evento:fin_evento]
df_referencia = _periodo_referencia(df_datos, inicio_evento, fin_evento, modo_referencia)

if df_evento.empty:
    st.error("No hay datos en el intervalo seleccionado. Ajusta las fechas para continuar.")
    st.stop()

metricas_evento = _calcular_metricas_sincronia(df_evento, contaminante_maestro, contaminante_esclavo)
metricas_referencia = _calcular_metricas_sincronia(
    df_referencia, contaminante_maestro, contaminante_esclavo
)

resumen_evento_maestro = _resumen_periodo(df_evento, contaminante_maestro)
resumen_ref_maestro = _resumen_periodo(df_referencia, contaminante_maestro)
resumen_evento_esclavo = _resumen_periodo(df_evento, contaminante_esclavo)
resumen_ref_esclavo = _resumen_periodo(df_referencia, contaminante_esclavo)

col1, col2, col3 = st.columns(3)
col1.metric(
    "Sincronía de tendencia durante el evento",
    value="N/D" if np.isnan(metricas_evento["sync_tend"]) else f"{metricas_evento['sync_tend']:.1f}%",
    delta=None if np.isnan(metricas_referencia["sync_tend"]) else f"Ref: {metricas_referencia['sync_tend']:.1f}%",
)
col2.metric(
    "Varianza del desfase (días²)",
    value="N/D" if np.isnan(metricas_evento["var_desfase"]) else f"{metricas_evento['var_desfase']:.1f}",
    delta=None
    if np.isnan(metricas_referencia["var_desfase"])
    else f"Ref: {metricas_referencia['var_desfase']:.1f}",
)

def _delta_metric(valor_evento: float, valor_ref: float) -> str:
    if np.isnan(valor_evento) or np.isnan(valor_ref) or valor_ref == 0:
        return ""
    return f"{((valor_evento - valor_ref) / valor_ref) * 100:.1f}% vs ref"

col3.metric(
    f"Media de {contaminante_maestro} en el evento",
    value="N/D" if np.isnan(resumen_evento_maestro["media"]) else f"{resumen_evento_maestro['media']:.2f}",
    delta=_delta_metric(resumen_evento_maestro["media"], resumen_ref_maestro["media"]),
)

st.markdown("### Distribución comparada del evento y su referencia")

def _tabla_resumen(nombre: str, resumen_maestro: Dict[str, float], resumen_esclavo: Dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Indicador": ["Media", "Mediana", "Máximo"],
            f"{contaminante_maestro} ({nombre})": [
                resumen_maestro["media"],
                resumen_maestro["mediana"],
                resumen_maestro["maximo"],
            ],
            f"{contaminante_esclavo} ({nombre})": [
                resumen_esclavo["media"],
                resumen_esclavo["mediana"],
                resumen_esclavo["maximo"],
            ],
        }
    )


tabla_evento = _tabla_resumen("Evento", resumen_evento_maestro, resumen_evento_esclavo)
tabla_ref = _tabla_resumen("Referencia", resumen_ref_maestro, resumen_ref_esclavo)
st.dataframe(pd.concat([tabla_evento, tabla_ref], ignore_index=True))


st.markdown("### Evolución temporal")
df_grafica = df_datos[[contaminante_maestro, contaminante_esclavo]].reset_index().rename(columns={"Fecha": "fecha"})
df_grafica = df_grafica.melt("fecha", var_name="Contaminante", value_name="Valor")

evento_df = pd.DataFrame({"inicio": [inicio_evento], "fin": [fin_evento], "Tipo": [nombre_evento]})
referencia_df = pd.DataFrame(
    {
        "inicio": [df_referencia.index.min()],
        "fin": [df_referencia.index.max()],
        "Tipo": [f"Referencia ({modo_referencia.lower()})"],
    }
)

lineas = (
    alt.Chart(df_grafica)
    .mark_line()
    .encode(
        x="fecha:T",
        y=alt.Y("Valor:Q", title="Concentración"),
        color="Contaminante:N",
        tooltip=["fecha:T", "Contaminante:N", alt.Tooltip("Valor:Q", format=".2f")],
    )
)

bandas_evento = alt.Chart(evento_df).mark_rect(opacity=0.2, color="#ff7f0e").encode(x="inicio:T", x2="fin:T")
bandas_ref = alt.Chart(referencia_df).mark_rect(opacity=0.12, color="#1f77b4").encode(x="inicio:T", x2="fin:T")

st.altair_chart(bandas_ref + bandas_evento + lineas, use_container_width=True)


st.markdown("### Interpretación rápida")
bullet_points = [
    "Usa la sincronía de tendencia para verificar si ambos contaminantes reaccionaron en la misma dirección durante el evento.",
    "Observa la varianza del desfase para identificar si hubo cambios en el momento en que ocurren los picos.",
    "Contrasta la media del evento contra la referencia para dimensionar la magnitud del impacto.",
]
st.write("\n".join(f"- {item}" for item in bullet_points))

if df_referencia.empty:
    st.info(
        "No se encontraron datos para el periodo de referencia seleccionado. Prueba con otra opción para contextualizar los resultados."
    )
