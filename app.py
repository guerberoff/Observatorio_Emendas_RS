import pandas as pd
import unicodedata
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

VERSAO_APP = "1.1.0"

PATH_DETALHES_EMENDAS = "dados/base_detalhes_emendas_v106.csv"
TOP_N_ALOCACOES = 10

PARTIDOS_PARLAMENTARES = {
    "ALCEU MOREIRA": "MDB",
    "ANY ORTIZ": "PP",
    "DAIANA SANTOS": "PCdoB",
    "DANRLEI DE DEUS HINTERHOLZ": "PSD",
    "FERNANDA MELCHIONNA": "PSOL",
    "HEITOR SCHUCH": "PSD",
    "LUCAS REDECKER": "PSD",
    "LUIZ CARLOS BUSATO": "UNIÃO",
    "MARCEL VAN HATTEM": "NOVO",
    "MAURICIO MARCON": "PL",
    "POMPEO DE MATTOS": "PDT",
    "REGINETE BISPO": "PT",
    "ZUCCO": "PL",
}


def format_percentage_br(value: float) -> str:
    """Formata percentual com uma casa decimal no padrão brasileiro."""
    return f"{value:.1f}%".replace(".", ",")


def ensure_tipo_registro_column(df: pd.DataFrame) -> pd.DataFrame:
    """Garante compatibilidade com bases antigas sem a coluna tipo_registro."""
    df = df.copy()

    if "tipo_registro" not in df.columns:
        df["tipo_registro"] = TIPO_PAGAMENTO_MUNICIPALIZADO

    df["tipo_registro"] = df["tipo_registro"].fillna("").astype(str).str.strip()

    return df


def split_observatorio_data(df_parl: pd.DataFrame) -> dict:
    """Separa a base do parlamentar em blocos financeiro, territorial e eleitoral."""
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
    """Soma uma coluna numérica de forma segura."""
    if df.empty or column not in df.columns:
        return 0.0

    return float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def count_distinct_nonempty(df: pd.DataFrame, column: str) -> int:
    """Conta valores distintos não vazios em uma coluna."""
    if df.empty or column not in df.columns:
        return 0

    serie = df[column].fillna("").astype(str).str.strip()

    return int(serie[serie != ""].nunique())


def normalize_text_for_match(value: object) -> str:
    """Normaliza texto para comparação sem depender de acento ou caixa."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text == "" or text.lower() in ["nan", "none"]:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper()
    text = " ".join(text.split())

    return text


def get_party_for_parliamentarian(parlamentar: object) -> str:
    """Retorna a sigla partidária do parlamentar, quando cadastrada."""
    parlamentar_norm = normalize_text_for_match(parlamentar)

    return PARTIDOS_PARLAMENTARES.get(parlamentar_norm, "")


def format_parliamentarian_label(parlamentar: object) -> str:
    """Formata o nome exibido no dropdown com partido entre parênteses."""
    nome = str(parlamentar).strip()
    partido = get_party_for_parliamentarian(nome)

    if partido == "":
        return nome

    return f"{nome} ({partido})"


def normalize_locality_type(value: object) -> str:
    """Padroniza os rótulos de tipo de localidade usados nos cards."""
    text = normalize_text_for_match(value)

    if text == "":
        return ""

    if text in ["MUNICIPAL", "MUNICIPIO"]:
        return "Municipal"

    if text in ["ESTADUAL/UF", "UF", "ESTADUAL", "ESTADO"]:
        return "Estadual/UF"

    if text in ["NACIONAL", "BRASIL"]:
        return "Nacional"

    if text == "SEM PAGAMENTO MUNICIPALIZADO":
        return "Sem pagamento municipalizado"

    return str(value).strip()


def classify_destination_for_card(row: pd.Series) -> str:
    """
    Classifica a linha para os cards Municipal / UF / Nacional.

    Prioridade:
    1. tipo_destinacao, que é a coluna consolidada correta da base v105.
    2. Colunas equivalentes, se existirem.
    3. Localidade de aplicação do recurso, como fallback.
    """
    for column in [
        "tipo_destinacao",
        "tipo_localidade_aplicacao",
        "tipo_localidade",
    ]:
        if column in row.index:
            classification = normalize_locality_type(row[column])

            if classification in [
                "Municipal",
                "Estadual/UF",
                "Nacional",
                "Sem pagamento municipalizado",
            ]:
                return classification

    for column in [
        "Localidade de aplicação do recurso",
        "localidade_aplicacao",
    ]:
        if column not in row.index:
            continue

        location = normalize_text_for_match(row[column])

        if location == "":
            continue

        if location in ["NACIONAL", "BRASIL"] or "NACIONAL" in location:
            return "Nacional"

        if "(UF)" in location or location in ["RIO GRANDE DO SUL", "RS"]:
            return "Estadual/UF"

        if location.endswith("- RS") or " - RS" in str(row[column]):
            return "Municipal"

    return ""


def build_observatorio_indicators(
    financeiro_mapa: pd.DataFrame,
    financeiro_total: pd.DataFrame,
    eleitoral: pd.DataFrame,
) -> dict:
    """Calcula indicadores compatíveis com a base v105."""
    municipios_contemplados = count_distinct_nonempty(
        financeiro_mapa,
        "municipio_normalizado",
    )

    valor_total_municipios = sum_values(financeiro_mapa, "Valor Pago")
    valor_total_recorte = sum_values(financeiro_total, "Valor Pago")

    valor_total_uf = 0.0
    valor_total_nacional = 0.0

    if not financeiro_total.empty:
        financeiro_total = financeiro_total.copy()

        nao_municipalizado = financeiro_total[
            financeiro_total["tipo_registro"] == TIPO_PAGAMENTO_NAO_MUNICIPALIZADO
        ].copy()

        if not nao_municipalizado.empty:
            mask_nacional = pd.Series(False, index=nao_municipalizado.index)

            for column in [
                "Localidade de aplicação do recurso",
                "localidade_aplicacao",
                "tipo_destinacao",
                "tipo_localidade_aplicacao",
                "tipo_localidade",
            ]:
                if column not in nao_municipalizado.columns:
                    continue

                serie_normalizada = nao_municipalizado[column].apply(
                    normalize_text_for_match
                )

                mask_nacional = mask_nacional | serie_normalizada.str.contains(
                    "NACIONAL|BRASIL",
                    case=False,
                    regex=True,
                    na=False,
                )

            valor_total_nacional = sum_values(
                nao_municipalizado[mask_nacional],
                "Valor Pago",
            )

            valor_total_uf = sum_values(
                nao_municipalizado[~mask_nacional],
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


def normalize_priority_label(value: object) -> str:
    """Padroniza rótulos vazios da faixa de prioridade."""
    texto = str(value).strip()

    if texto == "" or texto.lower() in ["nan", "none"]:
        return "Sem classificação"

    return texto


def build_ips_summary_v105(financeiro_mapa: pd.DataFrame) -> dict:
    """Cria narrativa IPS usando apenas pagamentos municipalizados."""
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



def load_emendas_detalhadas_v106(path: str) -> pd.DataFrame:
    """Carrega a base auxiliar de detalhes financeiros v106."""
    try:
        df_detalhes = pd.read_csv(
            path,
            sep=";",
            encoding="utf-8-sig",
            dtype=str,
            low_memory=False,
        )
    except FileNotFoundError:
        return pd.DataFrame()

    if df_detalhes.empty:
        return df_detalhes

    if "valor_pago" in df_detalhes.columns:
        df_detalhes["valor_pago"] = pd.to_numeric(
            df_detalhes["valor_pago"],
            errors="coerce",
        ).fillna(0)
    else:
        df_detalhes["valor_pago"] = 0

    for column in [
        "Parlamentar_Limpo",
        "municipio",
        "municipio_normalizado",
        "codigo_emenda",
        "tipo_transferencia",
        "tipo_localidade_aplicacao",
        "acao_orcamentaria",
        "programa_orcamentario",
    ]:
        if column not in df_detalhes.columns:
            df_detalhes[column] = ""

        df_detalhes[column] = df_detalhes[column].fillna("").astype(str).str.strip()

    return df_detalhes


def filter_details_by_parliamentarian(
    df_detalhes: pd.DataFrame,
    parlamentar: str,
) -> pd.DataFrame:
    """Filtra a base auxiliar de detalhes para o parlamentar selecionado."""
    if df_detalhes.empty or "Parlamentar_Limpo" not in df_detalhes.columns:
        return pd.DataFrame()

    parlamentar_norm = normalize_text_for_match(parlamentar)

    return df_detalhes[
        df_detalhes["Parlamentar_Limpo"].apply(normalize_text_for_match)
        == parlamentar_norm
    ].copy()


def build_transfer_summary_table(df_detalhes_parl: pd.DataFrame) -> pd.DataFrame:
    """Monta tabela de Transferência Especial x Finalidade Definida."""
    if df_detalhes_parl.empty:
        return pd.DataFrame(
            columns=[
                "Tipo de transferência",
                "Valor Pago",
                "% do total",
            ]
        )

    resumo = (
        df_detalhes_parl.groupby("tipo_transferencia", as_index=False)
        .agg(valor_pago=("valor_pago", "sum"))
        .sort_values("valor_pago", ascending=False)
    )

    total = float(resumo["valor_pago"].sum())

    if total == 0:
        resumo["percentual"] = 0.0
    else:
        resumo["percentual"] = resumo["valor_pago"] / total * 100

    resumo = resumo.rename(
        columns={
            "tipo_transferencia": "Tipo de transferência",
            "valor_pago": "Valor Pago",
            "percentual": "% do total",
        }
    )

    resumo["Valor Pago"] = resumo["Valor Pago"].apply(format_currency)
    resumo["% do total"] = resumo["% do total"].apply(format_percentage_br)

    return resumo[
        [
            "Tipo de transferência",
            "Valor Pago",
            "% do total",
        ]
    ]


def build_top_allocations_table(
    df_detalhes_parl: pd.DataFrame,
    top_n: int = TOP_N_ALOCACOES,
) -> pd.DataFrame:
    """Monta tabela das maiores alocações municipalizadas por código de emenda."""
    if df_detalhes_parl.empty:
        return pd.DataFrame(
            columns=[
                "Município",
                "Código da Emenda",
                "Tipo de transferência",
                "Ação Orçamentária",
                "Valor Pago",
            ]
        )

    df_top = df_detalhes_parl.copy()

    df_top = df_top[
        df_top["tipo_localidade_aplicacao"].apply(normalize_text_for_match)
        == "MUNICIPAL"
    ].copy()

    if df_top.empty:
        return pd.DataFrame(
            columns=[
                "Município",
                "Código da Emenda",
                "Tipo de transferência",
                "Ação Orçamentária",
                "Valor Pago",
            ]
        )

    df_top["municipio_exibicao"] = df_top["municipio"].where(
        df_top["municipio"].str.strip() != "",
        df_top["municipio_normalizado"],
    )

    group_columns = [
        "municipio_exibicao",
        "codigo_emenda",
        "tipo_transferencia",
        "acao_orcamentaria",
    ]

    resumo = (
        df_top.groupby(group_columns, dropna=False, as_index=False)
        .agg(valor_pago=("valor_pago", "sum"))
    )

    resumo = resumo[resumo["valor_pago"] > 0].copy()
    resumo = resumo.sort_values("valor_pago", ascending=False).head(top_n)

    resumo = resumo.rename(
        columns={
            "municipio_exibicao": "Município",
            "codigo_emenda": "Código da Emenda",
            "tipo_transferencia": "Tipo de transferência",
            "acao_orcamentaria": "Ação Orçamentária",
            "valor_pago": "Valor Pago",
        }
    )

    resumo["Valor Pago"] = resumo["Valor Pago"].apply(format_currency)

    return resumo[
        [
            "Município",
            "Código da Emenda",
            "Tipo de transferência",
            "Ação Orçamentária",
            "Valor Pago",
        ]
    ]


def build_municipios_contemplados_table(
    financeiro_mapa: pd.DataFrame,
    eleitoral: pd.DataFrame,
) -> pd.DataFrame:
    """Monta tabela de conferência dos municípios contemplados no mapa."""
    columns = [
        "Município",
        "Valor em Emendas",
        "Votos",
        "Faixa IPS",
    ]

    if financeiro_mapa.empty:
        return pd.DataFrame(columns=columns)

    df_financeiro = financeiro_mapa.copy()

    if "municipio_normalizado" not in df_financeiro.columns:
        return pd.DataFrame(columns=columns)

    if "Valor Pago" not in df_financeiro.columns:
        df_financeiro["Valor Pago"] = 0

    if "faixa_prioridade" not in df_financeiro.columns:
        df_financeiro["faixa_prioridade"] = "Sem informação"

    df_financeiro["municipio_normalizado"] = df_financeiro[
        "municipio_normalizado"
    ].apply(normalize_text_for_match)

    df_financeiro["Valor Pago"] = pd.to_numeric(
        df_financeiro["Valor Pago"],
        errors="coerce",
    ).fillna(0)

    resumo_financeiro = (
        df_financeiro[
            (df_financeiro["municipio_normalizado"] != "")
            & (df_financeiro["Valor Pago"] > 0)
        ]
        .groupby("municipio_normalizado", as_index=False)
        .agg(
            valor_pago=("Valor Pago", "sum"),
            faixa_prioridade=("faixa_prioridade", "first"),
        )
    )

    if resumo_financeiro.empty:
        return pd.DataFrame(columns=columns)

    if eleitoral.empty or "municipio_normalizado" not in eleitoral.columns:
        resumo_financeiro["QT_VOTOS"] = 0
    else:
        df_votos = eleitoral.copy()

        if "QT_VOTOS" not in df_votos.columns:
            df_votos["QT_VOTOS"] = 0

        df_votos["municipio_normalizado"] = df_votos[
            "municipio_normalizado"
        ].apply(normalize_text_for_match)

        df_votos["QT_VOTOS"] = pd.to_numeric(
            df_votos["QT_VOTOS"],
            errors="coerce",
        ).fillna(0)

        resumo_votos = (
            df_votos[df_votos["municipio_normalizado"] != ""]
            .groupby("municipio_normalizado", as_index=False)
            .agg(QT_VOTOS=("QT_VOTOS", "sum"))
        )

        resumo_financeiro = resumo_financeiro.merge(
            resumo_votos,
            on="municipio_normalizado",
            how="left",
        )

        resumo_financeiro["QT_VOTOS"] = resumo_financeiro["QT_VOTOS"].fillna(0)

    resumo_financeiro = resumo_financeiro.sort_values(
        "valor_pago",
        ascending=False,
    )

    resumo_financeiro = resumo_financeiro.rename(
        columns={
            "municipio_normalizado": "Município",
            "valor_pago": "Valor em Emendas",
            "QT_VOTOS": "Votos",
            "faixa_prioridade": "Faixa IPS",
        }
    )

    resumo_financeiro["Valor em Emendas"] = resumo_financeiro[
        "Valor em Emendas"
    ].apply(format_currency)

    resumo_financeiro["Votos"] = resumo_financeiro["Votos"].apply(format_integer)

    return resumo_financeiro[columns]




st.set_page_config(layout="wide", page_title="Observatório das Emendas RS")
load_css()


@st.cache_data
def get_data():
    df = preprocess_dataframe(load_csv(PATH_CSV))
    df = ensure_tipo_registro_column(df)

    validate_required_columns(df)

    geojson = load_geojson(PATH_GEOJSON)
    validate_geojson_structure(geojson)

    df_detalhes = load_emendas_detalhadas_v106(PATH_DETALHES_EMENDAS)

    return df, geojson, df_detalhes


# Dados
df, geojson, df_detalhes = get_data()

opcoes_parlamentares = sorted(
    [
        parlamentar
        for parlamentar in df["Parlamentar_Limpo"].dropna().unique()
        if str(parlamentar).strip() != ""
    ]
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

with st.expander("ℹ️ Sobre o Observatório", expanded=False):
    render_about()

st.markdown(
    """
    <div class="oers-research-block">
        <strong>📚 Pesquisa</strong><br>
        Redutos eleitorais e destinação de emendas parlamentares no Rio Grande do Sul
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# Layout principal em abas
tab_mapa, tab_detalhes, tab_ict, tab_metodologia = st.tabs(
    [
        "🗺️ Mapa e Indicadores",
        "💵 Detalhamento Financeiro",
        "🔎 ICT",
        "📌 Metodologia",
    ]
)


with tab_mapa:
    st.markdown(
        '<h2 class="oers-section-title">Distribuição Territorial das Emendas</h2>',
        unsafe_allow_html=True,
    )

    st.caption("Parlamentar selecionado")
    parlamentar_selecionado = st.selectbox(
        "Parlamentar selecionado",
        opcoes_parlamentares,
        format_func=format_parliamentarian_label,
        label_visibility="collapsed",
    )

# Processamento
df_parl = filter_by_parliamentarian(df, parlamentar_selecionado)
blocos = split_observatorio_data(df_parl)

df_financeiro_mapa = blocos["financeiro_mapa"]
df_financeiro_total = blocos["financeiro_total"]
df_eleitoral = blocos["eleitoral"]

df_detalhes_parl = filter_details_by_parliamentarian(
    df_detalhes,
    parlamentar_selecionado,
)

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

transfer_summary_table = build_transfer_summary_table(df_detalhes_parl)
top_allocations_table = build_top_allocations_table(
    df_detalhes_parl,
    top_n=TOP_N_ALOCACOES,
)

municipios_contemplados_table = build_municipios_contemplados_table(
    financeiro_mapa=df_financeiro_mapa,
    eleitoral=df_eleitoral,
)


with tab_mapa:
    col_mapa, col_cards = st.columns([4, 1])

    with col_mapa:
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
            "Nos municípios coloridos, o tooltip reúne emendas, votos e faixa IPS. "
            "Os marcadores azuis indicam votos em municípios sem pagamento municipalizado oficial. "
            "Valores UF ou Nacional são preservados nos totais, mas não são distribuídos "
            "artificialmente no mapa municipal."
        )

        with st.expander(
            f"Ver municípios contemplados no mapa ({indicadores['municipios_contemplados']})"
        ):
            if municipios_contemplados_table.empty:
                st.info("Não há municípios contemplados para o parlamentar selecionado.")
            else:
                st.dataframe(
                    municipios_contemplados_table,
                    use_container_width=True,
                    hide_index=True,
                )

        st.markdown("---")

        st.markdown(
            '<h3 class="oers-section-title">📊 Recursos por Faixa de Prioridade Social (IPS)</h3>',
            unsafe_allow_html=True,
        )

        fig_chart = build_ips_bar_chart(ips_data)
        st.plotly_chart(fig_chart, use_container_width=True)

        st.markdown("---")

        st.markdown(
            '<h3 class="oers-section-title">🦉 Leitura do Observatório</h3>',
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

    with col_cards:
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


with tab_detalhes:
    st.markdown(
        '<h2 class="oers-section-title">Detalhamento Financeiro</h2>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Esta seção usa a base auxiliar detalhada por código de emenda. "
        "Ela não altera o mapa nem os indicadores principais."
    )

    resumo_col1, resumo_col2 = st.columns([1, 2])

    with resumo_col1:
        st.markdown(
            '<h3 class="oers-section-title">Transferências por Tipo</h3>',
            unsafe_allow_html=True,
        )

        if transfer_summary_table.empty:
            st.info("Não há dados detalhados de transferência para o parlamentar selecionado.")
        else:
            st.dataframe(
                transfer_summary_table,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Classificação derivada do tipo da emenda nos CSVs detalhados."
        )

    with resumo_col2:
        st.markdown(
            f'<h3 class="oers-section-title">Top {TOP_N_ALOCACOES} Alocações Municipalizadas</h3>',
            unsafe_allow_html=True,
        )

        if top_allocations_table.empty:
            st.info("Não há alocações municipalizadas para o parlamentar selecionado.")
        else:
            st.dataframe(
                top_allocations_table,
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Ranking restrito a pagamentos com localidade oficial municipal no Rio Grande do Sul."
        )

    with st.expander("Como interpretar este detalhamento"):
        st.markdown(
            """
            - **Transferência Especial** corresponde às emendas do tipo Pix.
            - **Transferência com Finalidade Definida** corresponde às emendas com finalidade/programação indicada.
            - O **Top 10 Alocações Municipalizadas** considera município, código real da emenda,
              tipo de transferência e ação orçamentária.
            - Valores com localidade **Estadual/UF** ou **Nacional** ficam preservados nos cards
              principais, mas não entram no ranking municipal.
            """
        )


with tab_ict:
    st.markdown(
        '<h2 class="oers-section-title">Correspondência Territorial (ICT)</h2>',
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


with tab_metodologia:
    st.markdown(
        '<h2 class="oers-section-title">Notas metodológicas</h2>',
        unsafe_allow_html=True,
    )

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

        A seção de **Detalhamento Financeiro** usa uma base auxiliar derivada dos
        pagamentos detalhados por código de emenda. Essa base preserva códigos reais,
        ação orçamentária e tipo de transferência, inclusive ajustes negativos/estornos,
        para que o total continue batendo com a base financeira principal.

        No mapa, cada município contemplado deve ter um único tooltip consolidado,
        reunindo valor municipalizado, votos e faixa IPS. Os marcadores azuis ficam
        reservados para municípios com votos, mas sem pagamento municipalizado oficial.

        As siglas partidárias exibidas no seletor de parlamentares foram cadastradas
        em tabela auxiliar do próprio app, com base nas páginas públicas da Câmara dos
        Deputados consultadas durante a preparação da versão 1.1.0.

        No caso especial **Paulo Pimenta / Reginete Bispo**, Paulo Pimenta é preservado
        em arquivo metodológico complementar como contexto eleitoral-institucional, mas
        não é incluído na base financeira principal porque não aparece como autor de
        emendas no recorte financeiro de 2025. Reginete Bispo permanece na base principal
        com seus próprios votos de 2022 e suas próprias emendas de 2025.
        """
    )


# Rodapé
st.markdown(
    f"""
    <div class="oers-footer">
        <strong>Observatório das Emendas RS</strong><br>
        Versão {VERSAO_APP}<br>
        Projeto acadêmico desenvolvido na Universidade Federal do Rio Grande do Sul (UFRGS)
    </div>
    """,
    unsafe_allow_html=True,
)
