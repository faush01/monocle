# MonocleService (Rust)

A Rust port of the original C# `MonocleService`. Feature equivalent: a small HTTP
service that accepts telemetry payloads and writes them into per-database SQLite
files, plus a health endpoint that reports row counts.

## Endpoints

- `GET /` — health check. Returns `{ "message": "HealthPing", "metrics": { ... } }`.
- `POST /` — accepts a JSON payload of the form:

```json
{
  "test": [
    { "event_date": "2022-03-01 10:30:00", "event_type": "power",       "event_data": { "ws": 100.1, "ps": 10 } },
    { "event_date": "2022-03-01 10:31:00", "event_type": "temperature", "event_data": { "rh": 80.1, "t": 25.89 } }
  ]
}
```

Each top-level key becomes a SQLite database file (`<key>.sqlite`) in the
configured `DbFilePath` directory. Each item is inserted into a `telemetry`
table with `(event_date INT, data_type TEXT, data TEXT)`.

## Configuration

Reads `appsettings.json` (and optionally `appsettings.{ENV}.json` where `ENV`
comes from `ASPNETCORE_ENVIRONMENT` / `DOTNET_ENVIRONMENT`). Environment
variable `DbFilePath` overrides the configured path, matching the C# service.

## Run locally

```
cargo run --release
```

## Build Docker

```
docker build -t monocle-service-rust .
```

## Deploy Docker

```
docker volume create monocle-docker

docker run --rm --name monocle_service \
    -p 3456:3456 \
    -e TZ=Australia/Sydney \
    -e DbFilePath=/monocle_data \
    --volume=monocle-docker:/monocle_data \
    monocle-service-rust:latest
```

## Github Pull

```
docker image pull ghcr.io/faush01/monocle/monocleservice-rust:develop

docker run --rm --name monocle_service \
    -p 3456:3456 \
    -e TZ=Australia/Sydney \
    -e DbFilePath=/monocle_data \
    --volume=monocle-docker:/monocle_data \
    ghcr.io/faush01/monocle/monocleservice-rust:develop
```


