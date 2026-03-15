#!/usr/bin/env python3
"""
LMAgent - Performance Profiling Script
Perfilado rápido de endpoints HTTP con métricas de latencia.

Uso:
    python profile_endpoint.py --url http://localhost:8000/api/users --requests 100
    python profile_endpoint.py --url http://localhost:8000/api/users --requests 50 --concurrent 10
    python profile_endpoint.py --url http://localhost:8000/health --requests 200 --method GET
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def single_request(url: str, method: str = "GET", timeout: int = 30) -> dict:
    """Ejecuta un request y mide tiempo de respuesta."""
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            return {
                "status": resp.status,
                "duration_ms": round(elapsed, 2),
                "size_bytes": len(body),
                "error": None,
            }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "status": 0,
            "duration_ms": round(elapsed, 2),
            "size_bytes": 0,
            "error": str(e),
        }


def run_benchmark(url: str, num_requests: int, concurrency: int, method: str) -> dict:
    """Ejecuta benchmark de un endpoint."""
    print(f"\n🏎️  Benchmarking: {method} {url}")
    print(f"   Requests: {num_requests} | Concurrency: {concurrency}")
    print(f"   Started: {datetime.now().isoformat()}")
    print("-" * 50)

    results = []
    start_total = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(single_request, url, method)
            for _ in range(num_requests)
        ]
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            # Progress indicator
            if (i + 1) % max(1, num_requests // 10) == 0:
                pct = (i + 1) / num_requests * 100
                print(f"   Progress: {pct:.0f}% ({i + 1}/{num_requests})")

    total_time = time.perf_counter() - start_total

    # Calcular métricas
    durations = [r["duration_ms"] for r in results if r["error"] is None]
    errors = [r for r in results if r["error"] is not None]

    if not durations:
        return {"error": "Todos los requests fallaron", "errors": len(errors)}

    durations_sorted = sorted(durations)

    metrics = {
        "url": url,
        "method": method,
        "total_requests": num_requests,
        "successful": len(durations),
        "failed": len(errors),
        "error_rate": round(len(errors) / num_requests * 100, 2),
        "total_time_s": round(total_time, 2),
        "rps": round(num_requests / total_time, 1),
        "latency": {
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2),
            "mean_ms": round(statistics.mean(durations), 2),
            "median_ms": round(statistics.median(durations), 2),
            "stdev_ms": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0,
            "p90_ms": round(durations_sorted[int(len(durations_sorted) * 0.90)], 2),
            "p95_ms": round(durations_sorted[int(len(durations_sorted) * 0.95)], 2),
            "p99_ms": round(durations_sorted[int(len(durations_sorted) * 0.99)], 2),
        },
    }

    return metrics


def print_report(metrics: dict):
    """Imprime reporte de performance."""
    print("\n" + "=" * 50)
    print("📊 PERFORMANCE REPORT")
    print("=" * 50)

    if "error" in metrics:
        print(f"  ❌ {metrics['error']}")
        return

    print(f"  URL:       {metrics['url']}")
    print(f"  Method:    {metrics['method']}")
    print(f"  Requests:  {metrics['total_requests']}")
    print(f"  Errors:    {metrics['failed']} ({metrics['error_rate']}%)")
    print(f"  RPS:       {metrics['rps']}")
    print(f"  Total:     {metrics['total_time_s']}s")

    lat = metrics["latency"]
    print(f"\n  Latency:")
    print(f"    Min:    {lat['min_ms']:.1f}ms")
    print(f"    Mean:   {lat['mean_ms']:.1f}ms")
    print(f"    Median: {lat['median_ms']:.1f}ms")
    print(f"    P90:    {lat['p90_ms']:.1f}ms")
    print(f"    P95:    {lat['p95_ms']:.1f}ms")
    print(f"    P99:    {lat['p99_ms']:.1f}ms")
    print(f"    Max:    {lat['max_ms']:.1f}ms")
    print(f"    Stdev:  {lat['stdev_ms']:.1f}ms")

    # Evaluación
    print(f"\n  Assessment:")
    p95 = lat["p95_ms"]
    if p95 < 200:
        print(f"    ✅ P95 < 200ms — Excelente")
    elif p95 < 500:
        print(f"    ✅ P95 < 500ms — Bueno")
    elif p95 < 1000:
        print(f"    ⚠️  P95 < 1000ms — Aceptable, considerar optimización")
    else:
        print(f"    ❌ P95 > 1000ms — Requiere optimización urgente")

    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="LMAgent Endpoint Profiler")
    parser.add_argument("--url", "-u", required=True, help="URL del endpoint")
    parser.add_argument("--requests", "-n", type=int, default=100, help="Número de requests")
    parser.add_argument("--concurrent", "-c", type=int, default=5, help="Concurrencia")
    parser.add_argument("--method", "-m", default="GET", help="HTTP method")
    parser.add_argument("--json", action="store_true", help="Output en JSON")

    args = parser.parse_args()
    metrics = run_benchmark(args.url, args.requests, args.concurrent, args.method)

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_report(metrics)

    # Exit code basado en P95
    if metrics.get("latency", {}).get("p95_ms", 9999) > 1000:
        sys.exit(1)


if __name__ == "__main__":
    main()
