import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import shape

from config import MAPA_COR_GRADIENTE
from utils.format_utils import format_currency, format_integer


def _build_centroids_dataframe(geojson_data: dict) -> pd.DataFrame:
    """Cria latitude e longitude aproximadas para cada município do GeoJSON."""
    rows = []

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        geometry_data = feature.get("geometry")

        if not geometry_data:
            continue

        geom = shape(geometry_data)
        point = geom.representative_point()

        municipio = (
            properties.get("name")
            or properties.get("NOME")
            or properties.get("NM_MUN")
            or properties.get("municipio_normalizado")
        )

        if municipio:
            rows.append(
                {
                    "municipio_normalizado": municipio,
                    "lat": point.y,
                    "lon": point.x,
                }
            )

    return pd.DataFrame(rows)


def _format_colorbar_value(value: float) -> str:
    """Formata valores da barra de cores do mapa no padrão brasileiro."""
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f} mi".replace(".", ",")

    return f"R$ {int(value / 1_000)} mil"


def _build_colorbar_ticks(values: pd.Series) -> tuple[list[float], list[str]]:
    """Cria marcações dinâmicas para a barra de cores do mapa."""
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


def _add_vote_markers(
    fig: go.Figure,
    geojson_data: dict,
    municipal_df: pd.DataFrame,
) -> go.Figure:
    """Adiciona marcadores eleitorais para todos os municípios."""
    centroids_df = _build_centroids_dataframe(geojson_data)

    vote_df = municipal_df.merge(
        centroids_df,
        on="municipio_normalizado",
        how="left",
    )

    vote_df = vote_df.dropna(subset=["lat", "lon", "QT_VOTOS"]).copy()

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
        "Emendas destinadas: %{customdata[1]}<br>"
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
    show_vote_markers: bool = True,
) -> go.Figure:
    """Cria mapa coroplético de emendas com marcadores eleitorais."""
    df_map = municipal_df.copy()
    df_map["valor_pago_formatado"] = df_map["Valor Pago"].apply(format_currency)

    tickvals, ticktext = _build_colorbar_ticks(df_map["Valor Pago"])

    fig = px.choropleth_mapbox(
        df_map,
        geojson=geojson_data,
        locations="municipio_normalizado",
        featureidkey="properties.name",
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
            "Emendas destinadas: %{customdata[1]}"
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
            geojson_data=geojson_data,
            municipal_df=municipal_df,
        )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )

    return fig