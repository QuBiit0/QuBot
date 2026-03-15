#!/usr/bin/env python3
"""
LMAgent - Frontend Bundle Size Auditor
Verifica el tamaño del bundle y detecta dependencias pesadas.

Uso:
    python audit_bundle.py --dir ./dist --threshold 500
    python audit_bundle.py --dir ./.next --threshold 300 --format json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def analyze_directory(dist_path: Path) -> dict:
    """Analiza el tamaño de archivos en el directorio de build."""
    file_sizes = []
    total_size = 0

    for root, dirs, files in os.walk(dist_path):
        for f in files:
            filepath = Path(root) / f
            try:
                size = filepath.stat().st_size
                total_size += size
                file_sizes.append({
                    "file": str(filepath.relative_to(dist_path)),
                    "size_bytes": size,
                    "size_kb": round(size / 1024, 1),
                    "type": filepath.suffix,
                })
            except OSError:
                continue

    # Agrupar por tipo
    by_type = {}
    for f in file_sizes:
        ext = f["type"]
        by_type.setdefault(ext, {"count": 0, "total_kb": 0})
        by_type[ext]["count"] += 1
        by_type[ext]["total_kb"] += f["size_kb"]

    # Top 10 archivos más pesados
    top_files = sorted(file_sizes, key=lambda x: x["size_bytes"], reverse=True)[:10]

    return {
        "total_size_kb": round(total_size / 1024, 1),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_files": len(file_sizes),
        "by_type": dict(sorted(by_type.items(), key=lambda x: x[1]["total_kb"], reverse=True)),
        "top_files": top_files,
        "js_files": [f for f in file_sizes if f["type"] in (".js", ".mjs")],
        "css_files": [f for f in file_sizes if f["type"] == ".css"],
    }


def check_thresholds(analysis: dict, threshold_kb: int) -> list:
    """Verifica umbrales y genera advertencias."""
    warnings = []

    # Total bundle size
    if analysis["total_size_kb"] > threshold_kb:
        warnings.append({
            "severity": "HIGH",
            "message": f"Bundle total ({analysis['total_size_kb']}KB) excede umbral ({threshold_kb}KB)",
        })

    # Archivos JS individuales > 200KB
    for f in analysis.get("js_files", []):
        if f["size_kb"] > 200:
            warnings.append({
                "severity": "MEDIUM",
                "message": f"JS {f['file']} ({f['size_kb']}KB) > 200KB — considerar code splitting",
            })

    # CSS > 50KB
    for f in analysis.get("css_files", []):
        if f["size_kb"] > 50:
            warnings.append({
                "severity": "LOW",
                "message": f"CSS {f['file']} ({f['size_kb']}KB) > 50KB — considerar purging",
            })

    return warnings


def print_report(analysis: dict, warnings: list, threshold_kb: int):
    """Imprime reporte formateado."""
    print("\n" + "=" * 55)
    print("📦 BUNDLE SIZE AUDIT")
    print("=" * 55)
    print(f"  Total:     {analysis['total_size_mb']} MB ({analysis['total_size_kb']} KB)")
    print(f"  Files:     {analysis['total_files']}")
    print(f"  Threshold: {threshold_kb} KB")
    status = "✅ PASS" if analysis["total_size_kb"] <= threshold_kb else "❌ FAIL"
    print(f"  Status:    {status}")

    print(f"\n  By Type:")
    for ext, data in analysis["by_type"].items():
        print(f"    {ext or 'other':<8} {data['count']:>4} files   {data['total_kb']:>8.1f} KB")

    print(f"\n  Top 10 Largest Files:")
    for f in analysis["top_files"]:
        print(f"    {f['size_kb']:>8.1f} KB   {f['file']}")

    if warnings:
        print(f"\n  ⚠️  Warnings ({len(warnings)}):")
        for w in warnings:
            icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(w["severity"], "ℹ️")
            print(f"    {icon} {w['message']}")

    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="LMAgent Bundle Size Auditor")
    parser.add_argument("--dir", "-d", default="./dist", help="Build directory")
    parser.add_argument("--threshold", "-t", type=int, default=500, help="Max size (KB)")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()
    dist_path = Path(args.dir).resolve()

    if not dist_path.exists():
        print(f"❌ Directorio no encontrado: {dist_path}")
        sys.exit(1)

    analysis = analyze_directory(dist_path)
    warnings = check_thresholds(analysis, args.threshold)

    if args.format == "json":
        output = {**analysis, "warnings": warnings, "threshold_kb": args.threshold}
        print(json.dumps(output, indent=2))
    else:
        print_report(analysis, warnings, args.threshold)

    sys.exit(0 if analysis["total_size_kb"] <= args.threshold else 1)


if __name__ == "__main__":
    main()
