import pandas as pd
import json
from pathlib import Path
from config import PATH_CSV, PATH_GEOJSON, CSV_SEP

def check_file_exists(path: Path) -> bool:
    """Verifica se um arquivo existe no caminho especificado."""
    return path.exists()

def load_csv(path: Path = PATH_CSV) -> pd.DataFrame:
    """Carrega o arquivo CSV usando o separador definido no config."""
    if not check_file_exists(path):
        raise FileNotFoundError(f"Arquivo CSV não encontrado em: {path}")
    return pd.read_csv(path, sep=CSV_SEP)

def load_geojson(path: Path = PATH_GEOJSON) -> dict:
    """Carrega o arquivo GeoJSON."""
    if not check_file_exists(path):
        raise FileNotFoundError(f"Arquivo GeoJSON não encontrado em: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)