def format_currency(value: float) -> str:
    """Formata float para moeda brasileira (R$ X.XXX,XX)."""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_integer(value: int | float) -> str:
    """Formata int/float para número inteiro com separador de milhar (X.XXX)."""
    if value is None:
        return "0"
    return f"{int(value):,.0f}".replace(",", ".")

def format_percentage(value: float) -> str:
    """Formata float para porcentagem (XX,XX%)."""
    if value is None:
        return "0,00%"
    return f"{value:.2f}%".replace(".", ",")