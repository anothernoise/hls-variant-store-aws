"""
Tab 1: Cohort Allele Frequency & Annotation Overview View.
"""

from typing import Any, Dict
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd


def render_af_tab(
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

    col_display = {
        "engine": "⚙️ Storage Engine",
        "gene_symbol": "🧬 Gene",
        "reference_name": "Contig",
        "start": "Pos (Start)",
        "reference_bases": "Ref",
        "alternate_bases": "Alt",
        "carrier_frequency": "Carrier Freq",
        "total_cohort_samples": "Cohort N",
        "alt_carrier_count": "Alt Carriers",
        "clinical_significance": "Significance"
    }

    hover_cols = [c for c in ["clinical_significance", "engine"] if c in df.columns]
    fig = px.bar(
        df,
        x="start",
        y="carrier_frequency" if "carrier_frequency" in df else "af",
        color="gene_symbol" if "gene_symbol" in df else "gene",
        title=f"Cohort Allele Frequency Distribution — Engine: {engine}",
        labels={"start": "Genomic Coordinate (Start)", "carrier_frequency": "Carrier Frequency"},
        hover_data=hover_cols if hover_cols else None,
        template="plotly_white"
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return dbc.Card([
        dbc.CardHeader([
            html.Span("Cohort Allele Frequency & Annotation Overview", className="fw-bold me-2"),
            mode_badge,
            dbc.Badge(f"Latency: {meta.get('latency_ms', 0)} ms", color="info", className="ms-2 me-2"),
            dbc.Badge(f"Target DB: {meta.get('target_database', 'default')}", color="secondary", className="me-2"),
            dbc.Badge(f"Engine: {engine}", color="primary", className="float-end p-2")
        ], className="bg-white border-bottom py-3 d-flex align-items-center flex-wrap"),
        dbc.CardBody([
            dcc.Graph(figure=fig, className="mb-4"),
            html.H6("Tabular Variant Frequency Records", className="fw-bold text-muted mb-2"),
            dash_table.DataTable(
                id=f"af-table-{engine.lower().replace(' ', '_')}",
                data=df.to_dict("records"),
                columns=[{"name": col_display.get(c, c), "id": c} for c in df.columns],
                page_size=6,
                style_table={"overflowX": "auto", "minWidth": "100%"},
                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "color": "#495057"},
                style_header_conditional=[
                    {
                        "if": {"column_id": "engine"},
                        "backgroundColor": "#e7f1ff",
                        "color": "#0d6efd",
                        "fontWeight": "bold"
                    }
                ],
                style_cell={"textAlign": "left", "padding": "12px 10px", "fontSize": "13px"},
                style_data_conditional=[
                    {
                        "if": {"column_id": "engine"},
                        "fontFamily": "monospace",
                        "fontWeight": "bold",
                        "backgroundColor": "#f8faff",
                        "color": "#0d6efd"
                    },
                    {
                        "if": {"column_id": "carrier_frequency"},
                        "fontWeight": "bold",
                        "color": "#198754"
                    }
                ]
            )
        ])
    ], className="shadow-sm border-0")
