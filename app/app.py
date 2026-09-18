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
from api_client import VariantStoreApiClient

# Initialize Dash App with modern FLATLY theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="HLS SA Bootcamp App — Genomic Variant Store Explorer",
    suppress_callback_exceptions=True
)

backend = VariantStoreBackend()
api_client = VariantStoreApiClient()

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
            html.Div([
                dbc.Label("Execution Mode:", className="small text-muted me-2 mb-0 fw-semibold align-middle"),
                dbc.Switch(
                    id="online-offline-switch",
                    value=True,
                    className="d-inline-block align-middle me-2",
                    style={"transform": "scale(1.2)", "cursor": "pointer"}
                ),
                html.Span(id="mode-status-badge", className="align-middle")
            ], className="d-flex align-items-center bg-light px-3 py-1 rounded border shadow-sm me-3"),
            dbc.Badge("AWS HLS Solution Bootcamp", color="primary", className="p-2 fs-7 me-2 shadow-sm"),
            dbc.Badge("OMOP CDM v5.4 & Lakehouse", color="secondary", className="p-2 fs-7 shadow-sm")
        ], className="ms-auto d-flex align-items-center flex-wrap")
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
            html.Div([
                html.Label("Execution Mode:", className="form-label text-muted small fw-semibold mb-1"),
                html.Div(id="sidebar-mode-indicator", className="mb-3")
            ]),
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
        dbc.Tab(label="🔍 6. Store Data Explorer", tab_id="tab-raw"),
        dbc.Tab(label="🩺 7. Engine Health & Status", tab_id="tab-health"),
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
# Callback: Mode Status Indicator (Navbar & Sidebar)
# -----------------------------------------------------------------------------
@callback(
    [Output("mode-status-badge", "children"),
     Output("sidebar-mode-indicator", "children")],
    Input("online-offline-switch", "value")
)
def update_mode_status_badge(is_online):
    if is_online:
        nav_badge = dbc.Badge(
            [html.I(className="bi bi-cloud-check-fill me-1"), "Live AWS Mode (Online)"],
            color="success",
            className="p-2 fs-7 shadow-sm"
        )
        sidebar_badge = dbc.Badge(
            [html.I(className="bi bi-cloud-arrow-up-fill me-1"), "Online: Live AWS Athena & S3 Tables"],
            color="success",
            className="w-100 py-2 text-center shadow-sm"
        )
    else:
        nav_badge = dbc.Badge(
            [html.I(className="bi bi-laptop me-1"), "Offline Demo Mode"],
            color="warning",
            className="p-2 fs-7 text-dark shadow-sm"
        )
        sidebar_badge = dbc.Badge(
            [html.I(className="bi bi-laptop me-1"), "Offline: Local Synthetic Simulation"],
            color="warning",
            className="w-100 py-2 text-center text-dark shadow-sm"
        )
    return nav_badge, sidebar_badge


# -----------------------------------------------------------------------------
# Callback: Update Telemetry Badge
# -----------------------------------------------------------------------------
@callback(
    Output("telemetry-badge-container", "children"),
    [Input("engine-dropdown", "value"),
     Input("online-offline-switch", "value")]
)
def update_telemetry_badge(engine, is_online):
    health = api_client.get_engine_health(engine, offline=not is_online)
    h_status = health.get("status", "pass")
    h_dep = health.get("deployment_status", "ACTIVE")
    if h_status == "pass":
        health_badge = dbc.Badge([html.I(className="bi bi-check-circle-fill me-1"), f"Health: {h_dep}"], color="success", className="p-1 px-2 mb-2")
    elif h_status == "warn":
        health_badge = dbc.Badge([html.I(className="bi bi-exclamation-triangle-fill me-1"), f"Health: {h_dep}"], color="warning", className="p-1 px-2 mb-2 text-dark")
    else:
        health_badge = dbc.Badge([html.I(className="bi bi-x-octagon-fill me-1"), f"Health: {h_dep}"], color="danger", className="p-1 px-2 mb-2")

    if not is_online:
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Small("Engine Health Status:", className="text-muted d-block"),
                    health_badge
                ]),
                html.Div([
                    html.Small("Query Latency SLA:", className="text-muted d-block"),
                    dbc.Badge("Instant (~18ms)", color="warning", className="p-1 px-2 mb-2 text-dark")
                ]),
                html.Div([
                    html.Small("Storage Architecture:", className="text-muted d-block"),
                    html.Span("Local Synthetic Simulation (Offline)", className="fw-bold small text-dark d-block mb-1")
                ]),
                html.Div([
                    html.Small("Cost Profile:", className="text-muted d-block"),
                    html.Span("$0.00 / query (Air-gapped Demo)", className="badge bg-light text-dark border")
                ])
            ], className="p-2")
        ], className="bg-light border")

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
                html.Small("Engine Health Status:", className="text-muted d-block"),
                health_badge
            ]),
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
     Input("engine-dropdown", "value"),
     Input("online-offline-switch", "value")]
)
def render_tab_content(active_tab, engine, is_online):
    offline = not is_online
    mode_badge = (
        dbc.Badge([html.I(className="bi bi-cloud-check-fill me-1"), "Live AWS"], color="success", className="ms-2")
        if is_online else
        dbc.Badge([html.I(className="bi bi-laptop me-1"), "Offline Sim"], color="warning", className="ms-2 text-dark")
    )

    if active_tab == "tab-af":
        df, meta = api_client.get_allele_frequencies(engine, offline=offline)
        if meta.get("error"):
            return dbc.Alert([
                html.H5(f"Engine Status: {meta.get('status', 'Unavailable')}", className="alert-heading"),
                html.P(meta["error"]),
                html.Hr(),
                html.Small("Switch to 'Offline Demo Mode' in the navbar to test this engine with synthetic simulation.")
            ], color="warning", className="shadow-sm border-0")

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
                mode_badge,
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
        df, meta = api_client.get_pathogenic_carriers(engine, offline=offline)
        if meta.get("error"):
            return dbc.Alert([
                html.H5(f"Engine Status: {meta.get('status', 'Unavailable')}", className="alert-heading"),
                html.P(meta["error"]),
                html.Hr(),
                html.Small("Switch to 'Offline Demo Mode' in the navbar to test this engine with synthetic simulation.")
            ], color="warning", className="shadow-sm border-0")

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
        df, meta = api_client.get_gene_burden(engine, offline=offline)
        if meta.get("error"):
            return dbc.Alert([
                html.H5(f"Engine Status: {meta.get('status', 'Unavailable')}", className="alert-heading"),
                html.P(meta["error"]),
                html.Hr(),
                html.Small("Switch to 'Offline Demo Mode' in the navbar to test this engine with synthetic simulation.")
            ], color="warning", className="shadow-sm border-0")

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
        df, meta = api_client.get_omop_phenotype_join(engine, offline=offline)
        if meta.get("error"):
            return dbc.Alert([
                html.H5(f"Engine Status: {meta.get('status', 'Unavailable')}", className="alert-heading"),
                html.P(meta["error"]),
                html.Hr(),
                html.Small("Switch to 'Offline Demo Mode' in the navbar to test this engine with synthetic simulation.")
            ], color="warning", className="shadow-sm border-0")

        return dbc.Card([
            dbc.CardHeader([
                html.Span("Multimodal Genotype ↔ OMOP CDM Phenotype Federation", className="fw-bold text-success me-2"),
                mode_badge,
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
        bench_data = api_client.get_benchmarks()
        if bench_data:
            bench_df = pd.DataFrame(bench_data).rename(columns={
                "engine": "Engine",
                "carrier_lookup_ms": "Carrier Lookup (ms)",
                "allele_freq_ms": "Allele Freq (ms)",
                "omop_join_ms": "OMOP Join (ms)",
                "cost_per_query": "Cost/Query"
            })
        else:
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

    elif active_tab == "tab-raw":
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

    elif active_tab == "tab-health":
        summary = api_client.get_all_engines_health(offline=offline)
        cluster_status = summary.get("status", "healthy").upper()
        total_engines = summary.get("total_engines", 7)
        active_count = summary.get("active_engines", 6)
        not_deployed_count = summary.get("not_deployed_engines", 1)
        probe_latency = summary.get("probe_latency_ms", 0.0)
        engines_dict = summary.get("engines", {})

        status_color = "success" if cluster_status == "HEALTHY" else "warning"

        return dbc.Card([
            dbc.CardHeader([
                html.Span("AWS Genomic Storage Engines — Cluster Health & Readiness", className="fw-bold me-2"),
                mode_badge,
                dbc.Badge(f"Cluster: {cluster_status}", color=status_color, className="float-end p-2")
            ], className="bg-white border-bottom py-3"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Small("Cluster Overall Status", className="text-muted d-block fw-semibold"),
                            html.H4(cluster_status, className=f"text-{status_color} fw-bold mb-0")
                        ], className="p-3 bg-light rounded border text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Small("Active / Available Engines", className="text-muted d-block fw-semibold"),
                            html.H4(f"{active_count} / {total_engines}", className="text-success fw-bold mb-0")
                        ], className="p-3 bg-light rounded border text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Small("Not Deployed Engines", className="text-muted d-block fw-semibold"),
                            html.H4(f"{not_deployed_count}", className="text-warning fw-bold mb-0")
                        ], className="p-3 bg-light rounded border text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Small("Total Probe Duration", className="text-muted d-block fw-semibold"),
                            html.H4(f"{probe_latency} ms", className="text-primary fw-bold mb-0")
                        ], className="p-3 bg-light rounded border text-center")
                    ], md=3),
                ], className="g-3 mb-4"),

                html.H6("Detailed Engine Subsystem Probes (IETF RFC Health Specification)", className="fw-bold text-dark mb-3"),
                dash_table.DataTable(
                    data=[
                        {
                            "Engine": h.get("engine_name"),
                            "Status": h.get("status", "").upper(),
                            "Deployment": h.get("deployment_status"),
                            "Target Resource": h.get("target_resource"),
                            "Latency (ms)": h.get("latency_ms"),
                            "Storage Volume": h.get("checks", {}).get("storage_layer", {}).get("status", "N/A").upper(),
                            "Catalog Schema": h.get("checks", {}).get("catalog_metadata", {}).get("status", "N/A").upper(),
                            "Query Layer": h.get("checks", {}).get("query_interface", {}).get("status", "N/A").upper(),
                        }
                        for h in engines_dict.values()
                    ],
                    columns=[
                        {"name": "Engine", "id": "Engine"},
                        {"name": "Status", "id": "Status"},
                        {"name": "Deployment", "id": "Deployment"},
                        {"name": "Target Resource", "id": "Target Resource"},
                        {"name": "Latency (ms)", "id": "Latency (ms)"},
                        {"name": "Storage Volume", "id": "Storage Volume"},
                        {"name": "Catalog Schema", "id": "Catalog Schema"},
                        {"name": "Query Layer", "id": "Query Layer"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "color": "#495057"},
                    style_cell={"textAlign": "left", "padding": "12px", "fontSize": "13px"},
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{Status} = 'PASS'"},
                            "backgroundColor": "#e6f4ea",
                            "color": "#137333",
                            "fontWeight": "bold"
                        },
                        {
                            "if": {"filter_query": "{Status} = 'WARN'"},
                            "backgroundColor": "#fef7e0",
                            "color": "#b06000",
                            "fontWeight": "bold"
                        }
                    ]
                )
            ])
        ], className="shadow-sm border-0")


# -----------------------------------------------------------------------------
# Callback: Update Raw Store Data Explorer Body
# -----------------------------------------------------------------------------
@callback(
    Output("raw-explorer-body", "children"),
    [Input("engine-dropdown", "value"),
     Input("raw-table-select", "value"),
     Input("raw-chrom-select", "value"),
     Input("raw-sample-select", "value"),
     Input("online-offline-switch", "value")]
)
def update_raw_explorer_body(engine, table_name, chromosome, sample_id, is_online):
    offline = not is_online
    meta = backend.get_store_metadata(engine)
    df, telemetry, sql = api_client.get_raw_store_data(
        engine=engine,
        table_name=table_name or "variants",
        chromosome=chromosome or "All",
        sample_id=sample_id or "All",
        offline=offline
    )

    mode_badge = (
        dbc.Badge([html.I(className="bi bi-cloud-check-fill me-1"), "Live AWS"], color="success", className="ms-2")
        if is_online else
        dbc.Badge([html.I(className="bi bi-laptop me-1"), "Offline Sim"], color="warning", className="ms-2 text-dark")
    )

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

    # 2. Executed Direct SQL Query Card
    sql_card = dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-terminal me-2 text-dark"),
            html.Span("Direct Engine SQL Execution Preview", className="fw-bold me-2"),
            mode_badge,
            dbc.Badge(f"Rows: {telemetry['rows_retrieved']}", color="success", className="me-2 ms-2"),
            dbc.Badge(f"Engine Latency: {telemetry['latency_ms']} ms", color="info", className="me-2"),
            dbc.Badge(f"Scanned: {telemetry['scanned_bytes']} bytes", color="secondary")
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
            html.Span(f"Raw Records: {telemetry['table']}", className="fw-bold me-2"),
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)

