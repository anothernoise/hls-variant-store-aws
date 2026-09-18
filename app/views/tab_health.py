"""
Tab 7: AWS Genomic Storage Engines Cluster Health & Readiness View.
"""

from typing import Any, Dict
from dash import html, dash_table
import dash_bootstrap_components as dbc


def render_health_tab(summary: Dict[str, Any], mode_badge: dbc.Badge) -> dbc.Card:
    """Renders the comprehensive cluster health dashboard tab."""
    cluster_status = summary.get("status", "healthy").upper()
    total_engines = summary.get("total_engines", 4)
    active_count = summary.get("active_engines", 4)
    not_deployed_count = summary.get("not_deployed_engines", 0)
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
