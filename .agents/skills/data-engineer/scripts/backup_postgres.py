#!/usr/bin/env python3
"""
LMAgent - Database Backup & Restore Script (PostgreSQL)
Crea backups comprimidos y restaura bases de datos PostgreSQL.

Uso:
    python backup_postgres.py backup --db mydb --output ./backups/
    python backup_postgres.py restore --db mydb --file ./backups/mydb_20240121.sql.gz
    python backup_postgres.py list --dir ./backups/
    python backup_postgres.py clean --dir ./backups/ --keep 7

Requiere: pg_dump y pg_restore en el PATH.
Las credenciales se leen de variables de entorno.
"""

import argparse
import gzip
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_db_config() -> dict:
    """Obtiene configuración de DB desde variables de entorno."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def backup(db_name: str, output_dir: str) -> str:
    """Crea un backup comprimido de la base de datos."""
    config = get_db_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{db_name}_{timestamp}.sql.gz"
    filepath = output_path / filename

    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]

    print(f"📦 Creando backup de '{db_name}'...")

    # pg_dump → gzip
    pg_dump_cmd = [
        "pg_dump",
        "-h", config["host"],
        "-p", config["port"],
        "-U", config["user"],
        "-d", db_name,
        "--format=plain",
        "--no-owner",
        "--no-privileges",
    ]

    try:
        result = subprocess.run(
            pg_dump_cmd,
            capture_output=True,
            env=env,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"❌ Error en pg_dump: {result.stderr.decode()}")
            sys.exit(1)

        with gzip.open(filepath, "wb") as f:
            f.write(result.stdout)

        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"✅ Backup creado: {filepath} ({size_mb:.1f} MB)")
        return str(filepath)

    except subprocess.TimeoutExpired:
        print("❌ Timeout: el backup tardó más de 5 minutos")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ pg_dump no encontrado. Verifica que PostgreSQL esté instalado.")
        sys.exit(1)


def restore(db_name: str, backup_file: str):
    """Restaura una base de datos desde un backup."""
    config = get_db_config()
    filepath = Path(backup_file)

    if not filepath.exists():
        print(f"❌ Archivo no encontrado: {filepath}")
        sys.exit(1)

    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]

    print(f"🔄 Restaurando backup en '{db_name}' desde {filepath.name}...")

    # Descomprimir si es .gz
    if filepath.suffix == ".gz":
        with gzip.open(filepath, "rb") as f:
            sql_content = f.read()
    else:
        sql_content = filepath.read_bytes()

    psql_cmd = [
        "psql",
        "-h", config["host"],
        "-p", config["port"],
        "-U", config["user"],
        "-d", db_name,
    ]

    try:
        result = subprocess.run(
            psql_cmd,
            input=sql_content,
            capture_output=True,
            env=env,
            timeout=600,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode()
            if "ERROR" in stderr:
                print(f"⚠️ Restauración completada con errores:\n{stderr[:500]}")
            else:
                print(f"✅ Restauración completada exitosamente.")
        else:
            print(f"✅ Restauración completada exitosamente.")

    except subprocess.TimeoutExpired:
        print("❌ Timeout: la restauración tardó más de 10 minutos")
        sys.exit(1)


def list_backups(backup_dir: str):
    """Lista los backups disponibles."""
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        print(f"❌ Directorio no encontrado: {backup_path}")
        sys.exit(1)

    backups = sorted(backup_path.glob("*.sql*"), reverse=True)

    if not backups:
        print("📂 No hay backups disponibles.")
        return

    print(f"\n📂 Backups en {backup_path}:\n")
    print(f"{'Archivo':<45} {'Tamaño':<12} {'Fecha'}")
    print("-" * 75)

    for b in backups:
        size_mb = b.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{b.name:<45} {size_mb:>8.1f} MB   {mod_time}")


def clean_old_backups(backup_dir: str, keep: int = 7):
    """Elimina backups antiguos, manteniendo los N más recientes."""
    backup_path = Path(backup_dir)
    backups = sorted(backup_path.glob("*.sql*"), key=lambda p: p.stat().st_mtime, reverse=True)

    to_delete = backups[keep:]

    if not to_delete:
        print(f"✅ No hay backups para eliminar (manteniendo últimos {keep}).")
        return

    for b in to_delete:
        b.unlink()
        print(f"🗑️  Eliminado: {b.name}")

    print(f"✅ Eliminados {len(to_delete)} backups. Mantenidos: {keep}.")


def main():
    parser = argparse.ArgumentParser(
        description="LMAgent PostgreSQL Backup/Restore"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # backup
    p_backup = sub.add_parser("backup", help="Crear backup")
    p_backup.add_argument("--db", required=True, help="Nombre de la base de datos")
    p_backup.add_argument("--output", default="./backups", help="Directorio de salida")

    # restore
    p_restore = sub.add_parser("restore", help="Restaurar backup")
    p_restore.add_argument("--db", required=True, help="Nombre de la base de datos")
    p_restore.add_argument("--file", required=True, help="Archivo de backup")

    # list
    p_list = sub.add_parser("list", help="Listar backups")
    p_list.add_argument("--dir", default="./backups", help="Directorio de backups")

    # clean
    p_clean = sub.add_parser("clean", help="Limpiar backups antiguos")
    p_clean.add_argument("--dir", default="./backups", help="Directorio de backups")
    p_clean.add_argument("--keep", type=int, default=7, help="Cantidad a mantener")

    args = parser.parse_args()

    if args.command == "backup":
        backup(args.db, args.output)
    elif args.command == "restore":
        restore(args.db, args.file)
    elif args.command == "list":
        list_backups(args.dir)
    elif args.command == "clean":
        clean_old_backups(args.dir, args.keep)


if __name__ == "__main__":
    main()
