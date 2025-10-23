import streamlit as st

from utils.ui import (
    aplicar_estilos_generales,
    mostrar_encabezado,
    mostrar_tarjetas_descriptivas,
)

st.set_page_config(
    page_title="Análisis de Sincronía de Fase",
    page_icon="🌀",
    layout="wide"
)

aplicar_estilos_generales()
mostrar_encabezado(
    "Sistema Automatizado de Análisis de Sincronía de Fase",
    "Explora, compara y explica el comportamiento conjunto de los contaminantes"
    " atmosféricos de la Ciudad de México con una experiencia moderna y unificada.",
    "🌀",
)

st.subheader("Bienvenido")
st.write(
    "Esta plataforma interactiva implementa la metodología de **sincronización de fase** para investigar la "
    "interdependencia entre los principales contaminantes medidos en la Ciudad de México durante el periodo 2020-2024."
)
st.write(
    "Fue desarrollada como parte del Trabajo Terminal de **Eric Gael Romo Gutierrez** en la Escuela Superior de "
    "Cómputo (ESCOM) del IPN, con el objetivo de ofrecer un tablero intuitivo para analistas e investigadores ambientales."
)

st.subheader("Explora las herramientas disponibles")
herramientas = [
    {
        "icono": "🔬",
        "titulo": "Análisis comparativo",
        "descripcion": "Visualiza series suavizadas, picos y métricas clave para evaluar sincronía, desfases y correlación.",
        "enlace": "Análisis_comparativo",
        "texto_boton": "Ir al análisis",
    },
    {
        "icono": "🌐",
        "titulo": "Matriz de sincronía",
        "descripcion": "Explora mapas de calor interactivos sobre tendencias compartidas, varianza de desfase y liderazgo temporal.",
        "enlace": "Matriz_de_sincronía",
        "texto_boton": "Ver matriz",
    },
    {
        "icono": "🗓️",
        "titulo": "Eventos e interrupciones",
        "descripcion": "Evalúa episodios puntuales contra referencias históricas, revisa picos emparejados y cuantifica los cambios.",
        "enlace": "Eventos_e_interrupciones",
        "texto_boton": "Analizar eventos",
    },
    {
        "icono": "🔥",
        "titulo": "Episodios críticos",
        "descripcion": "Define umbrales dinámicos, identifica episodios prolongados y analiza la frecuencia mensual de alertas.",
        "enlace": "Episodios_críticos",
        "texto_boton": "Explorar episodios",
    },
    {
        "icono": "🔎",
        "titulo": "Exploración de tendencias",
        "descripcion": "Calcula resúmenes, patrones estacionales y correlaciones para respaldar hallazgos de sincronía.",
        "enlace": "Exploración_de_tendencias",
        "texto_boton": "Examinar tendencias",
    },
]

mostrar_tarjetas_descriptivas(herramientas, columnas=2)
