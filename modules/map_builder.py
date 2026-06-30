import copy
import math
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import shape

from config import MAPA_COR_GRADIENTE
from utils.format_utils import format_currency, format_integer


def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text == "" or text.lower() in ["nan", "none"]:
        return ""

    text = text.upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = " ".join(text.split())

    return text


def _clean_label(value, fallback: str = "Sem informação") -> str:
    if pd.isna(value):
        return fallback

    text = str(value).strip()

    if text == "" or text.lower() in ["nan", "none"]:
        return fallback

    return text


def _get_feature_municipality_name(properties: dict) -> str:
    return (
        properties.get("municipio_normalizado")
        or properties.get("name")
        or properties.get("NOME")
        or properties.get("NM_MUN")
        or properties.get("NM_MUNICIP")
        or properties.get("nome")
        or properties.get("NOME_MUNIC")
        or ""
    )


def _prepare_geojson_for_matching(geojson_data: dict) -> dict:
    geojson_copy = copy.deepcopy(geojson_data)

    for feature in geojson_copy.get("features", []):
        properties = feature.setdefault("properties", {})
        municipio = _get_feature_municipality_name(properties)
        properties["municipio_normalizado"] = _normalize_text(municipio)

    return geojson_copy


def _build_centroids_dataframe(geojson_data: dict) -> pd.DataFrame:
    rows = []

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        geometry_data = feature.get("geometry")

        if not geometry_data:
            continue

        municipio = _get_feature_municipality_name(properties)
        municipio_normalizado = _normalize_text(municipio)

        if municipio_normalizado == "":
            continue

        geom = shape(geometry_data)
        point = geom.representative_point()

        rows.append(
            {
                "municipio_normalizado": municipio_normalizado,
                "lat": point.y,
                "lon": point.x,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["municipio_normalizado", "lat", "lon"])

    centroids_df = pd.DataFrame(rows)
    centroids_df = centroids_df.drop_duplicates(subset=["municipio_normalizado"])

    return centroids_df


def _format_colorbar_value(value: float) -> str:
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f} mi".replace(".", ",")

    return f"R$ {int(value / 1_000)} mil"


def _build_colorbar_ticks(values: pd.Series) -> tuple[list[float], list[str]]:
    if values.empty:
        return [0], ["R$ 0"]

    valor_max = values.max()

    if pd.isna(valor_max) or valor_max <= 0:
        return [0], ["R$ 0"]

    if valor_max <= 1_000_000:
        step = 100_000
    elif valor_max <= 5_000_000:
        step = 500_000
    else:
        step = 1_000_000

    limite_superior = math.ceil(valor_max / step) * step

    ticks = list(range(step, int(limite_superior + step), step))
    ticktext = [_format_colorbar_value(valor) for valor in ticks]

    return ticks, ticktext


def _empty_map_figure() -> go.Figure:
    fig = go.Figure()

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=5.5,
            center={"lat": -30.0, "lon": -53.0},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )

    return fig


def _prepare_vote_summary(vote_df: pd.DataFrame | None) -> pd.DataFrame:
    if vote_df is None or vote_df.empty:
        return pd.DataFrame(
            columns=[
                "municipio_normalizado",
                "QT_VOTOS",
                "faixa_prioridade",
            ]
        )

    df_vote = vote_df.copy()

    if "municipio_normalizado" not in df_vote.columns:
        return pd.DataFrame(
            columns=[
                "municipio_normalizado",
                "QT_VOTOS",
                "faixa_prioridade",
            ]
        )

    if "QT_VOTOS" not in df_vote.columns:
        df_vote["QT_VOTOS"] = 0

    if "faixa_prioridade" not in df_vote.columns:
        df_vote["faixa_prioridade"] = "Sem informação"

    df_vote["municipio_normalizado"] = df_vote["municipio_normalizado"].apply(
        _normalize_text
    )

    df_vote["QT_VOTOS"] = pd.to_numeric(
        df_vote["QT_VOTOS"],
        errors="coerce",
    ).fillna(0)

    df_vote["faixa_prioridade"] = df_vote["faixa_prioridade"].apply(_clean_label)

    df_vote = df_vote[df_vote["municipio_normalizado"] != ""].copy()

    if df_vote.empty:
        return pd.DataFrame(
            columns=[
                "municipio_normalizado",
                "QT_VOTOS",
                "faixa_prioridade",
            ]
        )

    summary = (
        df_vote.groupby("municipio_normalizado", as_index=False)
        .agg(
            QT_VOTOS=("QT_VOTOS", "sum"),
            faixa_prioridade=("faixa_prioridade", "first"),
        )
    )

    return summary


def _prepare_map_dataframe(
    municipal_df: pd.DataFrame,
    vote_municipal_df: pd.DataFrame | None,
) -> pd.DataFrame:
    df_map = municipal_df.copy()

    if "municipio_normalizado" not in df_map.columns:
        df_map["municipio_normalizado"] = ""

    if "Valor Pago" not in df_map.columns:
        df_map["Valor Pago"] = 0

    if "QT_VOTOS" not in df_map.columns:
        df_map["QT_VOTOS"] = 0

    if "faixa_prioridade" not in df_map.columns:
        df_map["faixa_prioridade"] = "Sem informação"

    df_map["municipio_normalizado"] = df_map["municipio_normalizado"].apply(
        _normalize_text
    )

    df_map["Valor Pago"] = pd.to_numeric(
        df_map["Valor Pago"],
        errors="coerce",
    ).fillna(0)

    df_map["QT_VOTOS"] = pd.to_numeric(
        df_map["QT_VOTOS"],
        errors="coerce",
    ).fillna(0)

    df_map["faixa_prioridade"] = df_map["faixa_prioridade"].apply(_clean_label)

    df_map = df_map[
        (df_map["municipio_normalizado"] != "")
        & (df_map["Valor Pago"] > 0)
    ].copy()

    if df_map.empty:
        return df_map

    vote_summary = _prepare_vote_summary(vote_municipal_df)

    if not vote_summary.empty:
        df_map = df_map.merge(
            vote_summary,
            on="municipio_normalizado",
            how="left",
            suffixes=("", "_votos"),
        )

        if "QT_VOTOS_votos" in df_map.columns:
            df_map["QT_VOTOS"] = df_map["QT_VOTOS_votos"].fillna(
                df_map["QT_VOTOS"]
            )

        if "faixa_prioridade_votos" in df_map.columns:
            df_map["faixa_prioridade"] = df_map["faixa_prioridade"].where(
                df_map["faixa_prioridade"].apply(_normalize_text)
                != "SEM INFORMACAO",
                df_map["faixa_prioridade_votos"],
            )

    df_map["QT_VOTOS"] = pd.to_numeric(
        df_map["QT_VOTOS"],
        errors="coerce",
    ).fillna(0)

    df_map["faixa_prioridade"] = df_map["faixa_prioridade"].apply(_clean_label)

    df_map["valor_pago_formatado"] = df_map["Valor Pago"].apply(format_currency)
    df_map["votos_formatados"] = df_map["QT_VOTOS"].apply(format_integer)

    return df_map


def _add_vote_only_markers(
    fig: go.Figure,
    geojson_data: dict,
    vote_df: pd.DataFrame,
    municipalities_with_choropleth: set[str],
) -> go.Figure:
    if vote_df is None or vote_df.empty:
        return fig

    centroids_df = _build_centroids_dataframe(geojson_data)

    if centroids_df.empty:
        return fig

    vote_summary = _prepare_vote_summary(vote_df)

    if vote_summary.empty:
        return fig

    vote_summary = vote_summary[
        ~vote_summary["municipio_normalizado"].isin(municipalities_with_choropleth)
    ].copy()

    vote_summary = vote_summary[vote_summary["QT_VOTOS"] > 0].copy()

    if vote_summary.empty:
        return fig

    vote_summary = vote_summary.merge(
        centroids_df,
        on="municipio_normalizado",
        how="left",
    )

    vote_summary = vote_summary.dropna(subset=["lat", "lon"]).copy()

    if vote_summary.empty:
        return fig

    vote_summary["votos_formatados"] = vote_summary["QT_VOTOS"].apply(format_integer)

    customdata = vote_summary[
        [
            "municipio_normalizado",
            "votos_formatados",
            "faixa_prioridade",
        ]
    ].to_numpy()

    hovertemplate = (
        "<b>%{customdata[0]}</b><br><br>"
        "Emendas municipalizadas: R$ 0,00<br>"
        "Votos recebidos: %{customdata[1]}<br>"
        "Faixa IPS: %{customdata[2]}"
        "<extra></extra>"
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=vote_summary["lat"],
            lon=vote_summary["lon"],
            mode="markers",
            marker=dict(
                size=8,
                color="#1d4ed8",
                opacity=0.20,
            ),
            hoverinfo="skip",
            name="Contorno dos marcadores eleitorais",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=vote_summary["lat"],
            lon=vote_summary["lon"],
            mode="markers",
            marker=dict(
                size=5,
                color=vote_summary["QT_VOTOS"],
                colorscale=[
                    [0.0, "rgb(191, 219, 254)"],
                    [0.35, "rgb(96, 165, 250)"],
                    [0.70, "rgb(37, 99, 235)"],
                    [1.0, "rgb(30, 64, 175)"],
                ],
                opacity=0.70,
                showscale=False,
            ),
            customdata=customdata,
            hovertemplate=hovertemplate,
            name="Votos recebidos",
            showlegend=False,
        )
    )

    return fig


def build_choropleth_map(
    geojson_data: dict,
    municipal_df: pd.DataFrame,
    vote_municipal_df=None,
    show_vote_markers: bool = True,
) -> go.Figure:
    geojson_matching = _prepare_geojson_for_matching(geojson_data)

    df_map = _prepare_map_dataframe(
        municipal_df=municipal_df,
        vote_municipal_df=vote_municipal_df,
    )

    if vote_municipal_df is None:
        vote_municipal_df = df_map.copy()

    municipalities_with_choropleth = set()

    if not df_map.empty:
        municipalities_with_choropleth = set(df_map["municipio_normalizado"])

    if df_map.empty:
        fig = _empty_map_figure()

        if show_vote_markers:
            fig = _add_vote_only_markers(
                fig=fig,
                geojson_data=geojson_matching,
                vote_df=vote_municipal_df,
                municipalities_with_choropleth=municipalities_with_choropleth,
            )

        return fig

    tickvals, ticktext = _build_colorbar_ticks(df_map["Valor Pago"])

    fig = px.choropleth_mapbox(
        df_map,
        geojson=geojson_matching,
        locations="municipio_normalizado",
        featureidkey="properties.municipio_normalizado",
        color="Valor Pago",
        color_continuous_scale=MAPA_COR_GRADIENTE,
        mapbox_style="carto-positron",
        zoom=5.5,
        center={"lat": -30.0, "lon": -53.0},
        opacity=0.72,
        labels={"Valor Pago": "Valor das emendas (R$)"},
        custom_data=[
            "municipio_normalizado",
            "valor_pago_formatado",
            "votos_formatados",
            "faixa_prioridade",
        ],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br><br>"
            "Emendas municipalizadas: %{customdata[1]}<br>"
            "Votos recebidos: %{customdata[2]}<br>"
            "Faixa IPS: %{customdata[3]}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Valor das emendas",
            thickness=18,
            len=0.78,
            tickvals=tickvals,
            ticktext=ticktext,
        )
    )

    if show_vote_markers:
        fig = _add_vote_only_markers(
            fig=fig,
            geojson_data=geojson_matching,
            vote_df=vote_municipal_df,
            municipalities_with_choropleth=municipalities_with_choropleth,
        )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )

    return fig
