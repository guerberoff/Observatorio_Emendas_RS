import pandas as pd

from config import COL_LOCALIDADE, UF_IDENTIFIER
from utils.text_utils import normalize_municipality_name


def add_normalized_municipality_column(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a coluna municipio_normalizado aplicando a padronização."""
    df["municipio_normalizado"] = df[COL_LOCALIDADE].apply(normalize_municipality_name)
    return df


def add_destination_type_column(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a coluna tipo_destinacao baseada no identificador de UF."""
    df["tipo_destinacao"] = df[COL_LOCALIDADE].apply(
        lambda x: "UF" if x == UF_IDENTIFIER else "MUNICIPIO"
    )
    return df


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Executa todas as etapas de pré-processamento e retorna um novo DataFrame."""
    df_processed = df.copy()
    df_processed = add_normalized_municipality_column(df_processed)
    df_processed = add_destination_type_column(df_processed)
    return df_processed