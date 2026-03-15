#!/usr/bin/env python3
"""
LMAgent - Security Audit Script
Audita un proyecto buscando vulnerabilidades comunes.

Uso:
    python audit_security.py --path ./mi-proyecto
    python audit_security.py --path ./mi-proyecto --check secrets
    python audit_security.py --path ./mi-proyecto --check dependencies
    python audit_security.py --path ./mi-proyecto --check all
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# Patrones de secretos comunes
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "API Key"),
    (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "Secret Key"),
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}', "Password"),
    (r'(?i)(token)\s*[=:]\s*["\']?[A-Za-z0-9_\-\.]{20,}', "Token"),
    (r'(?i)(aws[_-]?access[_-]?key)\s*[=:]\s*["\']?AKIA[A-Z0-9]{12,}', "AWS Access Key"),
    (r'(?i)(private[_-]?key)\s*[=:]\s*["\']?-----BEGIN', "Private Key"),
    (r'postgresql://[^:]+:[^@]+@', "Database Connection String"),
    (r'mongodb(\+srv)?://[^:]+:[^@]+@', "MongoDB Connection String"),
    (r'redis://[^:]*:[^@]+@', "Redis Connection String"),
]

# Extensiones a escanear
SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".yaml", ".yml",
    ".json", ".toml", ".cfg", ".ini", ".conf", ".sh",
}

# Archivos/directorios a ignorar
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "coverage",
}


def scan_secrets(project_path: Path) -> list[dict]:
    """Escanea archivos buscando secretos hardcodeados."""
    findings = []

    for root, dirs, files in os.walk(project_path):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            filepath = Path(root) / filename

            # Solo escanear extensiones relevantes
            if filepath.suffix not in SCAN_EXTENSIONS:
                continue

            # Ignorar archivos .example y .template
            if ".example" in filepath.name or ".template" in filepath.name:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                for line_num, line in enumerate(content.split("\n"), 1):
                    for pattern, secret_type in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            # Verificar que no es un placeholder
                            if any(ph in line.lower() for ph in [
                                "example", "placeholder", "change-me",
                                "your-", "xxx", "todo", "fixme",
                                "os.getenv", "process.env", "environ",
                            ]):
                                continue

                            findings.append({
                                "type": secret_type,
                                "file": str(filepath.relative_to(project_path)),
                                "line": line_num,
                                "severity": "HIGH",
                                "snippet": line.strip()[:80] + "...",
                            })
            except (UnicodeDecodeError, PermissionError):
                continue

    return findings


def check_env_file(project_path: Path) -> list[dict]:
    """Verifica que no haya archivos .env versionados."""
    findings = []

    env_files = list(project_path.glob("**/.env"))
    env_files += list(project_path.glob("**/.env.local"))
    env_files += list(project_path.glob("**/.env.production"))

    for env_file in env_files:
        if ".git" not in str(env_file):
            findings.append({
                "type": "Unprotected .env file",
                "file": str(env_file.relative_to(project_path)),
                "severity": "MEDIUM",
                "recommendation": "Asegurar que .env esté en .gitignore",
            })

    # Verificar .gitignore
    gitignore = project_path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            findings.append({
                "type": ".env not in .gitignore",
                "file": ".gitignore",
                "severity": "HIGH",
                "recommendation": "Agregar .env a .gitignore",
            })

    return findings


def check_dependencies(project_path: Path) -> list[dict]:
    """Verifica vulnerabilidades en dependencias."""
    findings = []

    # Python: pip audit
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "audit", "-r", str(req_file)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                findings.append({
                    "type": "Python dependency vulnerabilities",
                    "output": result.stdout[:500],
                    "severity": "HIGH",
                })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            findings.append({
                "type": "pip-audit not available",
                "severity": "INFO",
                "recommendation": "Instalar: pip install pip-audit",
            })

    # Node: npm audit
    pkg_file = project_path / "package.json"
    if pkg_file.exists():
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True, text=True,
                cwd=str(project_path), timeout=60
            )
            if result.returncode != 0:
                try:
                    audit_data = json.loads(result.stdout)
                    vuln_count = audit_data.get("metadata", {}).get("vulnerabilities", {})
                    findings.append({
                        "type": "NPM dependency vulnerabilities",
                        "high": vuln_count.get("high", 0),
                        "critical": vuln_count.get("critical", 0),
                        "severity": "HIGH" if vuln_count.get("critical", 0) > 0 else "MEDIUM",
                    })
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return findings


def print_report(all_findings: dict):
    """Imprime el reporte de auditoría."""
    print("\n" + "=" * 60)
    print("🛡️  SECURITY AUDIT REPORT")
    print("=" * 60)

    total = sum(len(f) for f in all_findings.values())

    for category, findings in all_findings.items():
        if findings:
            print(f"\n🔍 {category} ({len(findings)} hallazgos)")
            print("-" * 40)
            for f in findings:
                severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️"}.get(
                    f.get("severity", "INFO"), "ℹ️"
                )
                print(f"  {severity_icon} [{f.get('severity', 'INFO')}] {f.get('type', 'Unknown')}")
                if "file" in f:
                    print(f"     File: {f['file']}")
                    if "line" in f:
                        print(f"     Line: {f['line']}")
                if "recommendation" in f:
                    print(f"     Fix: {f['recommendation']}")

    high_count = sum(1 for fs in all_findings.values() for f in fs if f.get("severity") == "HIGH")
    print(f"\n{'=' * 60}")
    print(f"Total: {total} hallazgos ({high_count} HIGH)")
    print(f"{'=' * 60}")

    return high_count


def main():
    parser = argparse.ArgumentParser(description="LMAgent Security Audit")
    parser.add_argument("--path", "-p", default=".", help="Ruta del proyecto")
    parser.add_argument(
        "--check", "-c",
        choices=["secrets", "env", "dependencies", "all"],
        default="all",
        help="Tipo de check"
    )

    args = parser.parse_args()
    project_path = Path(args.path).resolve()

    if not project_path.exists():
        print(f"❌ Ruta no encontrada: {project_path}")
        sys.exit(1)

    all_findings = {}

    if args.check in ("secrets", "all"):
        all_findings["Secretos Hardcodeados"] = scan_secrets(project_path)

    if args.check in ("env", "all"):
        all_findings["Archivos .env"] = check_env_file(project_path)

    if args.check in ("dependencies", "all"):
        all_findings["Dependencias Vulnerables"] = check_dependencies(project_path)

    high_count = print_report(all_findings)
    sys.exit(1 if high_count > 0 else 0)


if __name__ == "__main__":
    main()
