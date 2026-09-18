"""
Tab 6: Store Data Explorer & Direct Table Inspection View.
"""

from typing import Any, Dict
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


def render_raw_tab_shell(engine: str, mode_badge: dbc.Badge) -> dbc.Card:
    """Renders the container shell for the Store Data Explorer tab."""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.Span("Store Data Explorer — Direct Table Inspection", className="fw-bold fs-5 me-2"),
                    dbc.Badge(f"Engine: {engine}", color="primary", className="p-2"),
                    mode_badge
                ], md=5, className="d-flex align-items-center mb-2 mb-md-0"),
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            html.Small("Dataset:", className="text-muted d-block fw-semibold"),
                            dcc.Dropdown(
                                id="raw-table-select",
                                options=[
                                    {"label": "🧬 Genomic Variants (variants)", "value": "variants"},
                                    {"label": "👤 OMOP Patients (person)", "value": "person"},
                                    {"label": "🏥 OMOP Diagnoses (condition_occurrence)", "value": "condition_occurrence"}
                                ],
                                value="variants",
                                clearable=False,
                                className="small shadow-sm"
                            )
                        ], md=5),
                        dbc.Col([
                            html.Small("Contig:", className="text-muted d-block fw-semibold"),
                            dcc.Dropdown(
                                id="raw-chrom-select",
                                options=[
                                    {"label": "All Contigs", "value": "All"},
                                    {"label": "chr1", "value": "chr1"},
                                    {"label": "chr21", "value": "chr21"}
                                ],
                                value="All",
                                clearable=False,
                                className="small shadow-sm"
                            )
                        ], md=3),
                        dbc.Col([
                            html.Small("Sample ID:", className="text-muted d-block fw-semibold"),
                            dcc.Dropdown(
                                id="raw-sample-select",
                                options=[{"label": "All Samples", "value": "All"}] + [
                                    {"label": f"sample_{i:03d}", "value": f"sample_{i:03d}"} for i in range(1, 11)
                                ],
                                value="All",
                                clearable=False,
                                className="small shadow-sm"
                            )
                        ], md=4),
                    ], className="g-2")
                ], md=7)
            ], align="center")
        ], className="bg-white border-bottom py-3"),
        dbc.CardBody([
            html.Div(id="raw-explorer-body")
        ])
    ], className="shadow-sm border-0")


def render_raw_explorer_body(
    df: pd.DataFrame,
    telemetry: Dict[str, Any],
    sql: str,
    meta: Dict[str, str],
    engine: str,
    table_name: str,
    offline: bool,
    mode_badge: dbc.Badge
) -> html.Div:
    """Renders the detailed interior of the raw explorer."""
    # 1. Physical Storage Architecture & Schema Card
    meta_badges = [
        dbc.Col([
            html.Small(k, className="text-muted d-block text-truncate fw-semibold"),
            html.Span(v, className="fw-bold small text-dark d-block text-truncate")
        ], md=3, className="mb-2")
        for k, v in meta.items()
    ]

    meta_card = dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-diagram-3 me-2 text-primary"),
            html.Span("Physical Storage Architecture & Schema Details", className="fw-bold")
        ], className="bg-light py-2"),
        dbc.CardBody([
            dbc.Row(meta_badges, className="g-2")
        ], className="py-2")
    ], className="mb-3 border")

    rows_count = telemetry.get("rows_retrieved", len(df))
    latency = telemetry.get("latency_ms", 0.0)
    scanned = telemetry.get("scanned_bytes", 0)
    table_label = telemetry.get("table", table_name or "variants")

    # 2. Executed Direct SQL Query Card
    sql_card = dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-terminal me-2 text-dark"),
            html.Span("Direct Engine SQL Execution Preview", className="fw-bold me-2"),
            mode_badge,
            dbc.Badge(f"Rows: {rows_count}", color="success", className="me-2 ms-2"),
            dbc.Badge(f"Engine Latency: {latency} ms", color="info", className="me-2"),
            dbc.Badge(f"Scanned: {scanned} bytes", color="secondary")
        ], className="bg-light py-2 d-flex align-items-center flex-wrap"),
        dbc.CardBody([
            html.Pre(
                sql,
                style={
                    "backgroundColor": "#1e1e1e",
                    "color": "#9cdcfe",
                    "padding": "12px",
                    "borderRadius": "6px",
                    "fontSize": "13px",
                    "marginBottom": "0",
                    "whiteSpace": "pre-wrap"
                }
            )
        ], className="p-2")
    ], className="mb-4 border")

    # 3. Interactive Data Table
    table_card = dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-table me-2 text-primary"),
            html.Span(f"Raw Records: {table_label}", className="fw-bold me-2"),
            dbc.Badge("OFFLINE MOCK DATA", color="warning", className="text-dark fw-bold me-2") if offline else dbc.Badge("LIVE AWS", color="success", className="me-2"),
            html.Small("(Supports in-table search, column sorting, and 1-click CSV export)", className="text-muted")
        ], className="bg-white border-bottom py-2 d-flex align-items-center flex-wrap"),
        dbc.CardBody([
            dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=10,
                sort_action="native",
                filter_action="native",
                export_format="csv",
                export_headers="display",
                style_table={"overflowX": "auto"},
                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "color": "#495057"},
                style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"},
                style_data_conditional=[
                    {
                        "if": {"column_id": "engine"},
                        "fontFamily": "monospace",
                        "fontWeight": "bold",
                        "color": "#0d6efd"
                    },
                    {
                        "if": {"column_id": "genotype"},
                        "fontFamily": "monospace",
                        "fontWeight": "bold",
                        "color": "#d63384"
                    },
                    {
                        "if": {"column_id": "start"},
                        "fontFamily": "monospace"
                    },
                    {
                        "if": {"column_id": "end"},
                        "fontFamily": "monospace"
                    }
                ]
            )
        ])
    ], className="shadow-sm border-0")

    mock_banner = (
        dbc.Alert([
            html.I(className="bi bi-laptop me-2 fs-5 align-middle text-warning"),
            html.Span([
                html.Strong("Offline Demo Mode (Synthetic Mock Simulation): "),
                f"Displaying local synthetic mock records with engine stamped as 'mock_data' for simulation of {engine}. Switch to 'Live AWS Mode (Online)' in the top navbar to query live AWS Cloud tables."
            ], className="align-middle")
        ], color="warning", className="d-flex align-items-center mb-3 shadow-sm border-0")
        if offline else None
    )

    components = [b for b in [mock_banner, meta_card, sql_card, table_card] if b is not None]
    return html.Div(components)
