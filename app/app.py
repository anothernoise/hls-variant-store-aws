"""
HLS SA Bootcamp App — Genomic Variant Store Explorer
Interactive Population Genomics & Multimodal Clinical Discovery Platform.
Built with Plotly Dash & Dash Bootstrap Components.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

# Ensure project root and app directory are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.backend_modules.base import VariantStoreBackend
except (ImportError, ModuleNotFoundError):
    from backend_modules.base import VariantStoreBackend

from api_client import VariantStoreApiClient
from components import create_navbar, create_sidebar
from views import (
    render_af_tab,
    render_carriers_tab,
    render_burden_tab,
    render_omop_tab,
    render_benchmarks_tab,
    build_benchmarks_body,
    render_raw_tab_shell,
    render_raw_explorer_body,
    render_health_tab
)

# Initialize Dash App with modern FLATLY theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="HLS SA Bootcamp App — Genomic Variant Store Explorer",
    suppress_callback_exceptions=True
)

backend = VariantStoreBackend()
api_client = VariantStoreApiClient()

navbar = create_navbar()
sidebar = create_sidebar(supported_engines=VariantStoreBackend.SUPPORTED_ENGINES)

# -----------------------------------------------------------------------------
# Main Content Tabs Layout
# -----------------------------------------------------------------------------
content = html.Div([
    dcc.Loading(
        id="main-loading",
        type="circle",
        color="#0d6efd",
        children=html.Div(id="tab-content", className="mb-4")
    )
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
def update_mode_status_badge(is_online: bool):
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
# Callback: Update Refresh Timestamp
# -----------------------------------------------------------------------------
@callback(
    Output("last-refresh-timestamp", "children"),
    Input("global-refresh-btn", "n_clicks")
)
def update_refresh_timestamp(n_clicks: int):
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    if not n_clicks:
        return html.Span([
            html.I(className="bi bi-clock-history me-1 text-muted"),
            html.Span(f"Initial Load ({now_str})")
        ])
    return html.Span([
        html.I(className="bi bi-check2-circle me-1 text-success"),
        html.Span(f"Refreshed: {now_str} (x{n_clicks})")
    ])


# -----------------------------------------------------------------------------
# Callback: Update Telemetry Badge
# -----------------------------------------------------------------------------
@callback(
    Output("telemetry-badge-container", "children"),
    [Input("engine-dropdown", "value"),
     Input("online-offline-switch", "value"),
     Input("global-refresh-btn", "n_clicks")]
)
def update_telemetry_badge(engine: str, is_online: bool, refresh_clicks: int = 0):
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
# Callback: Update Cohort & Dataset Context in Left Sidebar
# -----------------------------------------------------------------------------
@callback(
    Output("cohort-context-container", "children"),
    [Input("engine-dropdown", "value"),
     Input("online-offline-switch", "value"),
     Input("tabs-main", "active_tab"),
     Input("global-refresh-btn", "n_clicks")]
)
def update_cohort_dataset_context(engine: str, is_online: bool, active_tab: str, refresh_clicks: int = 0):
    tab_contexts = {
        "tab-af": ("variants (Allele Freq)", "10 WGS Samples (Additive)", "APP, SOD1, BRCA1", "Allele Frequency"),
        "tab-carriers": ("variants (Genotypes)", "10 WGS Samples (Additive)", "APP (rs63750066)", "Carrier Discovery"),
        "tab-burden": ("variants (Aggregated)", "10 WGS Samples (Additive)", "APP (chr21:25891796)", "Gene Burden"),
        "tab-omop": ("variants ⨝ person ⨝ cond", "4 Federated Patients", "APP Missense ↔ Alzheimer's", "OMOP CDM v5.4"),
        "tab-benchmarks": ("lakehouse_benchmarks", "10 to 2,500 Samples", "Multi-Locus Cross-Engine", "Latency & Cost Matrix"),
        "tab-raw": ("store_explorer", "Direct Table Seek", "Contig / Sample Partition", "Raw Lakehouse Store"),
        "tab-health": ("health_telemetry", "Cluster Diagnostics", "All 4 Lakehouse Tiers", "Engine Diagnostic Probe"),
    }
    schema_label, cohort_str, loci_str, model_str = tab_contexts.get(
        active_tab,
        ("variants", "10 WGS Samples", "APP, SOD1, BRCA1", "OMOP CDM v5.4")
    )

    if is_online:
        origin_badge = html.Span([
            html.I(className="bi bi-cloud-check-fill me-1 text-success"),
            html.Span("Live AWS Lakehouse (us-east-1)", className="fw-bold text-success")
        ])
        engine_str = f"{engine} (Cloud)"
    else:
        origin_badge = html.Span([
            html.I(className="bi bi-laptop me-1 text-warning"),
            html.Span("Synthetic Simulation (Local Air-gap)", className="fw-bold text-dark")
        ])
        engine_str = f"{engine} (Mock Simulation)"

    return dbc.ListGroup([
        dbc.ListGroupItem([
            html.Small("Dataset Origin:", className="text-muted d-block"),
            origin_badge
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Storage Architecture:", className="text-muted d-block"),
            html.Span(engine_str, className="fw-bold text-dark")
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Active View Context:", className="text-muted d-block"),
            html.Span(model_str, className="fw-bold text-primary")
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Reference Coordinate:", className="text-muted d-block"),
            html.Span("GRCh38 / hg38", className="fw-bold text-dark")
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Evaluated Cohort:", className="text-muted d-block"),
            html.Span(cohort_str, className="fw-bold text-dark")
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Target Clinical Loci:", className="text-muted d-block"),
            html.Span(loci_str, className="fw-bold text-dark")
        ], className="border-0 px-0 py-1"),
        dbc.ListGroupItem([
            html.Small("Active Schema/Table:", className="text-muted d-block"),
            html.Span(schema_label, className="badge bg-light text-dark border")
        ], className="border-0 px-0 py-1"),
    ], flush=True)


# -----------------------------------------------------------------------------
# Callback: Dynamically Filter Engine Dropdown by Health API Availability
# -----------------------------------------------------------------------------
@callback(
    [Output("engine-dropdown", "options"),
     Output("engine-dropdown", "value")],
    [Input("online-offline-switch", "value"),
     Input("global-refresh-btn", "n_clicks")],
    [State("engine-dropdown", "value")]
)
def update_engine_dropdown_options(is_online: bool, refresh_clicks: int = 0, current_value: str = "Amazon S3 Tables"):
    offline = not is_online
    health_summary = api_client.get_all_engines_health(offline=offline)
    engines_health = health_summary.get("engines", {})

    available_engines = []
    for eng_id, h in engines_health.items():
        if is_online:
            if h.get("deployment_status") == "ACTIVE" and h.get("status") == "pass":
                available_engines.append(h.get("engine_name"))
        else:
            if h.get("status") in ("pass", "warn") and h.get("deployment_status") != "DISABLED":
                available_engines.append(h.get("engine_name"))

    if not available_engines:
        available_engines = [
            "Amazon S3 Tables",
            "Custom S3 + Iceberg",
            "Delta Lake on S3",
            "Hail VDS (Spark)"
        ]

    options = [{"label": e, "value": e} for e in available_engines]
    new_value = current_value if current_value in available_engines else available_engines[0]
    return options, new_value


# -----------------------------------------------------------------------------
# Callback: Render Main Tabs
# -----------------------------------------------------------------------------
@callback(
    Output("tab-content", "children"),
    [Input("tabs-main", "active_tab"),
     Input("engine-dropdown", "value"),
     Input("online-offline-switch", "value"),
     Input("global-refresh-btn", "n_clicks")]
)
def render_tab_content(active_tab: str, engine: str, is_online: bool, refresh_clicks: int = 0):
    offline = not is_online
    mode_badge = (
        dbc.Badge([html.I(className="bi bi-cloud-check-fill me-1"), "Live AWS"], color="success", className="ms-2")
        if is_online else
        dbc.Badge([html.I(className="bi bi-laptop me-1"), "Offline Sim"], color="warning", className="ms-2 text-dark")
    )
    config = backend.get_engine_config(engine)
    engine_id = config.get("id", engine.lower().replace(" ", "_"))

    if active_tab == "tab-af":
        df, meta = api_client.get_allele_frequencies(engine, offline=offline)
        return render_af_tab(df, meta, engine, offline, mode_badge, engine_id)

    elif active_tab == "tab-carriers":
        df, meta = api_client.get_pathogenic_carriers(engine, offline=offline)
        return render_carriers_tab(df, meta, engine, offline, mode_badge, engine_id)

    elif active_tab == "tab-burden":
        df, meta = api_client.get_gene_burden(engine, offline=offline)
        return render_burden_tab(df, meta, engine, offline, mode_badge, engine_id)

    elif active_tab == "tab-omop":
        df, meta = api_client.get_omop_phenotype_join(engine, offline=offline)
        return render_omop_tab(df, meta, engine, offline, mode_badge, engine_id)

    elif active_tab == "tab-benchmarks":
        bench_data = api_client.get_benchmarks()
        return render_benchmarks_tab(bench_data)

    elif active_tab == "tab-raw":
        return render_raw_tab_shell(engine, mode_badge)

    elif active_tab == "tab-health":
        summary = api_client.get_all_engines_health(offline=offline)
        return render_health_tab(summary, mode_badge)

    return dbc.Alert("Select a tab above to explore genomic variants.", color="light")


# -----------------------------------------------------------------------------
# Callback: Update Raw Store Data Explorer Body
# -----------------------------------------------------------------------------
@callback(
    Output("raw-explorer-body", "children"),
    [Input("engine-dropdown", "value"),
     Input("raw-table-select", "value"),
     Input("raw-chrom-select", "value"),
     Input("raw-sample-select", "value"),
     Input("online-offline-switch", "value"),
     Input("global-refresh-btn", "n_clicks")]
)
def update_raw_explorer_body(engine, table_name, chromosome, sample_id, is_online, refresh_clicks=0):
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

    return render_raw_explorer_body(
        df=df,
        telemetry=telemetry,
        sql=sql,
        meta=meta,
        engine=engine,
        table_name=table_name or "variants",
        offline=offline,
        mode_badge=mode_badge
    )


# -----------------------------------------------------------------------------
# Callback: Run Performance Benchmark & Update Results (Reactive on Dropdowns & Button)
# -----------------------------------------------------------------------------
@callback(
    [Output("benchmarks-results-container", "children"),
     Output("bench-status-badge", "children")],
    [Input("run-benchmark-btn", "n_clicks"),
     Input("bench-cohort-select", "value"),
     Input("bench-mode-select", "value")],
    prevent_initial_call=True
)
def handle_run_benchmark(n_clicks: Optional[int], cohort_size: Optional[int], mode: Optional[str]):
    target_cohort = int(cohort_size) if cohort_size else 100
    target_mode = mode or "simulated"
    res = api_client.run_benchmarks(
        mode=target_mode,
        cohort_size=target_cohort
    )
    exec_dur = res.get("execution_duration_ms", 0.0)
    status_badge = dbc.Badge([
        html.I(className="bi bi-check2-circle me-1 text-success"),
        f"Executed in {exec_dur:.1f}ms ({target_cohort} samples • {target_mode})"
    ], color="light", className="text-dark border p-2 small shadow-sm")
    return build_benchmarks_body(res), status_badge



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)

