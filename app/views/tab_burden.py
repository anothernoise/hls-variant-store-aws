"""
Tab 3: Gene Burden Rollup Analysis View.
"""

from typing import Any, Dict
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd


def render_burden_tab(
    df: pd.DataFrame,
    meta: Dict[str, Any],
    engine: str,
    offline: bool,
    mode_badge: dbc.Badge,
    engine_id: str
) -> dbc.Card:
    if meta.get("error"):
        return dbc.Alert([
            html.H5(f"Engine Status: {meta.get('status', 'Unavailable')}", className="alert-heading"),
            html.P(meta["error"]),
            html.Hr(),
            html.Small("Switch to 'Offline Demo Mode' in the navbar to test this engine with synthetic simulation.")
        ], color="warning", className="shadow-sm border-0")

    if not df.empty:
        if "engine" not in df.columns:
            df["engine"] = "mock_data" if offline else engine_id
        cols = ["engine"] + [c for c in df.columns if c != "engine"]
        df = df[cols]

    fig = px.bar(
        df,
        x="sample_id",
        y="total_alt_allele_burden",
        color="sample_id",
        title=f"Sample-Level Mutation Burden for APP Locus — Engine: {engine}",
        labels={"sample_id": "Cohort Sample ID", "total_alt_allele_burden": "Total Alternate Burden"},
        template="plotly_white"
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return dbc.Card([
        dbc.CardHeader([
            html.Span("Gene Burden Rollup Analysis", className="fw-bold me-2"),
            mode_badge,
            dbc.Badge(f"Engine: {engine}", color="info", className="float-end")
        ], className="bg-white border-bottom py-3"),
        dbc.CardBody([
            dcc.Graph(figure=fig, className="mb-4"),
            dash_table.DataTable(
                id=f"burden-table-{engine.lower().replace(' ', '_')}",
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=6,
                style_table={"overflowX": "auto"},
                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"},
                style_data_conditional=[
                    {
                        "if": {"column_id": "engine"},
                        "fontFamily": "monospace",
                        "fontWeight": "bold",
                        "color": "#0d6efd"
                    }
                ]
            )
        ])
    ], className="shadow-sm border-0")
