import pandas as pd

from config import (
    COL_PARLAMENTAR,
    COL_VALOR_PAGO,
    COL_VOTOS,
    COL_CODIGO_IBGE_IPS,
    COL_FAIXA_PRIORIDADE,
)


def filter_by_parliamentarian(df: pd.DataFrame, parliamentarian: str) -> pd.DataFrame:
    """Filtra o DataFrame por um parlamentar específico."""
    return df[df[COL_PARLAMENTAR] == parliamentarian].copy()


def aggregate_municipal_data(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega valores pagos e votos por município."""
    df_mun = df[df["tipo_destinacao"] == "MUNICIPIO"].copy()

    agregado = df_mun.groupby("municipio_normalizado").agg({
        COL_VALOR_PAGO: "sum",
        COL_VOTOS: "max",
        COL_CODIGO_IBGE_IPS: "first",
        COL_FAIXA_PRIORIDADE: "first",
    }).reset_index()

    return agregado


def aggregate_uf_total(df: pd.DataFrame) -> float:
    """Soma o valor total das emendas destinadas à UF."""
    return float(df[df["tipo_destinacao"] == "UF"][COL_VALOR_PAGO].sum())


def aggregate_by_ips_priority(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega os valores pagos por faixa de prioridade social."""
    return df.groupby(COL_FAIXA_PRIORIDADE)[COL_VALOR_PAGO].sum().reset_index()