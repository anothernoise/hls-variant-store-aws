"""
Tab 2: Pathogenic Mutation Carrier Discovery View (APP rs63750066).
"""

from typing import Any, Dict
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


def render_carriers_body(
    df: pd.DataFrame,
    engine: str,
    current_gene: str = "APP"
) -> html.Div:
    gene_details = {
        "APP": "chr21:25891796 A>G (Early-Onset Alzheimer's Disease Missense)",
        "SOD1": "chr21:31659700 G>A (Amyotrophic Lateral Sclerosis / ALS)",
        "BRCA1": "chr17:43044295 C>T (Hereditary Breast & Ovarian Cancer)"
    }
    desc = gene_details.get(current_gene, f"{current_gene} Pathogenic Locus")

    return html.Div([
        html.P([
            "Target locus: ", html.Strong(desc),
            ". Point lookup queries executed across ",
            dbc.Badge(engine, color="primary")
        ], className="text-muted small mb-3"),
        dash_table.DataTable(
            id=f"carriers-table-{engine.lower().replace(' ', '_')}",
            data=df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            page_size=6,
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "#fce8e6", "color": "#c5221f", "fontWeight": "bold"},
            style_cell={"textAlign": "left", "padding": "12px", "fontSize": "13px"},
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


def render_carriers_tab(
    df: pd.DataFrame,
    meta: Dict[str, Any],
    engine: str,
    offline: bool,
    mode_badge: dbc.Badge,
    engine_id: str,
    current_gene: str = "APP"
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

    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.Span("Pathogenic Mutation Carrier Discovery", className="fw-bold text-danger me-2 fs-5"),
                    mode_badge
                ], lg=6, md=12, className="d-flex align-items-center mb-2 mb-lg-0"),
                dbc.Col([
                    html.Div([
                        html.Label("Target Gene:", className="small text-muted fw-bold me-2 mb-0 align-middle"),
                        html.Div([
                            dcc.Dropdown(
                                id="carrier-gene-select",
                                options=[
                                    {"label": "🧬 APP (Alzheimer's)", "value": "APP"},
                                    {"label": "🧬 SOD1 (ALS)", "value": "SOD1"},
                                    {"label": "🧬 BRCA1 (Cancer)", "value": "BRCA1"}
                                ],
                                value=current_gene,
                                clearable=False,
                                className="small"
                            )
                        ], style={"width": "190px"}),
                        dbc.Badge(f"Engine: {engine}", color="danger", className="p-2 ms-2")
                    ], className="d-flex align-items-center justify-content-lg-end justify-content-start flex-wrap gap-1")
                ], lg=6, md=12)
            ], className="align-items-center")
        ], className="bg-white border-bottom py-3"),
        dbc.CardBody([
            html.Div(
                id="carriers-body-container",
                children=render_carriers_body(df, engine, current_gene)
            )
        ])
    ], className="shadow-sm border-0")
