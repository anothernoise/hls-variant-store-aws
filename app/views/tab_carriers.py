"""
Tab 2: Pathogenic Mutation Carrier Discovery View (APP rs63750066).
"""

from typing import Any, Dict
from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


def render_carriers_tab(
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

    return dbc.Card([
        dbc.CardHeader([
            html.Span("Pathogenic Mutation Carrier Discovery (APP rs63750066)", className="fw-bold text-danger me-2"),
            mode_badge,
            dbc.Badge(f"Engine: {engine}", color="danger", className="float-end")
        ], className="bg-white border-bottom py-3"),
        dbc.CardBody([
            html.P([
                "Target locus: ", html.Strong("chr21:25891796 A>G (APP Pathogenic Missense)"),
                " associated with Early-onset Alzheimer's disease. Queries executed against ",
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
    ], className="shadow-sm border-0")
