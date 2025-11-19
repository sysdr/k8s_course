import subprocess
import json
import pytest

def test_configmap_created():
    """Test that ConfigMaps are created correctly"""
    result = subprocess.run(
        ["kubectl", "get", "configmap", "log-processor-config", 
         "-n", "log-analytics", "-o", "json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    config = json.loads(result.stdout)
    assert config["data"]["LOG_LEVEL"] in ["info", "debug", "warn"]

def test_secrets_exist():
    """Test that Secrets are created"""
    result = subprocess.run(
        ["kubectl", "get", "secret", "database-credentials",
         "-n", "log-analytics"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_rbac_configured():
    """Test that RBAC is properly configured"""
    result = subprocess.run(
        ["kubectl", "get", "rolebinding", "-n", "log-analytics"],
        capture_output=True, text=True
    )
    assert "log-processor-secrets-binding" in result.stdout

def test_env_injection():
    """Test that environment variables are injected"""
    result = subprocess.run(
        ["kubectl", "exec", "deploy/log-processor", "-n", "log-analytics",
         "--", "env"],
        capture_output=True, text=True
    )
    assert "DB_HOST=" in result.stdout
    assert "DB_PASSWORD=" in result.stdout

def test_volume_mount():
    """Test that config files are mounted"""
    result = subprocess.run(
        ["kubectl", "exec", "deploy/log-processor", "-n", "log-analytics",
         "--", "cat", "/etc/config/config.yaml"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "processing:" in result.stdout
