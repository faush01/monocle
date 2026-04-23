use crate::telemetry::{TelemetryData, TelemetryItem};
use anyhow::{Context, Result};
use chrono::{DateTime, NaiveDateTime, TimeZone, Utc};
use rusqlite::{params, Connection};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

const KEEP_DAYS: i64 = 14;

/// SQLite-backed telemetry store. All access is serialised behind a single
/// `Mutex` to mirror the locking behaviour in the C# implementation.
pub struct TelemetryStoreSqlite {
    db_file_path: PathBuf,
    state: Mutex<StoreState>,
}

#[derive(Default)]
struct StoreState {
    last_delete_check: HashMap<PathBuf, DateTime<Utc>>,
}

impl TelemetryStoreSqlite {
    pub fn new(configured_path: &str) -> Result<Self> {
        let mut db_file_path = configured_path.to_string();
        println!("Telemetry Store Created");
        println!("DbServer:DbFilePath : {}", db_file_path);

        if let Ok(env_path) = std::env::var("DbFilePath") {
            if !env_path.is_empty() {
                db_file_path = env_path;
                println!(
                    "Enviroment variable DbFilePath loaded : {}",
                    db_file_path
                );
            }
        }

        let path = PathBuf::from(&db_file_path);
        if !path.exists() {
            fs::create_dir_all(&path)
                .with_context(|| format!("creating db directory {}", path.display()))?;
        }

        Ok(Self {
            db_file_path: path,
            state: Mutex::new(StoreState::default()),
        })
    }

    fn db_file_for(&self, db_name: &str) -> PathBuf {
        let file_name = if db_name.ends_with(".sqlite") {
            db_name.to_string()
        } else {
            format!("{}.sqlite", db_name)
        };
        self.db_file_path.join(file_name)
    }

    pub fn save_telemetry(&self, telemetry_data: &TelemetryData) {
        let mut state = self.state.lock().expect("telemetry store poisoned");

        for (db_name, items) in telemetry_data.iter() {
            let db_file = self.db_file_for(db_name);
            if let Err(e) = Self::delete_old(&db_file, &mut state.last_delete_check) {
                eprintln!("delete_old error: {}", e);
            }

            if let Err(e) = Self::write_items(&db_file, items) {
                eprintln!("write_items error: {}", e);
            }
        }

        match serde_json::to_string(telemetry_data) {
            Ok(json) => println!(
                "{}|{}",
                Utc::now().format("%Y-%m-%d %H:%M:%S"),
                json
            ),
            Err(e) => eprintln!("serialize error: {}", e),
        }
    }

    fn write_items(db_file: &Path, items: &[TelemetryItem]) -> Result<()> {
        let conn = Connection::open(db_file)
            .with_context(|| format!("opening {}", db_file.display()))?;
        Self::create_table(&conn, "telemetry")?;

        let sql = "INSERT INTO telemetry (event_date, data_type, data) \
                   VALUES (?1, ?2, ?3)";
        let mut stmt = conn.prepare(sql)?;

        for telem in items {
            let log_date_utc = parse_event_date(telem.event_date.as_deref());
            let event_date = log_date_utc.timestamp();
            let data_json = dic_to_json(&telem.event_data);
            stmt.execute(params![event_date, telem.event_type, data_json])?;
        }
        Ok(())
    }

    fn create_table(conn: &Connection, table_name: &str) -> Result<()> {
        let sql = format!(
            "CREATE TABLE IF NOT EXISTS {} (\
                 event_date int NOT NULL, \
                 data_type text NOT NULL, \
                 data text, \
                 PRIMARY KEY (event_date, data_type)\
             )",
            table_name
        );
        conn.execute(&sql, [])?;
        Ok(())
    }

    pub fn get_metrics(&self) -> HashMap<String, HashMap<String, i64>> {
        let _state = self.state.lock().expect("telemetry store poisoned");
        let mut metrics: HashMap<String, HashMap<String, i64>> = HashMap::new();

        let entries = match fs::read_dir(&self.db_file_path) {
            Ok(it) => it,
            Err(e) => {
                eprintln!("read_dir error: {}", e);
                return metrics;
            }
        };

        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) != Some("sqlite") {
                continue;
            }
            let db_name = match path.file_stem().and_then(|s| s.to_str()) {
                Some(s) => s.to_string(),
                None => continue,
            };

            match Self::collect_counts(&path) {
                Ok(Some(counts)) => {
                    metrics.insert(db_name, counts);
                }
                Ok(None) => {}
                Err(e) => eprintln!("metrics error for {}: {}", path.display(), e),
            }
        }

        metrics
    }

    fn collect_counts(db_file: &Path) -> Result<Option<HashMap<String, i64>>> {
        let conn = Connection::open(db_file)?;

        // Check if the telemetry table exists
        let exists: Option<String> = conn
            .query_row(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'",
                [],
                |row| row.get(0),
            )
            .ok();
        if exists.is_none() {
            return Ok(None);
        }

        let mut counts = HashMap::new();
        let mut stmt =
            conn.prepare("SELECT data_type, COUNT(*) as cnt FROM telemetry GROUP BY data_type")?;
        let rows = stmt.query_map([], |row| {
            let data_type: String = row.get(0)?;
            let cnt: i64 = row.get(1)?;
            Ok((data_type, cnt))
        })?;
        for row in rows {
            let (data_type, cnt) = row?;
            counts.insert(data_type, cnt);
        }
        Ok(Some(counts))
    }

    fn delete_old(
        db_file: &Path,
        last_delete_check: &mut HashMap<PathBuf, DateTime<Utc>>,
    ) -> Result<()> {
        if !db_file.exists() {
            return Ok(());
        }

        let now = Utc::now();
        let last = last_delete_check
            .get(db_file)
            .copied()
            .unwrap_or_else(|| Utc.timestamp_opt(0, 0).unwrap());

        if last > now - chrono::Duration::days(1) {
            return Ok(());
        }

        last_delete_check.insert(db_file.to_path_buf(), now);

        let cutoff = now - chrono::Duration::days(KEEP_DAYS);
        let cut_date = cutoff.timestamp();
        let sql_delete = format!("DELETE FROM telemetry WHERE event_date < {}", cut_date);

        println!("Deleting old telemetry data");
        println!("Older than : {}", cutoff.format("%Y-%m-%dT%H:%M:%S%:z"));
        println!("From       : {}", db_file.display());
        println!("{}", sql_delete);

        let conn = Connection::open(db_file)?;
        conn.execute(&sql_delete, [])?;
        drop(conn);

        Self::vacuum_database(db_file)?;
        Ok(())
    }

    fn vacuum_database(db_file: &Path) -> Result<()> {
        let len = fs::metadata(db_file).map(|m| m.len()).unwrap_or(0);
        println!("DB file size : {}", len);

        let conn = Connection::open(db_file)?;
        println!("Running DB Vacuum");
        conn.execute("VACUUM", [])?;
        drop(conn);

        let len = fs::metadata(db_file).map(|m| m.len()).unwrap_or(0);
        println!("DB file size : {}", len);
        Ok(())
    }
}

fn parse_event_date(input: Option<&str>) -> DateTime<Utc> {
    let s = match input {
        Some(s) if !s.is_empty() => s,
        _ => return Utc::now(),
    };

    // Try a few common formats; fall back to local-now if parsing fails.
    if let Ok(dt) = DateTime::parse_from_rfc3339(s) {
        return dt.with_timezone(&Utc);
    }
    for fmt in &["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S%.f"] {
        if let Ok(naive) = NaiveDateTime::parse_from_str(s, fmt) {
            // Treat naive timestamps as local time, then convert to UTC,
            // matching the C# `DateTime.Parse(...).ToUniversalTime()` behaviour.
            if let chrono::LocalResult::Single(local) = chrono::Local.from_local_datetime(&naive) {
                return local.with_timezone(&Utc);
            }
        }
    }
    Utc::now()
}

/// Format event_data as a JSON object with values rounded to 4 decimal places,
/// matching the C# `Dic2Json` helper.
fn dic_to_json(event_data: &HashMap<String, f64>) -> String {
    let parts: Vec<String> = event_data
        .iter()
        .map(|(k, v)| {
            let rounded = (v * 10_000.0).round() / 10_000.0;
            // Use serde_json for proper key escaping; format value compactly.
            let key = serde_json::to_string(k).unwrap_or_else(|_| format!("\"{}\"", k));
            format!("{}:{}", key, format_number(rounded))
        })
        .collect();
    format!("{{{}}}", parts.join(","))
}

fn format_number(v: f64) -> String {
    if v.fract() == 0.0 && v.is_finite() {
        format!("{}", v as i64)
    } else {
        // Trim trailing zeros from a fixed format, max 4 decimals.
        let s = format!("{:.4}", v);
        let trimmed = s.trim_end_matches('0').trim_end_matches('.').to_string();
        if trimmed.is_empty() || trimmed == "-" {
            "0".to_string()
        } else {
            trimmed
        }
    }
}
