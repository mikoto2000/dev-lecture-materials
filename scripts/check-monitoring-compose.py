#!/usr/bin/env python3
"""Validate the normalized Compose model with Docker's official Compose parser.

Requires Docker CLI + Compose v2, but does not require a running Docker daemon.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "docs/public/monitoring-intro/lab"


def validate(config):
    assert config["name"] == "monitoring-intro-lab", "unexpected project name"
    services = config["services"]
    assert set(services) == {"kuma", "demo", "notification-sink"}
    assert services["kuma"]["image"] == "louislam/uptime-kuma:2.5.5"
    assert set(config["volumes"]) == {"kumadata", "labstate"}
    expected_ports = {"kuma": ("13001", 3001), "demo": ("18080", 18080)}
    expected_volumes = {"kuma": ("kumadata", "/app/data"), "demo": ("labstate", "/lab/.state")}
    for name, service in services.items():
        for forbidden in ("container_name", "network_mode", "privileged", "devices", "pid", "ipc"):
            assert forbidden not in service, f"{name}: forbidden setting {forbidden}"
        assert not service.get("depends_on"), f"{name}: lifecycle must be independent"
        if name in expected_ports:
            ports = service.get("ports", [])
            assert len(ports) == 1, f"{name}: expected one loopback binding"
            port = ports[0]
            assert port["host_ip"] == "127.0.0.1"
            assert (str(port["published"]), port["target"]) == expected_ports[name]
            assert port["protocol"] == "tcp"
        else:
            assert not service.get("ports"), "notification receiver must not publish a host port"
        volumes = service.get("volumes", [])
        if name in expected_volumes:
            assert len(volumes) == 1
            volume = volumes[0]
            assert volume["type"] == "volume", "no host bind mounts"
            assert (volume["source"], volume["target"]) == expected_volumes[name]
        else:
            assert not volumes
        assert service["logging"]["options"] == {"max-size": "1m", "max-file": "3"}
    assert services["notification-sink"]["profiles"] == ["notifications"]
    assert services["notification-sink"]["command"] == ["python", "notification_sink.py"]
    for name in ("demo", "notification-sink"):
        service = services[name]
        assert Path(service["build"]["context"]).resolve() == LAB.resolve()
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in service["security_opt"]
    dockerfile = (LAB / "Dockerfile").read_text()
    assert dockerfile.startswith("FROM python:3.12-slim-bookworm\n")
    assert 'CMD ["python", "container_start.py"]' in dockerfile
    assert "ENTRYPOINT" not in dockerfile, "one-off reset must bypass app startup"
    assert "USER 10001:10001" in dockerfile


def main():
    try:
        result = subprocess.run(["docker", "compose", "--project-directory", str(LAB),
                                 "--profile", "notifications", "config", "--format", "json"],
                                check=True, capture_output=True, text=True, timeout=30)
        validate(json.loads(result.stdout))
    except (OSError, subprocess.SubprocessError, AssertionError, KeyError, ValueError) as exc:
        raise SystemExit(f"FAIL: Compose validation needs Docker CLI + Compose v2: {exc}") from exc
    print("PASS: official Compose model, pinned Kuma, loopback ports, scoped volumes, independent sink")


if __name__ == "__main__":
    main()
