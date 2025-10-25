"""Utilidades ligeras relacionadas con el runtime de Streamlit."""

from __future__ import annotations

import streamlit as st


def runtime_activo() -> bool:
    """Indica si la app se está ejecutando dentro del runtime de Streamlit."""

    try:
        return st.runtime.exists()
    except Exception:  # pragma: no cover - protección ante cambios de API
        return False


__all__ = ["runtime_activo"]
