use crate::store::TelemetryStoreSqlite;
use crate::telemetry::TelemetryData;
use axum::{extract::State, http::StatusCode, response::IntoResponse, Json};
use serde_json::{json, Value};
use std::sync::Arc;

pub type AppState = Arc<TelemetryStoreSqlite>;

/// GET / - basic health check, also returns per-database row counts.
pub async fn health(State(store): State<AppState>) -> impl IntoResponse {
    println!("HealthPing");
    let metrics = store.get_metrics();
    Json(json!({
        "message": "HealthPing",
        "metrics": metrics,
    }))
}

/// POST / - persist a telemetry payload.
pub async fn post_telemetry(
    State(store): State<AppState>,
    body: Option<Json<TelemetryData>>,
) -> impl IntoResponse {
    match body {
        None => {
            println!("No Data");
            (StatusCode::OK, Json(json!({ "message": "no data" })))
        }
        Some(Json(data)) => {
            store.save_telemetry(&data);
            (
                StatusCode::OK,
                Json(json!({ "message": "Telemetry Saved" })),
            )
        }
    }
}

/// Fallback for empty or unparseable POST bodies — Axum will reject these
/// before reaching `post_telemetry`, so we expose a simple JSON error.
pub async fn _unused_marker() -> Json<Value> {
    Json(json!({}))
}
