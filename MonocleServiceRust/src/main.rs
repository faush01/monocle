mod config;
mod handlers;
mod store;
mod telemetry;

use crate::config::AppSettings;
use crate::handlers::{health, post_telemetry, AppState};
use crate::store::TelemetryStoreSqlite;
use axum::{routing::get, Router};
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let settings = AppSettings::load();

    let store = TelemetryStoreSqlite::new(&settings.db_server.db_file_path)?;
    let state: AppState = Arc::new(store);

    let app = Router::new()
        .route("/", get(health).post(post_telemetry))
        .with_state(state);

    let bind = settings.bind_address();
    println!("Listening on {}", bind);
    let listener = tokio::net::TcpListener::bind(&bind).await?;
    axum::serve(listener, app).await?;
    Ok(())
}
