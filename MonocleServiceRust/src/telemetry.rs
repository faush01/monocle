use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Mirrors the C# `TelemetryItem` model.
#[derive(Debug, Deserialize, Serialize)]
pub struct TelemetryItem {
    pub event_date: Option<String>,
    pub event_type: String,
    pub event_data: HashMap<String, f64>,
}

/// Mirrors the C# `TelemetryData` (Dictionary<string, List<TelemetryItem>>).
pub type TelemetryData = HashMap<String, Vec<TelemetryItem>>;
