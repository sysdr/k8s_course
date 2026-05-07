# Lesson 65: Break-It-Friday — Docker DNS debugging

**Course: 180 — The Kubernetes Odyssey**

## Bootstrap (first-time)

This folder (`lesson65-dns-debug`) holds the exercises. **`setup.sh` lives one level up**, next to `lesson65-dns-debug/`. Generate or refresh outputs from there:

```bash
cd ..                  # lesson65 — parent directory that contains setup.sh
bash ./setup.sh
cd lesson65-dns-debug
```

Then work only inside `lesson65-dns-debug` unless you rerun `setup.sh`.

## Overview

This directory contains a deliberately broken Docker Compose environment.
Your objective: identify and fix three DNS-related misconfiguration bugs before
validating with the provided test suite and diagnostic tooling.

## Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.20+
- Python 3.11+ (for tests)
- `curl`, `jq` (for diagnostic scripts)

## Directory Structure

```
lesson65-dns-debug/
├── cleanup.sh               # Full Docker teardown + prune (optional daemon stop); see Cleanup
├── requirements.txt         # Integration test deps at repo root here
├── .gitignore
├── broken/                  # Buggy environment — three intentional errors
│   ├── api-service/         # FastAPI service that calls log-processor
│   ├── log-processor/       # FastAPI ingestion service
│   └── docker-compose.yml   # Contains BUG #1, #2, #3 — find them
├── fixed/                   # Corrected environment (reference solution)
│   ├── api-service/
│   ├── log-processor/
│   └── docker-compose.yml   # All three bugs fixed
├── scripts/
│   ├── diagnose.sh          # DNS debugging toolkit — run this first
│   ├── start-broken.sh      # Launch the broken environment
│   ├── start-fixed.sh       # Launch the fixed environment
│   └── cleanup.sh           # Tear down everything
├── tests/
│   └── test_dns_fix.py      # Integration test suite — validates your fix
├── monitoring/
│   └── check-dns-metrics.sh # DNS latency measurement
└── k8s-preview/
    └── manifests/           # Preview of Lesson 66 Kubernetes equivalents
```

## Exercise Instructions

### Step 1: Start the broken environment

```bash
./scripts/start-broken.sh
```

### Step 2: Observe the failure

```bash
# Check API health — it should report upstream_reachable: false
curl http://localhost:8000/health | python3 -m json.tool

# Run the diagnostic toolkit
./scripts/diagnose.sh
```

### Step 3: Diagnose

Inside the broken `docker-compose.yml`, find and understand all three bugs:

- **BUG #1**: Network attachment — which service is missing a network?
- **BUG #2**: Alias placement — at what YAML path must aliases be declared?
- **BUG #3**: Dependency condition — what's wrong with the `depends_on` block?

Use the diagnostic commands:

```bash
# Inspect network membership
docker inspect lesson65-api --format '{{json .NetworkSettings.Networks}}' | jq

# Test DNS from inside the container
docker exec lesson65-api nslookup processor 127.0.0.11
docker exec lesson65-api nslookup log-processor 127.0.0.11

# Distinguish DNS failure from connectivity failure
docker exec lesson65-api wget -qO- --timeout=5 http://processor:8080/health
```

### Step 4: Apply your fix

Edit `broken/docker-compose.yml` to resolve all three bugs, then:

```bash
cd broken
docker compose down && docker compose up -d
```

Re-run `./scripts/diagnose.sh` to verify.

### Step 5: Run integration tests against your fix

```bash
pip install -r requirements.txt   # or: pip install -r tests/requirements.txt
python -m pytest tests/test_dns_fix.py -v
```

All 9 tests must pass. Each test maps to a specific bug or behaviour.

### Step 6: Verify against the reference solution

```bash
./scripts/start-fixed.sh
python -m pytest tests/test_dns_fix.py -v
```

## Key Debugging Commands Reference

| Command | What it tells you |
|---|---|
| `docker inspect <ctr> \| jq '.[0].NetworkSettings.Networks'` | Which networks the container is on |
| `docker exec <ctr> cat /etc/resolv.conf` | Confirms DNS server is 127.0.0.11 |
| `docker exec <ctr> nslookup <name> 127.0.0.11` | Tests name resolution directly |
| `docker exec <ctr> wget -qO- http://<name>:<port>/health` | Tests HTTP connectivity |
| `docker compose logs <svc>` | Application-level error messages |
| `docker network inspect <net>` | Shows all containers on a network and their aliases |

## DNS Failure Taxonomy

| Error | Root Cause | Fix |
|---|---|---|
| `NXDOMAIN` | Name not registered on this network | Check network attachment (BUG #1) or alias placement (BUG #2) |
| `Connection refused` | DNS resolved, port not open | Check service is running and listening |
| `Connection timed out` | DNS resolved, network drops packets | Check NetworkPolicy or firewall |
| `Name or service not known` | Resolver unreachable | Check container is on a user-defined network |

## Kubernetes Bridge (Lesson 66 Preview)

The `k8s-preview/manifests/` directory shows the Kubernetes equivalents:

- Docker network alias → Kubernetes `Service` object (CoreDNS entry)
- `depends_on: condition: service_healthy` → `readinessProbe` on the Deployment
- Network attachment → Namespace + NetworkPolicy

Same mental model. Different implementation layer.

## Cleanup

Tear down only the Compose stacks (containers + volumes for this repo):

```bash
./scripts/cleanup.sh
```

Full cleanup (Compose down, lesson images, **global** unused Docker images/containers/build cache/volumes prune, networks):

```bash
./cleanup.sh
```

Optional: also try to stop the **Docker daemon** (needs sufficient privileges):

```bash
STOP_DOCKER_DAEMON=1 ./cleanup.sh
```

Remove local caches in this lesson tree:

```bash
find . -type d \( -name node_modules -o -name venv -o -name .venv -o -name .pytest_cache -o -name __pycache__ \) -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

**Note:** `setup.sh` (parent directory) may write **`../generate_k8s_system.log`** next to itself; `.gitignore` includes that pattern relative to ignores in this subtree where applicable — delete that log manually if desired.

## Security

Do **not** commit API keys or `.env` files with secrets. Keep credentials out of the lesson sources; `.gitignore` excludes common local paths (`venv/`, `.env`, etc.).
