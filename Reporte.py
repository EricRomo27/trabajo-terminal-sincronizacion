import streamlit as st

st.set_page_config(
    page_title="Análisis de Sincronía de Fase",
    page_icon="🌀",
    layout="wide"
)

st.title("🌀 Sistema Automatizado de Análisis de Sincronía de Fase")

st.markdown("---")

st.header("Bienvenido al sistema de análisis de contaminantes atmosféricos.")
st.subheader("Creado por: Eric Gael Romo Gutierrez")

st.markdown("""
Esta aplicación interactiva implementa la metodología de **sincronización de fase** para investigar la interdependencia entre los principales contaminantes de la Ciudad de México, basándose en los datos históricos del periodo 2020-2024.

**Utiliza el menú de la izquierda para navegar por las diferentes herramientas de análisis:**

* **🔬 Análisis Comparativo:** Compara dos contaminantes de tu elección, visualiza sus series de tiempo y obtén métricas detalladas de sincronización.
* **🌐 Matriz de Sincronía:** Obtén una visión global de cómo interactúan todos los contaminantes entre sí a través de un mapa de calor interactivo.
* **🗓️ Eventos e interrupciones:** Contrasta cualquier periodo de interés contra una referencia para medir la magnitud de los cambios.
* **🔥 Episodios críticos:** Identifica superaciones de umbral, su duración y los momentos de mayor severidad.
* **🔎 Exploración de tendencias:** Resume estadísticas generales, patrones estacionales y correlaciones entre contaminantes.

Este sistema fue desarrollado como parte del Trabajo Terminal para la Escuela Superior de Cómputo (ESCOM) del IPN.
""")
