"""
Top Navigation Bar Component.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_navbar() -> dbc.Navbar:
    """Creates the main top navigation bar with branding, mode switch, and refresh action."""
    return dbc.Navbar(
        dbc.Container([
            html.Div([
                html.I(className="bi bi-dna fs-2 text-primary me-3"),
                html.Div([
                    html.Div([
                        html.Span("HLS SA Bootcamp App", className="fw-bold text-primary fs-5 me-2"),
                        html.Span("—", className="text-muted fs-5 me-2"),
                        html.Span("Genomic Variant Store Explorer", className="fw-semibold text-dark fs-5"),
                    ]),
                    html.Small(
                        "Population-Scale Lakehouse & Clinical OMOP Discovery Platform (AWS Reference Solution)",
                        className="text-muted d-block"
                    )
                ])
            ], className="d-flex align-items-center mb-2 mb-xl-0"),
            dbc.Nav([
                html.Div([
                    dbc.Label("Execution Mode:", className="small text-muted me-2 mb-0 fw-semibold align-middle"),
                    dbc.Switch(
                        id="online-offline-switch",
                        value=True,
                        className="d-inline-block align-middle me-2",
                        style={"transform": "scale(1.1)", "cursor": "pointer"}
                    ),
                    html.Span(id="mode-status-badge", className="align-middle")
                ], className="d-flex align-items-center bg-light px-3 py-1 rounded border shadow-sm"),
                html.Div([
                    dbc.Button(
                        [html.I(className="bi bi-arrow-clockwise me-1"), "Refresh Data"],
                        id="global-refresh-btn",
                        color="primary",
                        size="sm",
                        className="fw-semibold shadow-sm me-2 text-nowrap"
                    ),
                    html.Span(id="last-refresh-timestamp", className="align-middle text-muted small text-nowrap")
                ], className="d-flex align-items-center bg-white px-2 py-1 rounded border shadow-sm"),
                dbc.Badge("AWS HLS Solution Bootcamp", color="primary", className="p-2 fs-7 shadow-sm text-nowrap"),
                dbc.Badge("OMOP CDM v5.4 & Lakehouse", color="secondary", className="p-2 fs-7 shadow-sm text-nowrap")
            ], className="ms-auto d-flex align-items-center flex-wrap gap-2")
        ], fluid=True),
        color="white",
        className="border-bottom shadow-sm mb-4 py-3"
    )
