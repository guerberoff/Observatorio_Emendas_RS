def get_project_colors() -> dict:
    """Retorna as cores principais definidas para o projeto."""
    return {
        "vermelho_emendas": "#d62728",
        "azul_votos": "#1f77b4",
        "baixa_prioridade": "#2ca02c",
        "media_prioridade": "#bcbd22",
        "alta_prioridade": "#d62728",
        "fundo_dark": "#1e1e1e",
        "texto_light": "#ffffff"
    }

def get_map_layout_config() -> dict:
    """Retorna as configurações padrão para o layout do mapa."""
    return {
        "center": {"lat": -30.0, "lon": -53.0},
        "zoom": 5.5,
        "opacity": 0.7,
        "mapbox_style": "carto-positron"
    }

def get_ips_color_map() -> dict:
    """Retorna o mapeamento de cores para as faixas de prioridade IPS."""
    return {
        "Alta Prioridade": "#C62828",
        "Média Prioridade": "#F9A825",
        "Baixa Prioridade": "#2E7D32",
    }

def get_ips_order() -> list:
    """Retorna a ordem lógica das faixas IPS."""
    return ["Alta Prioridade", "Média Prioridade", "Baixa Prioridade"]