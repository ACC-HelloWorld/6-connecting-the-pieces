import plotly.graph_objects as go


def to_plotly(axplotconfig):
    """Converts AxPlotConfig to plotly Figure."""
    data = axplotconfig[0]["data"]
    layout = axplotconfig[0]["layout"]
    fig = go.Figure({"data": data, "layout": layout})
    return fig
