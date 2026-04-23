# Build stage
FROM rust:1.82-slim AS build

WORKDIR /src

# Cache dependencies
COPY Cargo.toml Cargo.lock* ./
RUN mkdir src && echo "fn main(){}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Build the real source
COPY src ./src
RUN touch src/main.rs && cargo build --release

# Runtime stage
FROM debian:bookworm-slim AS runtime

ENV TZ=UTC

WORKDIR /app

COPY --from=build /src/target/release/monocle_service /app/monocle_service
COPY appsettings.json /app/appsettings.json

EXPOSE 3456

ENTRYPOINT ["/app/monocle_service"]
