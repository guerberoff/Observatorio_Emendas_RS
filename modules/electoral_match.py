import pandas as pd


IPS_ORDER = ["Alta Prioridade", "Média Prioridade", "Baixa Prioridade"]


def format_percentage_one_decimal(value: float) -> str:
    """Formata percentual com uma casa decimal no padrão brasileiro."""
    return f"{value:.1f}%".replace(".", ",")


def build_electoral_match_report(df_parl: pd.DataFrame, top_n: int = 20) -> dict:
    """Calcula sobreposição entre municípios de maior votação e maior volume de emendas."""
    df_mun = df_parl[df_parl["tipo_destinacao"] == "MUNICIPIO"].copy()

    agregado = (
        df_mun.groupby("municipio_normalizado")
        .agg(
            valor_total_emendas=("Valor Pago", "sum"),
            votos=("QT_VOTOS", "max"),
            faixa_prioridade=("faixa_prioridade", "first"),
        )
        .reset_index()
    )

    total_municipios = len(agregado)
    top_n_real = min(top_n, total_municipios)

    top_votos = agregado.nlargest(top_n_real, "votos").copy()
    top_emendas = agregado.nlargest(top_n_real, "valor_total_emendas").copy()

    municipios_top_votos = set(top_votos["municipio_normalizado"])
    municipios_top_emendas = set(top_emendas["municipio_normalizado"])

    municipios_coincidentes_lista = municipios_top_votos.intersection(municipios_top_emendas)

    municipios_coincidentes = agregado[
        agregado["municipio_normalizado"].isin(municipios_coincidentes_lista)
    ].copy()

    municipios_coincidentes = municipios_coincidentes.sort_values(
        "valor_total_emendas", ascending=False
    )

    qtd_coincidentes = len(municipios_coincidentes)
    percentual_coincidencia = (
        (qtd_coincidentes / top_n_real) * 100 if top_n_real > 0 else 0
    )

    distribuicao_ips = (
        municipios_coincidentes["faixa_prioridade"]
        .value_counts()
        .reindex(IPS_ORDER, fill_value=0)
        .to_dict()
    )

    partes_ips = []
    for faixa in IPS_ORDER:
        qtd = distribuicao_ips.get(faixa, 0)
        if qtd > 0:
            partes_ips.append(f"{qtd} na faixa de {faixa} Social")

    if qtd_coincidentes == 0:
        texto = (
            f"Não houve coincidência entre os {top_n_real} municípios com maior votação "
            f"e os {top_n_real} municípios que mais receberam recursos de emendas."
        )
    else:
        ips_texto = ", ".join(partes_ips[:-1])
        if len(partes_ips) > 1:
            ips_texto += f" e {partes_ips[-1]}"
        elif partes_ips:
            ips_texto = partes_ips[0]
        else:
            ips_texto = "sem classificação IPS disponível"

        texto = (
            f"Dos {top_n_real} municípios com maior votação do parlamentar selecionado, "
            f"{qtd_coincidentes} também aparecem entre os {top_n_real} municípios que mais receberam recursos de emendas. "
            f"Isso corresponde a {format_percentage_one_decimal(percentual_coincidencia)} de coincidência. "
            f"Entre os municípios coincidentes, {ips_texto}."
        )

    return {
        "top_votos": top_votos,
        "top_emendas": top_emendas,
        "municipios_coincidentes": municipios_coincidentes,
        "qtd_coincidentes": int(qtd_coincidentes),
        "percentual_coincidencia": float(percentual_coincidencia),
        "distribuicao_ips_coincidentes": distribuicao_ips,
        "texto": texto,
    }