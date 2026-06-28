import streamlit as st
from pathlib import Path

def load_css(css_path: str | Path = "assets/style.css") -> None:
    """Lê um arquivo CSS e aplica ao Streamlit."""
    path = Path(css_path)
    
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Arquivo de estilo não encontrado em: {css_path}")