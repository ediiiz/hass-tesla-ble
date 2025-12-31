FROM rust:1.83-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    dbus-dev \
    musl-dev \
    pkgconf \
    openssl-dev

WORKDIR /build

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./
COPY build.rs ./
COPY proto ./proto/
COPY src ./src/

# Build the project
RUN cargo build --release

# Final stage
FROM alpine:3.20

# Install runtime dependencies
RUN apk add --no-cache \
    dbus \
    bluez \
    libgcc

# Create non-root user
RUN addgroup -g 1000 hass && \
    adduser -D -u 1000 -G hass -h /data hass

# Copy binary from builder
COPY --from=builder /build/target/release/hass-tesla-ble /usr/local/bin/

# Set up directories
RUN mkdir -p /data /config && \
    chown -R hass:hass /data /config

# Switch to non-root user
USER hass

# Set working directory
WORKDIR /data

# Expose health endpoint (if needed)
EXPOSE 8099

# Run the application
CMD ["/usr/local/bin/hass-tesla-ble"]
