#!/bin/bash
set -euo pipefail
# ─── Break-It-Friday: Multi-Cluster Failover Test ────────────────────────────

PRIMARY_CTX="${PRIMARY_CTX:-cluster-us-east}"
FAILOVER_CTX="${FAILOVER_CTX:-cluster-eu-west}"
NAMESPACE="${NAMESPACE:-log-platform}"
DNS_ZONE_ID="${DNS_ZONE_ID:-}"
API_HOST="${API_HOST:-api.example.com}"

log() { echo "[$(date +%H:%M:%S)] $*"; }

check_prereqs() {
  for cmd in kubectl aws curl dig; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "Missing: $cmd"; exit 1; }
  done
  kubectl config get-contexts "$PRIMARY_CTX"  >/dev/null 2>&1 || { echo "Context $PRIMARY_CTX not found"; exit 1; }
  kubectl config get-contexts "$FAILOVER_CTX" >/dev/null 2>&1 || { echo "Context $FAILOVER_CTX not found"; exit 1; }
}

record_rto_start() {
  OUTAGE_START=$(date +%s)
  log "⏱  RTO measurement started at $(date -d @$OUTAGE_START)"
}

simulate_outage() {
  log "🔴 SIMULATING REGIONAL OUTAGE on $PRIMARY_CTX"
  log "Cordoning all nodes in primary cluster..."

  kubectl --context="$PRIMARY_CTX" get nodes -o name | while read -r node; do
    kubectl --context="$PRIMARY_CTX" cordon "$node"
    log "  Cordoned: $node"
  done

  log "Draining application pods (grace-period=30s)..."
  kubectl --context="$PRIMARY_CTX" drain \
    --ignore-daemonsets \
    --delete-emptydir-data \
    --grace-period=30 \
    --timeout=120s \
    -l "tier=application" \
    --all-namespaces 2>&1 | tail -5 || true
}

watch_failover_cluster() {
  log "👀 Watching failover cluster: $FAILOVER_CTX"
  local max_wait=300
  local elapsed=0
  while [[ $elapsed -lt $max_wait ]]; do
    local ready
    ready=$(kubectl --context="$FAILOVER_CTX" get pods -n "$NAMESPACE" \
      --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    log "  Running pods in $NAMESPACE: $ready"
    if [[ $ready -ge 3 ]]; then
      log "✅ Failover cluster healthy ($ready pods running)"
      return 0
    fi
    sleep 10
    elapsed=$((elapsed + 10))
  done
  log "❌ Failover cluster did not stabilize within ${max_wait}s"
  return 1
}

update_dns() {
  if [[ -z "$DNS_ZONE_ID" ]]; then
    log "⚠  DNS_ZONE_ID not set, skipping Route53 update (manual DNS update required)"
    return
  fi

  FAILOVER_LB=$(kubectl --context="$FAILOVER_CTX" get svc -n istio-system istio-ingressgateway \
    -o jsonpath="{.status.loadBalancer.ingress[0].hostname}" 2>/dev/null || echo "")

  if [[ -z "$FAILOVER_LB" ]]; then
    log "⚠  Could not determine failover LB hostname"
    return
  fi

  log "🌐 Updating DNS: $API_HOST → $FAILOVER_LB"
  aws route53 change-resource-record-sets \
    --hosted-zone-id "$DNS_ZONE_ID" \
    --change-batch "{
      \"Changes\": [{
        \"Action\": \"UPSERT\",
        \"ResourceRecordSet\": {
          \"Name\": \"${API_HOST}\",
          \"Type\": \"CNAME\",
          \"TTL\": 60,
          \"ResourceRecords\": [{\"Value\": \"${FAILOVER_LB}\"}]
        }
      }]
    }" || log "⚠  Route53 update failed — check credentials"

  log "Waiting for DNS propagation (TTL=60s)..."
  for i in $(seq 1 12); do
    sleep 10
    resolved=$(dig +short "$API_HOST" | head -1 || echo "")
    log "  dig $API_HOST → $resolved"
  done
}

validate_traffic() {
  log "🔍 Validating traffic on failover cluster..."
  local healthy=false
  for i in $(seq 1 6); do
    if curl -sf --max-time 5 "https://${API_HOST}/healthz" >/dev/null 2>&1; then
      healthy=true
      break
    fi
    log "  Attempt $i/6 failed, retrying in 10s..."
    sleep 10
  done

  if $healthy; then
    local rto=$(( $(date +%s) - OUTAGE_START ))
    log "✅ TRAFFIC VALIDATED — Actual RTO: ${rto}s"
  else
    log "❌ TRAFFIC VALIDATION FAILED — investigate failover cluster"
  fi
}

restore_primary() {
  log "🔁 Restoring primary cluster nodes..."
  kubectl --context="$PRIMARY_CTX" get nodes -o name | while read -r node; do
    kubectl --context="$PRIMARY_CTX" uncordon "$node"
    log "  Uncordoned: $node"
  done
  log "✅ Primary cluster restored"
}

main() {
  check_prereqs
  log "=== Break-It-Friday: Multi-Cluster Failover Test ==="
  log "Primary:  $PRIMARY_CTX"
  log "Failover: $FAILOVER_CTX"
  echo ""

  record_rto_start
  simulate_outage
  watch_failover_cluster
  update_dns
  validate_traffic

  log ""
  log "Press ENTER to restore the primary cluster..."
  read -r
  restore_primary
  log "=== Failover test complete ==="
}

main "$@"
