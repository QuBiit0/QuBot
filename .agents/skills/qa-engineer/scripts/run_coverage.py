#!/usr/bin/env python3
"""
LMAgent - Test Coverage Report Generator
Genera reportes de cobertura de tests y verifica umbrales mínimos.

Uso:
    python run_coverage.py --framework pytest --threshold 80
    python run_coverage.py --framework jest --threshold 80
    python run_coverage.py --check-only --threshold 80
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def run_pytest_coverage(threshold: int) -> dict:
    """Ejecuta pytest con coverage y retorna métricas."""
    print("🧪 Ejecutando pytest con coverage...")

    cmd = [
        sys.executable, "-m", "pytest",
        "--cov", "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "-q",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

    if result.returncode not in (0, 1):  # 1 = test failures
        print(f"⚠️ Stderr: {result.stderr}")

    # Parse coverage.xml
    metrics = parse_coverage_xml("coverage.xml")
    metrics["tests_passed"] = result.returncode == 0
    metrics["threshold"] = threshold
    metrics["meets_threshold"] = metrics.get("line_rate", 0) >= threshold

    return metrics


def run_jest_coverage(threshold: int) -> dict:
    """Ejecuta jest con coverage y retorna métricas."""
    print("🧪 Ejecutando jest con coverage...")

    cmd = ["npx", "jest", "--coverage", "--coverageReporters=json-summary", "--silent"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

    # Parse coverage summary
    summary_path = Path("coverage/coverage-summary.json")
    if summary_path.exists():
        with open(summary_path) as f:
            data = json.load(f)
        total = data.get("total", {})
        line_rate = total.get("lines", {}).get("pct", 0)
        branch_rate = total.get("branches", {}).get("pct", 0)
    else:
        line_rate = 0
        branch_rate = 0

    return {
        "line_rate": line_rate,
        "branch_rate": branch_rate,
        "tests_passed": result.returncode == 0,
        "threshold": threshold,
        "meets_threshold": line_rate >= threshold,
    }


def parse_coverage_xml(filepath: str) -> dict:
    """Parsea coverage.xml (Cobertura format)."""
    path = Path(filepath)
    if not path.exists():
        return {"line_rate": 0, "branch_rate": 0, "error": "coverage.xml not found"}

    tree = ET.parse(filepath)
    root = tree.getroot()

    line_rate = float(root.get("line-rate", 0)) * 100
    branch_rate = float(root.get("branch-rate", 0)) * 100

    # Per-package breakdown
    packages = []
    for pkg in root.findall(".//package"):
        packages.append({
            "name": pkg.get("name", "unknown"),
            "line_rate": round(float(pkg.get("line-rate", 0)) * 100, 1),
            "branch_rate": round(float(pkg.get("branch-rate", 0)) * 100, 1),
        })

    return {
        "line_rate": round(line_rate, 1),
        "branch_rate": round(branch_rate, 1),
        "packages": packages,
    }


def print_report(metrics: dict):
    """Imprime reporte formateado."""
    print("\n" + "=" * 60)
    print("📊 COVERAGE REPORT")
    print("=" * 60)
    print(f"  Line Coverage:   {metrics.get('line_rate', 0):.1f}%")
    print(f"  Branch Coverage: {metrics.get('branch_rate', 0):.1f}%")
    print(f"  Threshold:       {metrics.get('threshold', 80)}%")
    print(f"  Tests Passed:    {'✅' if metrics.get('tests_passed') else '❌'}")
    print(f"  Meets Threshold: {'✅' if metrics.get('meets_threshold') else '❌'}")
    print("=" * 60)

    # Low coverage packages
    packages = metrics.get("packages", [])
    low = [p for p in packages if p["line_rate"] < metrics.get("threshold", 80)]
    if low:
        print(f"\n⚠️ Paquetes bajo el umbral ({metrics.get('threshold', 80)}%):")
        for p in sorted(low, key=lambda x: x["line_rate"]):
            print(f"  - {p['name']}: {p['line_rate']}%")


def main():
    parser = argparse.ArgumentParser(description="LMAgent Coverage Report Generator")
    parser.add_argument("--framework", "-f", choices=["pytest", "jest"], default="pytest")
    parser.add_argument("--threshold", "-t", type=int, default=80, help="Umbral mínimo (%)")
    parser.add_argument("--check-only", action="store_true", help="Solo verificar coverage.xml existente")

    args = parser.parse_args()

    if args.check_only:
        metrics = parse_coverage_xml("coverage.xml")
        metrics["threshold"] = args.threshold
        metrics["tests_passed"] = True
        metrics["meets_threshold"] = metrics.get("line_rate", 0) >= args.threshold
    elif args.framework == "pytest":
        metrics = run_pytest_coverage(args.threshold)
    elif args.framework == "jest":
        metrics = run_jest_coverage(args.threshold)

    print_report(metrics)
    sys.exit(0 if metrics.get("meets_threshold") else 1)


if __name__ == "__main__":
    main()
