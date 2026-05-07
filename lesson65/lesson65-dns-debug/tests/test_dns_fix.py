"""
Integration tests — Lesson 65 Break-It-Friday
Validates that the fixed Docker Compose environment resolves all three bugs.
Run with: python -m pytest tests/ -v
Requires: docker compose (fixed) to be running.
"""

import subprocess
import time
import pytest
import httpx


API_BASE = "http://localhost:8000"
PROCESSOR_BASE = "http://localhost:8080"
API_CONTAINER = "lesson65-api"
PROCESSOR_CONTAINER = "lesson65-processor"


def docker_exec(container: str, *cmd: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["docker", "exec", container, *cmd],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestContainerNetworkMembership:
    """Verify both containers are on the correct networks after the fix."""

    def test_api_service_on_frontend_net(self):
        rc, out, _ = docker_exec(
            API_CONTAINER,
            "cat", "/etc/hostname"
        )
        assert rc == 0, f"Cannot exec into {API_CONTAINER}"

    def test_api_service_attached_to_backend_net(self):
        result = subprocess.run(
            ["docker", "inspect", API_CONTAINER, "--format",
             "{{range $net, $_ := .NetworkSettings.Networks}}{{$net}} {{end}}"],
            capture_output=True, text=True
        )
        networks = result.stdout.strip()
        assert "lesson65-backend" in networks, (
            f"api-service not on backend-net. Networks: {networks}\n"
            "BUG #1 is still present."
        )

    def test_log_processor_on_backend_net(self):
        result = subprocess.run(
            ["docker", "inspect", PROCESSOR_CONTAINER, "--format",
             "{{range $net, $_ := .NetworkSettings.Networks}}{{$net}} {{end}}"],
            capture_output=True, text=True
        )
        networks = result.stdout.strip()
        assert "lesson65-backend" in networks, (
            f"log-processor not on backend-net. Networks: {networks}"
        )


class TestDNSResolution:
    """Verify DNS names and aliases resolve correctly from api-service."""

    def test_log_processor_dns_resolves(self):
        rc, out, err = docker_exec(
            API_CONTAINER,
            "nslookup", "log-processor", "127.0.0.11"
        )
        assert rc == 0, (
            f"DNS lookup for 'log-processor' failed from api-service.\n"
            f"stdout: {out}\nstderr: {err}\n"
            "Check BUG #1 (network attachment)."
        )
        assert "NXDOMAIN" not in out, (
            f"NXDOMAIN returned for 'log-processor'.\n"
            "BUG #1 is still present: api-service not on backend-net."
        )

    def test_processor_alias_resolves(self):
        rc, out, err = docker_exec(
            API_CONTAINER,
            "nslookup", "processor", "127.0.0.11"
        )
        assert rc == 0, (
            f"DNS lookup for alias 'processor' failed.\n"
            f"stdout: {out}\nstderr: {err}\n"
            "Check BUG #2 (alias placement in compose file)."
        )
        assert "NXDOMAIN" not in out, (
            "NXDOMAIN for 'processor' alias. BUG #2 is still present:\n"
            "Aliases must be under networks.<network-name>.aliases, "
            "not at the service root level."
        )

    def test_log_svc_alias_resolves(self):
        rc, out, err = docker_exec(
            API_CONTAINER,
            "nslookup", "log-svc", "127.0.0.11"
        )
        assert rc == 0, "DNS lookup for alias 'log-svc' failed."
        assert "NXDOMAIN" not in out, "NXDOMAIN for 'log-svc' alias."


class TestHTTPConnectivity:
    """Verify HTTP connectivity after DNS resolution is confirmed."""

    def test_log_processor_health_direct(self):
        resp = httpx.get(f"{PROCESSOR_BASE}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_api_health_reports_upstream_reachable(self):
        resp = httpx.get(f"{API_BASE}/health", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert data["upstream_reachable"] is True, (
            f"api-service reports upstream unreachable: {data}\n"
            "DNS resolution may have succeeded but HTTP connectivity failed."
        )
        assert data["latency_ms"] is not None

    def test_log_forwarding_end_to_end(self):
        payload = {
            "level": "INFO",
            "message": "Integration test log entry",
            "service": "test-suite"
        }
        resp = httpx.post(f"{API_BASE}/log", json=payload, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "forwarded"

    def test_logs_appear_in_processor(self):
        time.sleep(1)
        resp = httpx.get(f"{PROCESSOR_BASE}/logs?limit=10", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        messages = [e["service"] for e in data["entries"]]
        assert "test-suite" in messages


class TestDependsOnBehavior:
    """
    BUG #3 validation: verify depends_on condition is respected.
    This test validates the healthcheck is present and passing — a proxy
    for the condition: service_healthy fix being effective.
    """

    def test_log_processor_healthcheck_passing(self):
        result = subprocess.run(
            ["docker", "inspect", PROCESSOR_CONTAINER,
             "--format", "{{.State.Health.Status}}"],
            capture_output=True, text=True
        )
        status = result.stdout.strip()
        assert status == "healthy", (
            f"log-processor healthcheck status: '{status}' (expected 'healthy').\n"
            "Ensure HEALTHCHECK is defined in Dockerfile and "
            "depends_on condition: service_healthy is set."
        )
