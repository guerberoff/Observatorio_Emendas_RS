import streamlit as st

def render_indicator_card(
    icon: str,
    title: str,
    value: str,
    help_text: str | None = None
) -> None:
    """Renderiza um cartão usando classes CSS globais."""
    
    # Criamos a estrutura HTML utilizando apenas as classes definidas no style.css
    help_html = f'<div class="oers-card-help">{help_text}</div>' if help_text else ''
    
    card_html = f"""
    <div class="oers-card">
        <div class="oers-card-header">
            <span>{icon}</span> {title}
        </div>
        <div class="oers-card-value">
            {value}
        </div>
        {help_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)