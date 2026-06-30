import pandas as pd
import streamlit as st

from config import PATH_CSV, PATH_GEOJSON
from modules.loader import load_csv, load_geojson
from modules.validator import validate_required_columns, validate_geojson_structure
from modules.preprocessing import preprocess_dataframe
from modules.aggregator import (
    filter_by_parliamentarian,
    aggregate_municipal_data,
    aggregate_by_ips_priority,
)
from modules.map_builder import build_choropleth_map
from modules.cards import render_indicator_card
from modules.charts import build_ips_bar_chart
from modules.electoral_match import build_electoral_match_report
from modules.about import render_about
from utils.format_utils import format_currency, format_integer
from utils.style_loader import load_css


TOP_N_ICT = 20

TIPO_PAGAMENTO_MUNICIPALIZADO = "pagamento_municipalizado"
TIPO_PAGAMENTO_NAO_MUNICIPALIZADO = "pagamento_nao_municipalizado"
TIPO_VOTO_SEM_PAGAMENTO = "voto_sem_pagamento_municipalizado"


def format_percentage_br(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def ensure_tipo_registro_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "tipo_registro" not in df.columns:
        df["tipo_registro"] = TIPO_PAGAMENTO_MUNICIPALIZADO

    df["tipo_registro"] = df["tipo_registro"].fillna("").astype(str).str.strip()

    return df


def split_observatorio_data(df_parl: pd.DataFrame) -> dict:
    df_parl = ensure_tipo_registro_column(df_parl)

    financeiro_mapa = df_parl[
        (df_parl["tipo_registro"] == TIPO_PAGAMENTO_MUNICIPALIZADO)
        & (df_parl["Valor Pago"] > 0)
    ].copy()

    financeiro_total = df_parl[
        df_parl["tipo_registro"].isin(
            [
                TIPO_PAGAMENTO_MUNICIPALIZADO,
                TIPO_PAGAMENTO_NAO_MUNICIPALIZADO,
            ]
        )
    ].copy()

    eleitoral = df_parl[
        df_parl["tipo_registro"].isin(
            [
                TIPO_PAGAMENTO_MUNICIPALIZADO,
                TIPO_VOTO_SEM_PAGAMENTO,
            ]
        )
    ].copy()

    return {
        "financeiro_mapa": financeiro_mapa,
        "financeiro_total": financeiro_total,
        "eleitoral": eleitoral,
    }


def sum_values(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def count_distinct_nonempty(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0

    serie = df[column].fillna("").astype(str).str.strip()
    return int(serie[serie != ""].nunique())


def build_observatorio_indicators(
    financeiro_mapa: pd.DataFrame,
    financeiro_total: pd.DataFrame,
    eleitoral: pd.DataFrame,
) -> dict:
    municipios_contemplados = count_distinct_nonempty(
        financeiro_mapa,
        "municipio_normalizado",
    )

    valor_total_municipios = sum_values(financeiro_mapa, "Valor Pago")
    valor_total_recorte = sum_values(financeiro_total, "Valor Pago")

    valor_total_uf = 0.0
    valor_total_nacional = 0.0

    if not financeiro_total.empty and "tipo_destinacao" in financeiro_total.columns:
        valor_total_uf = sum_values(
            financeiro_total[financeiro_total["tipo_destinacao"] == "Estadual/UF"],
            "Valor Pago",
        )

        valor_total_nacional = sum_values(
            financeiro_total[financeiro_total["tipo_destinacao"] == "Nacional"],
            "Valor Pago",
        )

    if eleitoral.empty:
        total_votos = 0
    else:
        votos_por_municipio = (
            eleitoral.groupby("municipio_normalizado", as_index=False)
            .agg(QT_VOTOS=("QT_VOTOS", "sum"))
        )
        total_votos = int(
            pd.to_numeric(
                votos_por_municipio["QT_VOTOS"],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

    return {
        "municipios_contemplados": municipios_contemplados,
        "valor_total_recorte": valor_total_recorte,
        "valor_total_municipios": valor_total_municipios,
        "valor_total_uf": valor_total_uf,
        "valor_total_nacional": valor_total_nacional,
        "total_votos": total_votos,
    }


def normalize_priority_label(value: str) -> str:
    texto = str(value).strip()

    if texto == "" or texto.lower() in ["nan", "none"]:
        return "Sem classificação"

    return texto


def build_ips_summary_v105(financeiro_mapa: pd.DataFrame) -> dict:
    if financeiro_mapa.empty:
        return {
            "texto": (
                "Não há pagamentos municipalizados para o parlamentar selecionado "
                "neste recorte."
            )
        }

    df_ips = financeiro_mapa.copy()

    if "faixa_prioridade" not in df_ips.columns:
        return {
            "texto": (
                "Não há informação de faixa de prioridade social disponível "
                "para os pagamentos municipalizados do parlamentar selecionado."
            )
        }

    df_ips["faixa_prioridade_limpa"] = df_ips["faixa_prioridade"].apply(
        normalize_priority_label
    )

    resumo = (
        df_ips.groupby("faixa_prioridade_limpa", as_index=False)
        .agg(valor_pago=("Valor Pago", "sum"))
    )

    total = float(resumo["valor_pago"].sum())

    if total <= 0:
        return {
            "texto": (
                "Não há valor municipalizado positivo para calcular a distribuição "
                "por faixa de prioridade social."
            )
        }

    ordem = {
        "Alta Prioridade": 1,
        "Alta Prioridade Social": 1,
        "Média Prioridade": 2,
        "Média Prioridade Social": 2,
        "Media Prioridade": 2,
        "Media Prioridade Social": 2,
        "Baixa Prioridade": 3,
        "Baixa Prioridade Social": 3,
        "Sem classificação": 4,
        "Não se aplica": 5,
    }

    resumo["ordem"] = resumo["faixa_prioridade_limpa"].map(ordem).fillna(99)
    resumo = resumo.sort_values(by=["ordem", "faixa_prioridade_limpa"])

    partes = []

    for _, row in resumo.iterrows():
        faixa = row["faixa_prioridade_limpa"]
        valor = float(row["valor_pago"])
        percentual = valor / total * 100
        partes.append(f"{format_percentage_br(percentual)} à faixa de {faixa}")

    if len(partes) == 1:
        texto_faixas = partes[0]
    else:
        texto_faixas = ", ".join(partes[:-1]) + f" e {partes[-1]}"

    texto = (
        "Dos recursos municipalizados oficialmente para o parlamentar selecionado, "
        f"{texto_faixas}. "
        "A leitura considera apenas pagamentos cuja localidade oficial de aplicação "
        "foi informada em nível municipal no Rio Grande do Sul."
    )

    return {"texto": texto}


st.set_page_config(layout="wide", page_title="Observatório das Emendas RS")
load_css()


@st.cache_data
def get_data():
    df = preprocess_dataframe(load_csv(PATH_CSV))
    df = ensure_tipo_registro_column(df)

    validate_required_columns(df)

    geojson = load_geojson(PATH_GEOJSON)
    validate_geojson_structure(geojson)

    return df, geojson


df, geojson = get_data()


with st.sidebar:
    st.markdown("## 🦉 Observatório")
    st.caption("Transparência • Evidências • Análise Territorial")

    with st.expander("ℹ️ Sobre o Observatório"):
        render_about()

    st.markdown("---")

    opcoes_parlamentares = sorted(
        [
            parlamentar
            for parlamentar in df["Parlamentar_Limpo"].dropna().unique()
            if str(parlamentar).strip() != ""
        ]
    )

    parlamentar_selecionado = st.selectbox(
        "Parlamentar selecionado",
        opcoes_parlamentares,
    )


st.markdown(
    '<h1 class="oers-title">🦉 Observatório das Emendas RS</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="oers-subtitle">Transparência • Evidências • Análise Territorial</p>',
    unsafe_allow_html=True,
)
st.markdown("---")
st.markdown(
    """
    <div class="oers-research-block">
        <strong>📚 Pesquisa</strong><br>
        Redutos eleitorais e destinação de emendas parlamentares no Rio Grande do Sul
    </div>
    """,
    unsafe_allow_html=True,
)


df_parl = filter_by_parliamentarian(df, parlamentar_selecionado)
blocos = split_observatorio_data(df_parl)

df_financeiro_mapa = blocos["financeiro_mapa"]
df_financeiro_total = blocos["financeiro_total"]
df_eleitoral = blocos["eleitoral"]

mun_data = aggregate_municipal_data(df_financeiro_mapa)
vote_mun_data = aggregate_municipal_data(df_eleitoral)
ips_data = aggregate_by_ips_priority(df_financeiro_mapa)

indicadores = build_observatorio_indicators(
    financeiro_mapa=df_financeiro_mapa,
    financeiro_total=df_financeiro_total,
    eleitoral=df_eleitoral,
)

narrativa_ips = build_ips_summary_v105(df_financeiro_mapa)
match_report = build_electoral_match_report(df_eleitoral, top_n=TOP_N_ICT)


col1, col2 = st.columns([4, 1])

with col1:
    st.markdown(
        '<h2 class="oers-section-title">Distribuição Territorial das Emendas</h2>',
        unsafe_allow_html=True,
    )
    st.caption("Parlamentar selecionado")
    st.subheader(parlamentar_selecionado)

    fig_mapa = build_choropleth_map(
        geojson_data=geojson,
        municipal_df=mun_data,
        vote_municipal_df=vote_mun_data,
    )

    st.plotly_chart(
        fig_mapa,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
        },
    )

    st.caption(
        "A intensidade do vermelho representa o valor municipalizado oficialmente. "
        "Os marcadores azuis representam os votos recebidos pelo parlamentar. "
        "Valores com localidade UF ou Nacional são preservados nos totais, mas não "
        "são distribuídos artificialmente no mapa municipal."
    )

    st.markdown(
        '<h3 class="oers-section-title">📊 Destinação de Recursos por Faixa de Prioridade Social (IPS)</h3>',
        unsafe_allow_html=True,
    )

    fig_chart = build_ips_bar_chart(ips_data)
    st.plotly_chart(fig_chart, use_container_width=True)


with col2:
    st.markdown(
        '<h2 class="oers-section-title">Painel Analítico</h2>',
        unsafe_allow_html=True,
    )

    render_indicator_card(
        "📍",
        "Municípios contemplados",
        format_integer(indicadores["municipios_contemplados"]),
        "Municípios que receberam pagamento municipalizado oficialmente.",
    )

    render_indicator_card(
        "💰",
        "Total Pago no Recorte",
        format_currency(indicadores["valor_total_recorte"]),
        "Total pago nos CSVs detalhados, incluindo valores municipalizados e não municipalizados.",
    )

    render_indicator_card(
        "🏙️",
        "Emendas aos Municípios",
        format_currency(indicadores["valor_total_municipios"]),
        "Total pago com localidade oficial municipal no Rio Grande do Sul.",
    )

    render_indicator_card(
        "🏛️",
        "Emendas Estaduais (UF)",
        format_currency(indicadores["valor_total_uf"]),
        "Recursos com localidade oficial em nível de Unidade da Federação.",
    )

    render_indicator_card(
        "🌐",
        "Emendas Nacionais",
        format_currency(indicadores["valor_total_nacional"]),
        "Recursos com localidade oficial nacional.",
    )

    render_indicator_card(
        "🗳️",
        "Votos Recebidos",
        format_integer(indicadores["total_votos"]),
        "Soma dos votos municipais do parlamentar em 2022.",
    )


st.markdown(
    '<h2 class="oers-section-title">🦉 Leitura do Observatório</h2>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="oers-card">
        <p class="oers-narrative-text">{narrativa_ips["texto"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<h2 class="oers-section-title">🔎 Correspondência Territorial (ICT)</h2>',
    unsafe_allow_html=True,
)

ict_col1, ict_col2, ict_col3 = st.columns(3)

with ict_col1:
    render_indicator_card(
        "🔁",
        "Municípios coincidentes",
        format_integer(match_report["qtd_coincidentes"]),
        "Municípios que aparecem simultaneamente entre os maiores em votos e em emendas.",
    )

with ict_col2:
    render_indicator_card(
        "📐",
        "ICT",
        format_percentage_br(match_report["percentual_coincidencia"]),
        "Índice de Correspondência Territorial.",
    )

with ict_col3:
    render_indicator_card(
        "📋",
        "Ranking analisado",
        format_integer(TOP_N_ICT),
        "Quantidade de municípios considerada em cada ranking.",
    )

st.markdown(
    f"""
    <div class="oers-card">
        <div class="oers-card-header">🦉 Leitura do Observatório — ICT</div>
        <p class="oers-narrative-text">{match_report["texto"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Ver municípios coincidentes"):
    df_table = match_report["municipios_coincidentes"].copy()

    if not df_table.empty:
        df_table = df_table[
            [
                "municipio_normalizado",
                "votos",
                "valor_total_emendas",
                "faixa_prioridade",
            ]
        ]

        df_table = df_table.rename(
            columns={
                "municipio_normalizado": "Município",
                "votos": "Votos",
                "valor_total_emendas": "Valor em Emendas",
                "faixa_prioridade": "Faixa IPS",
            }
        )

        df_table["Votos"] = df_table["Votos"].apply(format_integer)
        df_table["Valor em Emendas"] = df_table["Valor em Emendas"].apply(
            format_currency
        )

        st.dataframe(df_table, use_container_width=True, hide_index=True)
    else:
        st.info("Não há municípios coincidentes no ranking analisado.")


with st.expander("Nota metodológica sobre municipalização e votos"):
    st.markdown(
        """
        A base atual separa três tipos de registro:

        - **pagamento_municipalizado**: pagamentos cuja localidade oficial de aplicação
          foi informada como município do Rio Grande do Sul. Esses valores entram no mapa.
        - **pagamento_nao_municipalizado**: pagamentos com localidade oficial em nível UF
          ou Nacional. Esses valores entram nos totais financeiros, mas não são distribuídos
          artificialmente entre municípios.
        - **voto_sem_pagamento_municipalizado**: linhas eleitorais complementares,
          criadas para preservar os votos de 2022 nos municípios em que o parlamentar
          teve votos, mas não teve pagamento municipalizado oficial.

        No caso especial **Paulo Pimenta / Reginete Bispo**, Paulo Pimenta é preservado
        em arquivo metodológico complementar como contexto eleitoral-institucional, mas
        não é incluído na base financeira principal porque não aparece como autor de
        emendas no recorte financeiro de 2025. Reginete Bispo permanece na base principal
        com seus próprios votos de 2022 e suas próprias emendas de 2025.
        """
    )


st.markdown(
    """
    <div class="oers-footer">
        <strong>Observatório das Emendas RS</strong><br>
        Versão 1.0.1<br>
        Projeto acadêmico desenvolvido na Universidade Federal do Rio Grande do Sul (UFRGS)
    </div>
    """,
    unsafe_allow_html=True,
)
