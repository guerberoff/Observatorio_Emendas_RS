def get_theme_colors() -> dict:
    """Retorna a paleta de cores oficial do Observatório."""
    return {
        "fundo_principal": "#0e1117",
        "fundo_cartao": "#262730",
        "texto_principal": "#ffffff",
        "texto_secundario": "#b0b0b0",
        "borda": "#464e5f",
        "emendas_vermelho": "#d62728",
        "votos_azul": "#1f77b4",
        "cinza_institucional": "#888888",
        "ips_alta": "#d62728",
        "ips_media": "#bcbd22",
        "ips_baixa": "#2ca02c"
    }

def get_typography() -> dict:
    """Retorna as configurações de tamanho de fonte."""
    return {
        "titulo_principal": "2.5rem",
        "subtitulo": "1.2rem",
        "titulo_secao": "1.5rem",
        "valor_cartao": "1.8rem",
        "texto_auxiliar": "0.85rem"
    }

def get_spacing() -> dict:
    """Retorna as definições de espaçamento (padding/margin)."""
    return {
        "pequeno": "5px",
        "medio": "10px",
        "grande": "20px",
        "extra_grande": "30px"
    }

def get_card_style_config() -> dict:
    """Retorna a configuração básica de estilo para cartões."""
    colors = get_theme_colors()
    return {
        "border_radius": "12px",
        "border": f"1px solid {colors['borda']}",
        "shadow": "2px 2px 10px rgba(0,0,0,0.3)"
    }