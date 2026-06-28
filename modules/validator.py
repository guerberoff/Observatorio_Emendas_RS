import pandas as pd
from config import COLUNAS_OBRIGATORIAS

def validate_required_columns(df: pd.DataFrame, required_columns: list[str] = COLUNAS_OBRIGATORIAS) -> None:
    """Valida se todas as colunas obrigatórias estão presentes no DataFrame."""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas ausentes no CSV: {missing_columns}")

def validate_geojson_structure(geojson_data: dict) -> None:
    """Valida se o GeoJSON possui a estrutura mínima (deve ser um FeatureCollection)."""
    if "type" not in geojson_data or geojson_data["type"] != "FeatureCollection":
        raise ValueError("O arquivo GeoJSON não parece ser um 'FeatureCollection' válido.")
    if "features" not in geojson_data:
        raise ValueError("O arquivo GeoJSON não contém a lista de 'features'.")