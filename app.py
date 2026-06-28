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
from modules.indicators import build_indicators
from modules.cards import render_indicator_card
from modules.charts import build_ips_bar_chart
from modules.narrative import build_ips_summary
from modules.electoral_match import build_electoral_match_report
from modules.about import render_about
from utils.format_utils import format_currency, format_integer
from utils.style_loader import load_css


TOP_N_ICT = 20


def format_percentage_br(value: float) -> str:
    """Formata percentual com uma casa decimal no padrão brasileiro."""
    return f"{value:.1f}%".replace(".", ",")


st.set_page_config(layout="wide", page_title="Observatório das Emendas RS")
load_css()


@st.cache_data
def get_data():
    df = preprocess_dataframe(load_csv(PATH_CSV))
    validate_required_columns(df)

    geojson = load_geojson(PATH_GEOJSON)
    validate_geojson_structure(geojson)

    return df, geojson


# Dados
df, geojson = get_data()


# Barra lateral — identidade, sobre e filtro
with st.sidebar:
    st.markdown("## 🦉 Observatório")
    st.caption("Transparência • Evidências • Análise Territorial")

    with st.expander("ℹ️ Sobre o Observatório"):
        render_about()

    st.markdown("---")

    parlamentar_selecionado = st.selectbox(
        "Parlamentar selecionado",
        sorted(df["Parlamentar_Limpo"].unique()),
    )


# Cabeçalho principal
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


# Processamento
df_parl = filter_by_parliamentarian(df, parlamentar_selecionado)

mun_data = aggregate_municipal_data(df_parl)
ips_data = aggregate_by_ips_priority(df_parl)
indicadores = build_indicators(df_parl)
narrativa_ips = build_ips_summary(ips_data)
match_report = build_electoral_match_report(df_parl, top_n=TOP_N_ICT)


# Bloco 1 — Mapa + IPS + indicadores
col1, col2 = st.columns([4, 1])

with col1:
    st.markdown(
        '<h2 class="oers-section-title">Distribuição Territorial das Emendas</h2>',
        unsafe_allow_html=True,
    )
    st.caption("Parlamentar selecionado")
    st.subheader(parlamentar_selecionado)

    fig_mapa = build_choropleth_map(geojson, mun_data)
    st.plotly_chart(
        fig_mapa,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
        },
    )

    st.caption(
        "A intensidade do vermelho representa o valor das emendas destinadas ao município. "
        "Os marcadores azuis representam os votos recebidos pelo parlamentar."
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
        "Municípios que receberam emendas do parlamentar selecionado.",
    )

    render_indicator_card(
        "💰",
        "Emendas aos Municípios",
        format_currency(indicadores["valor_total_municipios"]),
        "Total pago em emendas destinadas diretamente aos municípios.",
    )

    render_indicator_card(
        "🏛️",
        "Emendas Estaduais (UF)",
        format_currency(indicadores["valor_total_uf"]),
        "Recursos destinados ao Estado do Rio Grande do Sul.",
    )

    render_indicator_card(
        "🗳️",
        "Votos Recebidos",
        format_integer(indicadores["total_votos"]),
        "Soma dos votos municipais, evitando duplicidade por município.",
    )


# Bloco 2 — Leitura IPS
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


# Bloco 3 — ICT
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
    df_table["Valor em Emendas"] = df_table["Valor em Emendas"].apply(format_currency)

    st.dataframe(df_table, use_container_width=True, hide_index=True)


# Rodapé
st.markdown(
    """
    <div class="oers-footer">
        <strong>Observatório das Emendas RS</strong><br>
        Versão 1.0<br>
        Projeto acadêmico desenvolvido na Universidade Federal do Rio Grande do Sul (UFRGS)
    </div>
    """,
    unsafe_allow_html=True,
)