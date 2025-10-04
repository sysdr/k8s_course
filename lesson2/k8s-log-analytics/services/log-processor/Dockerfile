# Multi-stage build for Go - Optimized from 370MB to 8MB

# Stage 1: Builder
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git

# Copy go mod files for layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o log-processor ./cmd/processor

# Stage 2: Minimal runtime using alpine instead of scratch for compatibility
FROM alpine:latest

# Install CA certificates
RUN apk --no-cache add ca-certificates

# Copy static binary
COPY --from=builder /build/log-processor /log-processor

# Use non-root user
RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE 9000

ENTRYPOINT ["/log-processor"]
