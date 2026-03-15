#!/usr/bin/env python3
"""
LMAgent - Docker Healthcheck Script
Verifica la salud de servicios Docker: API, DB, Redis.

Uso:
    python docker_healthcheck.py --service api --url http://localhost:8000/health
    python docker_healthcheck.py --service postgres --host localhost --port 5432
    python docker_healthcheck.py --service redis --host localhost --port 6379
    python docker_healthcheck.py --all
"""

import argparse
import json
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime


def check_http(url: str, timeout: int = 5) -> dict:
    """Verifica un endpoint HTTP."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            return {
                "status": "healthy",
                "code": resp.status,
                "response": body[:200],
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def check_tcp(host: str, port: int, timeout: int = 5) -> dict:
    """Verifica conectividad TCP a un servicio."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return {"status": "healthy", "host": host, "port": port}
    except Exception as e:
        return {"status": "unhealthy", "host": host, "port": port, "error": str(e)}


def check_docker_containers() -> dict:
    """Verifica el estado de contenedores Docker."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                containers.append({
                    "name": parts[0] if len(parts) > 0 else "unknown",
                    "status": parts[1] if len(parts) > 1 else "unknown",
                    "ports": parts[2] if len(parts) > 2 else "",
                })
        return {"status": "ok", "containers": containers}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_disk_space() -> dict:
    """Verifica espacio en disco disponible."""
    try:
        result = subprocess.run(
            ["docker", "system", "df", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=10
        )
        return {"status": "ok", "output": result.stdout.strip()[:500]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="LMAgent Docker Healthcheck — Verifica salud de servicios"
    )
    parser.add_argument("--service", "-s", choices=["api", "postgres", "redis", "docker"])
    parser.add_argument("--url", default="http://localhost:8000/health")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--all", action="store_true", help="Verificar todos los servicios")

    args = parser.parse_args()

    results = {"timestamp": datetime.now().isoformat(), "checks": {}}

    if args.all or args.service == "api":
        results["checks"]["api"] = check_http(args.url)

    if args.all or args.service == "postgres":
        results["checks"]["postgres"] = check_tcp(args.host, 5432)

    if args.all or args.service == "redis":
        results["checks"]["redis"] = check_tcp(args.host, 6379)

    if args.all or args.service == "docker":
        results["checks"]["docker"] = check_docker_containers()
        results["checks"]["disk"] = check_disk_space()

    if args.all and not args.service:
        results["checks"]["api"] = check_http(args.url)
        results["checks"]["postgres"] = check_tcp(args.host, 5432)
        results["checks"]["redis"] = check_tcp(args.host, 6379)
        results["checks"]["docker"] = check_docker_containers()

    # Output
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Exit code
    all_healthy = all(
        c.get("status") in ("healthy", "ok")
        for c in results["checks"].values()
    )
    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
