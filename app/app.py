"""
HLS SA Bootcamp App — Genomic Variant Store Explorer
Interactive Population Genomics & Multimodal Clinical Discovery Platform.
Built with Plotly Dash & Dash Bootstrap Components.
"""

import os
import sys
import dash
from dash import html, dcc, dash_table, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Ensure app package can import backend
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend import VariantStoreBackend

# Initialize Dash App with modern FLATLY theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="HLS SA Bootcamp App — Genomic Variant Store Explorer",
    suppress_callback_exceptions=True
)

backend = VariantStoreBackend()

# -----------------------------------------------------------------------------
# Top Navigation Bar (Header & Branding)
# -----------------------------------------------------------------------------
navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(html.I(className="bi bi-dna fs-2 text-primary me-3"), width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("HLS SA Bootcamp App", className="fw-bold text-primary fs-4 me-2"),
                    html.Span("—", className="text-muted fs-4 me-2"),
                    html.Span("Genomic Variant Store Explorer", className="fw-semibold text-dark fs-4"),
                ]),
                html.Small(
                    "Population-Scale Lakehouse & Clinical OMOP Discovery Platform (AWS Reference Solution)",
                    className="text-muted"
                )
            ])
        ], align="center", className="g-0"),
        dbc.Nav([
            dbc.Badge("AWS HLS Solution Bootcamp", color="primary", className="p-2 fs-7 me-2 shadow-sm"),
            dbc.Badge("OMOP CDM v5.4 & Lakehouse", color="secondary", className="p-2 fs-7 shadow-sm")
        ], className="ms-auto d-none d-md-flex align-items-center")
    ], fluid=True),
    color="white",
    className="border-bottom shadow-sm mb-4 py-3"
)

# -----------------------------------------------------------------------------
# Left Sidebar Panel
# -----------------------------------------------------------------------------
sidebar = html.Div([
    # Control Card 1: Storage Engine Selection
    dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-hdd-network me-2 text-primary"),
            html.Span("Storage Architecture Tier", className="fw-bold")
        ], className="bg-light py-2"),
        dbc.CardBody([
            html.Label("Active Storage Engine:", className="form-label text-muted small fw-semibold mb-2"),
            dcc.Dropdown(
                id="engine-dropdown",
                options=[{"label": e, "value": e} for e in VariantStoreBackend.SUPPORTED_ENGINES],
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

# -----------------------------------------------------------------------------
# Main Content Area (Tabs + Dynamic Visualizations)
# -----------------------------------------------------------------------------
content = html.Div([
    dbc.Tabs([
        dbc.Tab(label="📊 1. Cohort Allele Frequency", tab_id="tab-af"),
        dbc.Tab(label="🧬 2. Pathogenic Carrier Discovery", tab_id="tab-carriers"),
        dbc.Tab(label="📈 3. Gene Burden Rollup", tab_id="tab-burden"),
        dbc.Tab(label="🏥 4. Multimodal OMOP Clinical Join", tab_id="tab-omop"),
        dbc.Tab(label="⚡ 5. Multi-Engine Latency Benchmarks", tab_id="tab-benchmarks"),
    ], id="tabs-main", active_tab="tab-af", className="mb-3 nav-fill border-bottom"),
    html.Div(id="tab-content", className="mb-4")
])

# -----------------------------------------------------------------------------
# App Layout
# -----------------------------------------------------------------------------
app.layout = dbc.Container([
    navbar,
    dbc.Row([
        dbc.Col(sidebar, md=4, lg=3, className="mb-4"),
        dbc.Col(content, md=8, lg=9, className="mb-4")
    ]),
    html.Footer([
        html.Hr(className="mt-4 mb-2"),
        html.P([
            "AWS Health & Life Sciences Solution Bootcamp — Reference Architecture Lab. ",
            html.Span("Synthetic data only — no real PHI/Genomic data committed.", className="text-muted")
        ], className="text-center text-muted small py-2")
    ])
], fluid=True, className="px-4 bg-light min-vh-100")


# -----------------------------------------------------------------------------
# Callback: Update Telemetry Badge
# -----------------------------------------------------------------------------
@callback(
    Output("telemetry-badge-container", "children"),
    Input("engine-dropdown", "value")
)
def update_telemetry_badge(engine):
    metrics = {
        "Amazon S3 Tables": ("Sub-second (~800ms)", "Zero-Ops Compaction", "Low ($0.023/GB)", "success"),
        "Custom S3 + Iceberg": ("Sub-second (~890ms)", "Partition Pruned", "Low ($0.023/GB)", "info"),
        "Delta Lake on S3": ("Sub-second (~850ms)", "ACID Transaction Log", "Medium", "primary"),
        "Hail VDS (Spark)": ("Batch (~1.2s)", "Sparse MatrixTable", "Medium-High", "warning"),
        "Amazon Aurora PostgreSQL (Serverless v2)": ("Real-time (<50ms)", "B-tree Seek + GIN JSONB", "Auto-scaling ACU", "danger"),
        "Amazon RDS PostgreSQL": ("Real-time (<75ms)", "db.t4g Fixed Instance", "Fixed Dev Cost", "secondary"),
        "AWS HealthOmics Variant Store": ("Analytical (~900ms)", "Managed VCF Lakehouse", "Higher ($0.04/GB)", "primary"),
    }.get(engine, ("~800ms", "Standard", "Medium", "info"))

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Small("Query Latency SLA:", className="text-muted d-block"),
                dbc.Badge(metrics[0], color=metrics[3], className="p-1 px-2 mb-2")
            ]),
            html.Div([
                html.Small("Storage Architecture:", className="text-muted d-block"),
                html.Span(metrics[1], className="fw-bold small text-dark d-block mb-1")
            ]),
            html.Div([
                html.Small("Cost Profile:", className="text-muted d-block"),
                html.Span(metrics[2], className="badge bg-light text-dark border")
            ])
        ], className="p-2")
    ], className="bg-light border")


# -----------------------------------------------------------------------------
# Callback: Render Main Tabs
# -----------------------------------------------------------------------------
@callback(
    Output("tab-content", "children"),
    [Input("tabs-main", "active_tab"),
     Input("engine-dropdown", "value")]
)
def render_tab_content(active_tab, engine):
    if active_tab == "tab-af":
        df, meta = backend.get_allele_frequencies(engine)
        fig = px.bar(
            df,
            x="start",
            y="carrier_frequency" if "carrier_frequency" in df else "af",
            color="gene_symbol" if "gene_symbol" in df else "gene",
            title=f"Cohort Allele Frequency Distribution — Engine: {engine}",
            labels={"start": "Genomic Coordinate (Start)", "carrier_frequency": "Carrier Frequency"},
            hover_data=["clinical_significance"] if "clinical_significance" in df else None,
            template="plotly_white"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        return dbc.Card([
            dbc.CardHeader([
                html.Span("Cohort Allele Frequency & Annotation Overview", className="fw-bold me-2"),
                dbc.Badge(f"Engine: {engine}", color="primary", className="float-end")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                dcc.Graph(figure=fig, className="mb-4"),
                html.H6("Tabular Variant Frequency Records", className="fw-bold text-muted mb-2"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "color": "#495057"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"}
                )
            ])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-carriers":
        df, meta = backend.get_pathogenic_carriers(engine)
        return dbc.Card([
            dbc.CardHeader([
                html.Span("Pathogenic Mutation Carrier Discovery (APP rs63750066)", className="fw-bold text-danger me-2"),
                dbc.Badge(f"Engine: {engine}", color="danger", className="float-end")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                html.P([
                    "Target locus: ", html.Strong("chr21:25891796 A>G (APP Pathogenic Missense)"),
                    " associated with Early-onset Alzheimer's disease. Queries executed against ",
                    dbc.Badge(engine, color="primary")
                ], className="text-muted small mb-3"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#fce8e6", "color": "#c5221f", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "12px", "fontSize": "13px"}
                )
            ])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-burden":
        df, meta = backend.get_gene_burden(engine)
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
                dbc.Badge(f"Engine: {engine}", color="info", className="float-end")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                dcc.Graph(figure=fig, className="mb-4"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"}
                )
            ])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-omop":
        df, meta = backend.get_omop_phenotype_join(engine)
        return dbc.Card([
            dbc.CardHeader([
                html.Span("Multimodal Genotype ↔ OMOP CDM Phenotype Federation", className="fw-bold text-success me-2"),
                dbc.Badge(f"Engine: {engine}", color="success", className="float-end")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                html.P("In-place federated join between genomic variant calls and OMOP clinical person/condition tables:", className="text-muted small mb-3"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#e6f4ea", "color": "#137333", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"}
                )
            ])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-benchmarks":
        bench_df = pd.DataFrame([
            {"Engine": "Amazon S3 Tables", "Carrier Lookup (ms)": 385, "Allele Freq (ms)": 462, "OMOP Join (ms)": 682, "Cost/Query": "$0.000063"},
            {"Engine": "Custom S3 + Iceberg", "Carrier Lookup (ms)": 451, "Allele Freq (ms)": 528, "OMOP Join (ms)": 781, "Cost/Query": "$0.000063"},
            {"Engine": "Delta Lake on S3", "Carrier Lookup (ms)": 418, "Allele Freq (ms)": 495, "OMOP Join (ms)": 726, "Cost/Query": "$0.000063"},
            {"Engine": "Aurora PostgreSQL Serverless", "Carrier Lookup (ms)": 49, "Allele Freq (ms)": 418, "OMOP Join (ms)": 93, "Cost/Query": "$0.000010"},
            {"Engine": "RDS PostgreSQL (t4g)", "Carrier Lookup (ms)": 71, "Allele Freq (ms)": 572, "OMOP Join (ms)": 143, "Cost/Query": "$0.000010"},
            {"Engine": "Hail VDS (Spark)", "Carrier Lookup (ms)": 1078, "Allele Freq (ms)": 1375, "OMOP Join (ms)": 2310, "Cost/Query": "$0.000079"},
            {"Engine": "AWS HealthOmics", "Carrier Lookup (ms)": 480, "Allele Freq (ms)": 590, "OMOP Join (ms)": 890, "Cost/Query": "$0.000085"},
        ])
        fig = px.bar(
            bench_df,
            x="Engine",
            y=["Carrier Lookup (ms)", "Allele Freq (ms)", "OMOP Join (ms)"],
            barmode="group",
            title="Multi-Engine Latency Comparison Across Core Queries",
            template="plotly_white"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        return dbc.Card([
            dbc.CardHeader([
                html.Span("Multi-Engine Query Latency & Cost Comparison", className="fw-bold me-2"),
                dbc.Badge("Comprehensive Benchmark", color="dark", className="float-end")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                dcc.Graph(figure=fig, className="mb-4"),
                dash_table.DataTable(
                    data=bench_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in bench_df.columns],
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "13px"}
                )
            ])
        ], className="shadow-sm border-0")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)

