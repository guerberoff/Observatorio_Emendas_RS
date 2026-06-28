from config import UF_IDENTIFIER

def normalize_municipality_name(value: str) -> str:
    """
    Aplica a padronização completa de nomes de municípios.
    Preserva o identificador da UF.
    """

    # Proteção para valores vazios
    if value is None or value == "":
        return ""

    # Verifica se é o caso especial da UF
    if value.strip() == UF_IDENTIFIER:
        return UF_IDENTIFIER

    # Aplica a limpeza
    clean_value = remove_rs_suffix(value)
    clean_value = normalize_spaces(clean_value)
    clean_value = to_title_case(clean_value)

    return clean_value

def remove_rs_suffix(value: str) -> str:
    """Remove o sufixo ' - RS' de uma string, se existir."""
    if value.endswith(" - RS"):
        return value[:-5]
    return value

def normalize_spaces(value: str) -> str:
    """Remove espaços extras no início/fim e normaliza espaços duplicados."""
    return " ".join(value.split())

def to_title_case(value: str) -> str:
    """Converte para formato de título, preservando preposições em minúsculas."""
    small_words = {"da", "de", "do", "das", "dos", "e"}

    words = value.lower().split()
    formatted_words = [
        word if word in small_words else word.capitalize()
        for word in words
    ]

    return " ".join(formatted_words)

def normalize_municipality_name(value: str) -> str:
    """
    Aplica a padronização completa de nomes de municípios.
    Preserva o identificador da UF.
    """
    # Verifica se é o caso especial da UF
    if value.strip() == UF_IDENTIFIER:
        return UF_IDENTIFIER
    
    # Aplica a limpeza
    clean_value = remove_rs_suffix(value)
    clean_value = normalize_spaces(clean_value)
    clean_value = to_title_case(clean_value)
    
    return clean_value