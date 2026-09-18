"""
Left Sidebar Navigation and Control Panel Component.
"""

from typing import List
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_sidebar(supported_engines: List[str]) -> html.Div:
    """Creates the left sidebar panel containing navigation views, engine selector, cohort context, and links."""
    return html.Div([
        # Navigation Card: Analytics & Discovery Views
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-compass me-2 text-primary"),
                html.Span("Analytics & Discovery", className="fw-bold")
            ], className="bg-light py-2"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="📊 1. Allele Frequency", tab_id="tab-af", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="🧬 2. Carrier Discovery", tab_id="tab-carriers", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="📈 3. Gene Burden Rollup", tab_id="tab-burden", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="🏥 4. OMOP Clinical Join", tab_id="tab-omop", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="⚡ 5. Latency Benchmarks", tab_id="tab-benchmarks", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="🔍 6. Store Data Explorer", tab_id="tab-raw", tab_style={"cursor": "pointer"}),
                    dbc.Tab(label="🩺 7. Engine Health", tab_id="tab-health", tab_style={"cursor": "pointer"}),
                ], id="tabs-main", active_tab="tab-af", className="nav-pills flex-column sidebar-nav-pills")
            ], className="p-2")
        ], className="shadow-sm mb-3 border-0"),

        # Control Card 1: Storage Engine Selection
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-hdd-network me-2 text-primary"),
                html.Span("Storage Architecture Tier", className="fw-bold")
            ], className="bg-light py-2"),

            dbc.CardBody([
                html.Div([
                    html.Label("Execution Mode:", className="form-label text-muted small fw-semibold mb-1"),
                    html.Div(id="sidebar-mode-indicator", className="mb-3")
                ]),
                html.Label("Active Storage Engine:", className="form-label text-muted small fw-semibold mb-2"),
                dcc.Dropdown(
                    id="engine-dropdown",
                    options=[{"label": e, "value": e} for e in supported_engines],
                    value="Amazon S3 Tables",
                    clearable=False,
                    className="shadow-sm mb-3"
                ),
                html.Div(id="telemetry-badge-container")
            ])
        ], className="shadow-sm mb-3 border-0"),

        # Control Card 2: Cohort & Reference Context
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-info-circle me-2 text-info"),
                html.Span("Cohort & Dataset Context", className="fw-bold")
            ], className="bg-light py-2"),
            dbc.CardBody([
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Small("Reference Coordinate:", className="text-muted d-block"),
                        html.Span("GRCh38 / hg38", className="fw-bold text-dark")
                    ], className="border-0 px-0 py-1"),
                    dbc.ListGroupItem([
                        html.Small("Cohort Size:", className="text-muted d-block"),
                        html.Span("10 WGS Samples (Additive Batches)", className="fw-bold text-dark")
                    ], className="border-0 px-0 py-1"),
                    dbc.ListGroupItem([
                        html.Small("Target Clinical Loci:", className="text-muted d-block"),
                        html.Span("APP (rs63750066), SOD1, BRCA1", className="fw-bold text-dark")
                    ], className="border-0 px-0 py-1"),
                    dbc.ListGroupItem([
                        html.Small("Phenotype Model:", className="text-muted d-block"),
                        html.Span("OMOP CDM v5.4 (Person, Condition)", className="fw-bold text-dark")
                    ], className="border-0 px-0 py-1"),
                ], flush=True)
            ])
        ], className="shadow-sm mb-3 border-0"),

        # Control Card 3: Architecture Reference Links
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-book me-2 text-success"),
                html.Span("Bootcamp Resources", className="fw-bold")
            ], className="bg-light py-2"),
            dbc.CardBody([
                html.Ul([
                    html.Li(html.A("Lab Exercises Guide (Ex 1–6)", href="https://github.com/anothernoise/hls-variant-store-aws/blob/main/docs/exercises.md", target="_blank", className="text-decoration-none small")),
                    html.Li(html.A("Architecture Decision Records (ADRs)", href="https://github.com/anothernoise/hls-variant-store-aws/tree/main/docs/adr", target="_blank", className="text-decoration-none small")),
                    html.Li(html.A("SA Matrix & Decision Tree", href="https://github.com/anothernoise/hls-variant-store-aws/blob/main/docs/summary.md", target="_blank", className="text-decoration-none small")),
                    html.Li(html.A("GitHub Repository", href="https://github.com/anothernoise/hls-variant-store-aws", target="_blank", className="text-decoration-none small")),
                ], className="list-unstyled mb-0")
            ])
        ], className="shadow-sm mb-3 border-0")
    ])
