#!/bin/bash
set -euo pipefail

# Startup script to start all services using docker-compose
# Checks for duplicate services before starting

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

log_info "Starting Kubernetes Health Probes System..."

# Check for duplicate services
check_duplicates() {
    log_info "Checking for duplicate services..."
    
    # Check docker-compose services
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' | grep -E "(log-collector|log-processor|analytics-api|frontend|redis|kafka)" > /dev/null 2>&1; then
            log_warn "Found existing containers. Checking for duplicates..."
            EXISTING=$(docker ps --format '{{.Names}}' | grep -E "(log-collector|log-processor|analytics-api|frontend|redis|kafka)" || true)
            if [ -n "${EXISTING}" ]; then
                log_warn "Existing containers found:"
                echo "${EXISTING}"
                read -p "Stop existing containers and continue? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Stopping existing containers..."
                    docker-compose down 2>/dev/null || docker stop $(echo "${EXISTING}") 2>/dev/null || true
                else
                    log_error "Aborting startup. Please stop existing containers first."
                    exit 1
                fi
            fi
        fi
    fi
    
    # Check for port conflicts
    PORTS=(3000 6379 9092 8081 8082 8083)
    for port in "${PORTS[@]}"; do
        if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warn "Port ${port} is already in use"
            PID=$(lsof -Pi :${port} -sTCP:LISTEN -t)
            log_warn "Process using port ${port}: PID ${PID}"
        fi
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    # Check for docker-compose or docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log_error "docker-compose is not available. Please install docker-compose."
        exit 1
    fi
    
    log_info "Using: ${COMPOSE_CMD}"
}

# Build images if needed
build_images() {
    log_info "Building Docker images..."
    
    if [ -f "${PROJECT_ROOT}/scripts/build.sh" ]; then
        if [ -x "${PROJECT_ROOT}/scripts/build.sh" ]; then
            "${PROJECT_ROOT}/scripts/build.sh"
        else
            log_warn "build.sh is not executable, making it executable..."
            chmod +x "${PROJECT_ROOT}/scripts/build.sh"
            "${PROJECT_ROOT}/scripts/build.sh"
        fi
    else
        log_error "build.sh not found at ${PROJECT_ROOT}/scripts/build.sh"
        exit 1
    fi
}

# Start services
start_services() {
    log_info "Starting services with docker-compose..."
    
    cd "${PROJECT_ROOT}"
    
    if [ ! -f "docker-compose.yaml" ]; then
        log_error "docker-compose.yaml not found in ${PROJECT_ROOT}"
        exit 1
    fi
    
    ${COMPOSE_CMD} up -d
    
    log_info "Waiting for services to be healthy..."
    sleep 5
    
    # Wait for services to be ready
    MAX_WAIT=120
    WAIT_TIME=0
    while [ ${WAIT_TIME} -lt ${MAX_WAIT} ]; do
        if curl -sf http://localhost:8081/health/live > /dev/null 2>&1; then
            log_info "Log Collector is ready"
            break
        fi
        sleep 2
        WAIT_TIME=$((WAIT_TIME + 2))
    done
    
    if [ ${WAIT_TIME} -ge ${MAX_WAIT} ]; then
        log_warn "Services may not be fully ready. Check logs with: ${COMPOSE_CMD} logs"
    fi
}

# Main execution
main() {
    check_prerequisites
    check_duplicates
    build_images
    start_services
    
    log_info "Services started!"
    log_info "Frontend: http://localhost:3000"
    log_info "Log Collector: http://localhost:8081"
    log_info "Log Processor: http://localhost:8082"
    log_info "Analytics API: http://localhost:8083"
    log_info ""
    log_info "To view logs: ${COMPOSE_CMD} logs -f"
    log_info "To stop services: ${COMPOSE_CMD} down"
    log_info "To run demo: ${PROJECT_ROOT}/scripts/demo.sh"
}

main "$@"

