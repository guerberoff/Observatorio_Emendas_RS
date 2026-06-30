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


def _add_vote_markers(
    fig: go.Figure,
    geojson_data: dict,
    vote_df: pd.DataFrame,
) -> go.Figure:
    if vote_df is None or vote_df.empty:
        return fig

    centroids_df = _build_centroids_dataframe(geojson_data)

    if centroids_df.empty:
        return fig

    vote_df = vote_df.copy()

    if "municipio_normalizado" not in vote_df.columns:
        return fig

    if "QT_VOTOS" not in vote_df.columns:
        vote_df["QT_VOTOS"] = 0

    if "Valor Pago" not in vote_df.columns:
        vote_df["Valor Pago"] = 0

    vote_df["municipio_normalizado"] = vote_df["municipio_normalizado"].apply(
        _normalize_text
    )

    vote_df["QT_VOTOS"] = pd.to_numeric(
        vote_df["QT_VOTOS"],
        errors="coerce",
    ).fillna(0)

    vote_df["Valor Pago"] = pd.to_numeric(
        vote_df["Valor Pago"],
        errors="coerce",
    ).fillna(0)

    vote_df = vote_df[vote_df["QT_VOTOS"] > 0].copy()

    if vote_df.empty:
        return fig

    vote_df = vote_df.merge(
        centroids_df,
        on="municipio_normalizado",
        how="left",
    )

    vote_df = vote_df.dropna(subset=["lat", "lon"]).copy()

    if vote_df.empty:
        return fig

    vote_df["votos_formatados"] = vote_df["QT_VOTOS"].apply(format_integer)
    vote_df["valor_pago_formatado"] = vote_df["Valor Pago"].apply(format_currency)

    customdata = vote_df[
        [
            "municipio_normalizado",
            "valor_pago_formatado",
            "votos_formatados",
        ]
    ].to_numpy()

    hovertemplate = (
        "<b>%{customdata[0]}</b><br><br>"
        "Emendas municipalizadas: %{customdata[1]}<br>"
        "Votos recebidos: %{customdata[2]}"
        "<extra></extra>"
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=vote_df["lat"],
            lon=vote_df["lon"],
            mode="markers",
            marker=dict(
                size=8,
                color="#1d4ed8",
                opacity=0.20,
            ),
            customdata=customdata,
            hovertemplate=hovertemplate,
            name="Contorno dos marcadores eleitorais",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=vote_df["lat"],
            lon=vote_df["lon"],
            mode="markers",
            marker=dict(
                size=5,
                color=vote_df["QT_VOTOS"],
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

    df_map = municipal_df.copy()

    if "municipio_normalizado" not in df_map.columns:
        df_map["municipio_normalizado"] = ""

    if "Valor Pago" not in df_map.columns:
        df_map["Valor Pago"] = 0

    df_map["municipio_normalizado"] = df_map["municipio_normalizado"].apply(
        _normalize_text
    )

    df_map["Valor Pago"] = pd.to_numeric(
        df_map["Valor Pago"],
        errors="coerce",
    ).fillna(0)

    df_map = df_map[
        (df_map["municipio_normalizado"] != "")
        & (df_map["Valor Pago"] > 0)
    ].copy()

    if vote_municipal_df is None:
        vote_municipal_df = df_map.copy()

    if df_map.empty:
        fig = _empty_map_figure()

        if show_vote_markers:
            fig = _add_vote_markers(
                fig=fig,
                geojson_data=geojson_matching,
                vote_df=vote_municipal_df,
            )

        return fig

    df_map["valor_pago_formatado"] = df_map["Valor Pago"].apply(format_currency)

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
        custom_data=["municipio_normalizado", "valor_pago_formatado"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br><br>"
            "Emendas municipalizadas: %{customdata[1]}"
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
        fig = _add_vote_markers(
            fig=fig,
            geojson_data=geojson_matching,
            vote_df=vote_municipal_df,
        )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )

    return fig
