import pandas as pd

from config import COL_VALOR_PAGO, COL_VOTOS


def build_indicators(df: pd.DataFrame) -> dict:
    """Calcula os indicadores analíticos para o dashboard."""
    df_mun = df[df["tipo_destinacao"] == "MUNICIPIO"]

    municipios_contemplados = df_mun["municipio_normalizado"].nunique()
    valor_total_municipios = df_mun[COL_VALOR_PAGO].sum()
    valor_total_uf = df[df["tipo_destinacao"] == "UF"][COL_VALOR_PAGO].sum()

    total_votos = df_mun.groupby("municipio_normalizado")[COL_VOTOS].max().sum()

    return {
        "municipios_contemplados": int(municipios_contemplados),
        "valor_total_municipios": float(valor_total_municipios),
        "valor_total_uf": float(valor_total_uf),
        "total_votos": int(total_votos),
    }