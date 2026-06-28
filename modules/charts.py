import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.styles import get_ips_color_map, get_ips_order


def format_millions_br(value: float) -> str:
    """Formata valores em milhões no padrão brasileiro."""
    value_millions = value / 1_000_000
    return f"R$ {value_millions:.1f} milhões".replace(".", ",")


def build_ips_bar_chart(ips_df: pd.DataFrame) -> go.Figure:
    """Cria gráfico compacto de barras horizontais para distribuição de emendas por IPS."""
    ips_df = ips_df.copy()

    ips_df["faixa_prioridade"] = pd.Categorical(
        ips_df["faixa_prioridade"],
        categories=get_ips_order(),
        ordered=True,
    )

    ips_df = ips_df.sort_values("faixa_prioridade")
    ips_df["valor_formatado"] = ips_df["Valor Pago"].apply(format_millions_br)

    fig = px.bar(
        ips_df,
        x="Valor Pago",
        y="faixa_prioridade",
        orientation="h",
        color="faixa_prioridade",
        color_discrete_map=get_ips_color_map(),
        text="valor_formatado",
        custom_data=["faixa_prioridade", "valor_formatado"],
    )

    fig.update_traces(
        width=0.45,
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br><br>"
            "Valor destinado: %{customdata[1]}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=230,
        xaxis_title=None,
        yaxis_title=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=13),
        showlegend=False,
        margin=dict(l=10, r=90, t=0, b=0),
        bargap=0.35,
    )

    fig.update_xaxes(
        visible=False,
        showgrid=False,
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=False,
        categoryorder="array",
        categoryarray=get_ips_order(),
    )

    return fig