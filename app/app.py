"""
Interactive Genomic Variant Store Explorer Web Application.
Built with Plotly Dash & Dash Bootstrap Components.
Enables dynamic switching across 7 storage engines with live clinical genetics visualizations.
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

# Initialize Dash App with modern Darkly / Flatly theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="AWS Genomic Variant Store Explorer",
    suppress_callback_exceptions=True
)

backend = VariantStoreBackend()

# App Header Component
navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            dbc.Row([
                dbc.Col(html.I(className="bi bi-dna fs-2 text-primary me-2")),
                dbc.Col([
                    html.H4("AWS Genomic Variant Store Explorer", className="mb-0 text-primary fw-bold"),
                    html.Small("Population-Scale Lakehouse & Clinical OMOP Discovery Platform", className="text-muted")
                ])
            ], align="center", className="g-0"),
            style={"textDecoration": "none"}
        ),
        dbc.Badge("AWS Well-Architected HLS Lab", color="info", className="p-2 fs-6")
    ], fluid=True),
    color="light",
    className="border-bottom shadow-sm mb-4 py-3"
)

# Engine Selector Card
engine_selector = dbc.Card([
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Label([html.I(className="bi bi-hdd-network me-2"), "Select Storage Engine / Architecture Tier:"], className="fw-bold mb-2"),
                dcc.Dropdown(
                    id="engine-dropdown",
                    options=[{"label": e, "value": e} for e in VariantStoreBackend.SUPPORTED_ENGINES],
                    value="Amazon S3 Tables",
                    clearable=False,
                    className="shadow-sm"
                )
            ], md=6),
            dbc.Col([
                html.Label([html.I(className="bi bi-speedometer2 me-2"), "Engine Performance & Telemetry SLA:"], className="fw-bold mb-2"),
                html.Div(id="telemetry-badge-container", className="d-flex align-items-center h-75")
            ], md=6)
        ])
    ])
], className="shadow-sm mb-4 border-0 bg-light")

# Layout with Tabs
app.layout = dbc.Container([
    navbar,
    engine_selector,
    dbc.Tabs([
        dbc.Tab(label="📊 1. Cohort Allele Frequency", tab_id="tab-af"),
        dbc.Tab(label="🧬 2. Pathogenic Carrier Discovery", tab_id="tab-carriers"),
        dbc.Tab(label="📈 3. Gene Burden Rollup", tab_id="tab-burden"),
        dbc.Tab(label="🏥 4. Multimodal OMOP Clinical Join", tab_id="tab-omop"),
        dbc.Tab(label="⚡ 5. Multi-Engine Latency Benchmarks", tab_id="tab-benchmarks"),
    ], id="tabs-main", active_tab="tab-af", className="mb-4"),
    html.Div(id="tab-content", className="mb-5")
], fluid=True, className="px-4")


# Callback: Update Telemetry Badge
@callback(
    Output("telemetry-badge-container", "children"),
    Input("engine-dropdown", "value")
)
def update_telemetry_badge(engine):
    metrics = {
        "Amazon S3 Tables": ("Sub-second (800ms)", "Zero-Ops Compaction", "success"),
        "Custom S3 + Iceberg": ("Sub-second (890ms)", "Partition Pruned", "info"),
        "Delta Lake on S3": ("Sub-second (850ms)", "ACID Transaction Log", "primary"),
        "Hail VDS (Spark)": ("Batch (1.2s)", "Sparse MatrixTable", "warning"),
        "Amazon Aurora PostgreSQL (Serverless v2)": ("Real-time (<50ms)", "B-tree Seek + GIN JSONB", "danger"),
        "Amazon RDS PostgreSQL": ("Real-time (<75ms)", "db.t4g Fixed Instance", "secondary"),
        "AWS HealthOmics Variant Store": ("Analytical (900ms)", "Managed VCF Lakehouse", "primary"),
    }.get(engine, ("~800ms", "Standard", "info"))

    return dbc.Row([
        dbc.Col(dbc.Badge(f"Latency: {metrics[0]}", color=metrics[2], className="p-2 fs-6 me-2 shadow-sm")),
        dbc.Col(dbc.Badge(f"Storage Trait: {metrics[1]}", color="dark", className="p-2 fs-6 shadow-sm"))
    ], className="g-2")


# Callback: Render Main Tabs
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
        return dbc.Card([
            dbc.CardHeader(html.H5("Cohort Allele Frequency & Annotation Overview", className="mb-0 fw-bold")),
            dbc.CardBody([
                dcc.Graph(figure=fig, className="mb-4"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px"}
                )
            ])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-carriers":
        df, meta = backend.get_pathogenic_carriers(engine)
        return dbc.Card([
            dbc.CardHeader(html.H5("Pathogenic Mutation Carrier Discovery (APP rs63750066)", className="mb-0 fw-bold text-danger")),
            dbc.CardBody([
                html.P([
                    "Target locus: ", html.Strong("chr21:25891796 A>G (APP Pathogenic Missense)"),
                    " linked to Early-onset Alzheimer's disease. Queries executed against ",
                    dbc.Badge(engine, color="primary")
                ], className="text-muted"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#fce8e6", "color": "#c5221f", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "12px"}
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
        return dbc.Card([
            dbc.CardHeader(html.H5("Gene Burden Rollup Analysis", className="mb-0 fw-bold")),
            dbc.CardBody([dcc.Graph(figure=fig)])
        ], className="shadow-sm border-0")

    elif active_tab == "tab-omop":
        df, meta = backend.get_omop_phenotype_join(engine)
        return dbc.Card([
            dbc.CardHeader(html.H5("Multimodal Genotype ↔ OMOP CDM Phenotype Federation", className="mb-0 fw-bold text-success")),
            dbc.CardBody([
                html.P("In-place federated join between genomic variant calls and OMOP clinical person/condition tables:", className="text-muted"),
                dash_table.DataTable(
                    data=df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=6,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#e6f4ea", "color": "#137333", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px"}
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
        return dbc.Card([
            dbc.CardHeader(html.H5("Multi-Engine Query Latency & Cost Comparison", className="mb-0 fw-bold")),
            dbc.CardBody([
                dcc.Graph(figure=fig, className="mb-4"),
                dash_table.DataTable(
                    data=bench_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in bench_df.columns],
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                    style_cell={"textAlign": "left", "padding": "10px"}
                )
            ])
        ], className="shadow-sm border-0")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
