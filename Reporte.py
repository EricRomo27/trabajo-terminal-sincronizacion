import streamlit as st

from utils.ui import aplicar_estilos_generales, mostrar_encabezado

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

st.markdown(
    """
    <div class="app-section">
        <h3>Bienvenido</h3>
        <p>
            Esta plataforma interactiva implementa la metodología de <strong>sincronización de fase</strong>
            para investigar la interdependencia entre los principales contaminantes medidos en la Ciudad de México
            durante el periodo 2020-2024.
        </p>
        <p>
            Fue desarrollada como parte del Trabajo Terminal de <strong>Eric Gael Romo Gutierrez</strong> en la Escuela
            Superior de Cómputo (ESCOM) del IPN, con el objetivo de ofrecer un tablero intuitivo para analistas e
            investigadores ambientales.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-section">
        <h3>Explora las herramientas disponibles</h3>
        <div class="app-card-grid">
            <div class="app-card">
                <span>🔬 Análisis comparativo</span>
                <h4>Compara dos contaminantes en detalle</h4>
                <p>Visualiza sus series suavizadas, picos y métricas clave para evaluar sincronía, desfases y correlación.</p>
            </div>
            <div class="app-card">
                <span>🌐 Matriz de sincronía</span>
                <h4>Panorama global de interacciones</h4>
                <p>Explora mapas de calor interactivos sobre tendencias compartidas, varianza de desfase y liderazgo temporal.</p>
            </div>
            <div class="app-card">
                <span>🗓️ Eventos e interrupciones</span>
                <h4>Contrasta periodos de interés</h4>
                <p>Evalúa episodios puntuales contra referencias históricas, revisa picos emparejados y cuantifica los cambios.</p>
            </div>
            <div class="app-card">
                <span>🔥 Episodios críticos</span>
                <h4>Detecta superaciones y su intensidad</h4>
                <p>Define umbrales dinámicos, identifica episodios prolongados y analiza la frecuencia mensual de alertas.</p>
            </div>
            <div class="app-card">
                <span>🔎 Exploración de tendencias</span>
                <h4>Obtén contexto estadístico</h4>
                <p>Calcula resúmenes, patrones estacionales y correlaciones para respaldar hallazgos de sincronía.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
