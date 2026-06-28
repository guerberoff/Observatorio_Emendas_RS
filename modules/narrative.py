import pandas as pd

from utils.format_utils import format_currency


def format_percentage_one_decimal(value: float) -> str:
    """Formata percentual com uma casa decimal no padrão brasileiro."""
    return f"{value:.1f}%".replace(".", ",")


def build_ips_summary(ips_df: pd.DataFrame) -> dict:
    """Gera resumo textual objetivo da distribuição de emendas por IPS."""
    total_pago = ips_df["Valor Pago"].sum()

    percentuais = {}
    for _, row in ips_df.iterrows():
        faixa = row["faixa_prioridade"]
        valor = row["Valor Pago"]
        percentual = (valor / total_pago * 100) if total_pago > 0 else 0
        percentuais[faixa] = percentual

    maior_faixa = (
        ips_df.loc[ips_df["Valor Pago"].idxmax(), "faixa_prioridade"]
        if not ips_df.empty
        else "Nenhuma"
    )

    ordem = ["Alta Prioridade", "Média Prioridade", "Baixa Prioridade"]

    trechos = []
    for faixa in ordem:
        if faixa in percentuais:
            percentual_formatado = format_percentage_one_decimal(percentuais[faixa])
            trechos.append(
                f"{percentual_formatado} à faixa de {faixa} Social"
            )

    if len(trechos) == 3:
        texto = (
            "Dos recursos destinados pelo parlamentar selecionado, "
            f"{trechos[0]}, {trechos[1]} e {trechos[2]}."
        )
    elif trechos:
        texto = (
            "Dos recursos destinados pelo parlamentar selecionado, "
            + ", ".join(trechos)
            + "."
        )
    else:
        texto = (
            "Não há recursos classificados por faixa de prioridade social "
            "para o parlamentar selecionado."
        )

    return {
        "total_pago": float(total_pago),
        "total_pago_formatado": format_currency(total_pago),
        "percentuais": percentuais,
        "maior_faixa": maior_faixa,
        "texto": texto,
    }