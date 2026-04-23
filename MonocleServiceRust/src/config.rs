use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
pub struct DbServerConfig {
    #[serde(rename = "DbFilePath")]
    pub db_file_path: String,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
pub struct HttpEndpoint {
    #[serde(rename = "Url")]
    pub url: String,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
pub struct Endpoints {
    #[serde(rename = "Http")]
    pub http: HttpEndpoint,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
pub struct KestrelConfig {
    #[serde(rename = "Endpoints")]
    pub endpoints: Endpoints,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
pub struct AppSettings {
    #[serde(rename = "DbServer")]
    pub db_server: DbServerConfig,
    #[serde(rename = "Kestrel")]
    pub kestrel: KestrelConfig,
}

impl AppSettings {
    /// Load `appsettings.json` and overlay `appsettings.{ENV}.json` if present.
    /// Falls back to defaults when files are missing.
    pub fn load() -> Self {
        let mut settings = Self::load_file("appsettings.json").unwrap_or_default();

        let env_name = std::env::var("ASPNETCORE_ENVIRONMENT")
            .or_else(|_| std::env::var("DOTNET_ENVIRONMENT"))
            .unwrap_or_else(|_| "Production".to_string());
        let env_file = format!("appsettings.{}.json", env_name);
        if let Some(env_settings) = Self::load_file(&env_file) {
            // Simple overlay: non-empty env values win
            if !env_settings.db_server.db_file_path.is_empty() {
                settings.db_server.db_file_path = env_settings.db_server.db_file_path;
            }
            if !env_settings.kestrel.endpoints.http.url.is_empty() {
                settings.kestrel.endpoints.http.url = env_settings.kestrel.endpoints.http.url;
            }
        }

        if settings.db_server.db_file_path.is_empty() {
            settings.db_server.db_file_path = "metrics".to_string();
        }
        if settings.kestrel.endpoints.http.url.is_empty() {
            settings.kestrel.endpoints.http.url = "http://*:3456".to_string();
        }

        settings
    }

    fn load_file<P: AsRef<Path>>(path: P) -> Option<Self> {
        let text = fs::read_to_string(path).ok()?;
        serde_json::from_str(&text).ok()
    }

    /// Convert the Kestrel URL ("http://*:3456" or "http://0.0.0.0:3456") to a bind address.
    pub fn bind_address(&self) -> String {
        let url = &self.kestrel.endpoints.http.url;
        let without_scheme = url
            .trim_start_matches("http://")
            .trim_start_matches("https://");
        // Replace wildcard host with 0.0.0.0
        let parts: Vec<&str> = without_scheme.rsplitn(2, ':').collect();
        if parts.len() == 2 {
            let port = parts[0];
            let host = parts[1];
            let host = if host == "*" || host.is_empty() {
                "0.0.0.0"
            } else {
                host
            };
            format!("{}:{}", host, port)
        } else {
            // No port specified, default to 3456
            "0.0.0.0:3456".to_string()
        }
    }
}
