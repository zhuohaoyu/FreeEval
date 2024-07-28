import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any

def create_dashboard_layout(plots: List[go.Figure], summary_stats: Dict[str, Any]) -> go.Figure:
    n_plots = len(plots)
    fig = make_subplots(rows=n_plots, cols=1, subplot_titles=[p.layout.title.text for p in plots])
    
    for i, plot in enumerate(plots, start=1):
        for trace in plot.data:
            fig.add_trace(trace, row=i, col=1)
    
    # Add summary stats as annotations
    annotation_text = "<br>".join([f"{k}: {v}" for k, v in summary_stats.items()])
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.98, y=1.05,
        text=annotation_text,
        showarrow=False,
        font=dict(size=12),
        align="right",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1,
    )
    
    fig.update_layout(height=300 * n_plots, title_text="Evaluation Dashboard")
    return fig

def create_case_study_plot(case_data: Dict[str, Any]) -> go.Figure:
    fig = go.Figure()

    # Add text boxes for each field in the case data
    for i, (key, value) in enumerate(case_data.items()):
        fig.add_annotation(
            x=0,
            y=1 - i * 0.1,
            xref="paper",
            yref="paper",
            text=f"<b>{key}:</b> {value}",
            showarrow=False,
            font=dict(size=12),
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1,
        )

    fig.update_layout(
        height=100 * len(case_data),
        title_text="Case Study Details",
        showlegend=False,
    )

    return fig