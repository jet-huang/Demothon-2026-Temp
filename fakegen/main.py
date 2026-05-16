from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from faker import Faker
from loguru import logger
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    text,
)
from sqlalchemy.engine import Engine

TYPE_MAP = {
    "integer": Integer,
    "string": String,
    "date": Date,
    "datetime": DateTime,
    "float": Float,
    "boolean": Boolean,
}

INTERNAL_GENERATORS = {"date_from_offset", "datetime_from_offset"}
VALID_UNITS = {"days", "hours", "minutes", "seconds"}
BATCH_SIZE = 500


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_table(schema: dict[str, Any], metadata: MetaData) -> Table:
    pk: set[str] = set(schema.get("primary_key", []) or [])
    cols: list[Column] = []
    for c in schema["columns"]:
        sa_type = TYPE_MAP[c["type"].lower()]
        cols.append(Column(c["name"], sa_type, primary_key=c["name"] in pk))
    return Table(schema["table"], metadata, *cols)


def _gen_value(faker: Faker, col: dict[str, Any], row: dict[str, Any]) -> Any:
    gen = col.get("generator")
    if gen is None:
        raise ValueError(
            f"column '{col['name']}' has no generator and was not set by an axis"
        )
    args = col.get("args", {}) or {}
    if gen == "date_from_offset":
        offset = int(row[args["source"]])
        return date.today() + timedelta(days=offset)
    if gen == "datetime_from_offset":
        unit = args.get("unit", "hours")
        if unit not in VALID_UNITS:
            raise ValueError(f"unit '{unit}' not in {sorted(VALID_UNITS)}")
        offset = int(row[args["source"]])
        anchor = datetime.now().replace(microsecond=0)
        return anchor + timedelta(**{unit: offset})
    if not hasattr(faker, gen):
        raise ValueError(f"unknown generator '{gen}' for column '{col['name']}'")
    return getattr(faker, gen)(**args)


def _axis_base_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    axes: list[tuple[str, list[Any]]] = []
    if "sequence" in schema and schema["sequence"]:
        seq = schema["sequence"]
        step = int(seq.get("step", 1))
        values = list(range(int(seq["min"]), int(seq["max"]) + 1, step))
        axes.append((seq["column"], values))
    for grp in schema.get("groups", []) or []:
        axes.append((grp["column"], list(grp["values"])))
    if not axes:
        return []
    rows: list[dict[str, Any]] = [{}]
    for col, values in axes:
        rows = [{**r, col: v} for r in rows for v in values]
    return rows


def _generate_rows(schema: dict[str, Any], faker: Faker) -> list[dict[str, Any]]:
    base_rows = _axis_base_rows(schema)
    if not base_rows:
        base_rows = [{} for _ in range(int(schema.get("rows", 100)))]
    rows: list[dict[str, Any]] = []
    for base in base_rows:
        row: dict[str, Any] = dict(base)
        for col in schema["columns"]:
            if col["name"] in row:
                continue
            row[col["name"]] = _gen_value(faker, col, row)
        rows.append(row)
    return rows


def _offset_columns(schema: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in schema["columns"]:
        gen = c.get("generator")
        if gen in INTERNAL_GENERATORS:
            args = c.get("args", {}) or {}
            out.append(
                {
                    "name": c["name"],
                    "source": args["source"],
                    "generator": gen,
                    "unit": args.get("unit", "days" if gen == "date_from_offset" else "hours"),
                }
            )
    return out


def cmd_generate(db_cfg: dict[str, Any], schema: dict[str, Any]) -> None:
    engine: Engine = create_engine(db_cfg["url"])
    metadata = MetaData()
    table = _build_table(schema, metadata)

    if db_cfg.get("truncate", False):
        metadata.drop_all(engine)
        logger.info("dropped table '{}' (truncate=true)", table.name)
    if db_cfg.get("create_if_missing", True):
        metadata.create_all(engine)
        logger.info("ensured table '{}' exists", table.name)

    with engine.begin() as conn:
        if db_cfg.get("truncate", False):
            conn.execute(delete(table))

        faker = Faker(schema.get("locale", "en_US"))
        rows = _generate_rows(schema, faker)
        for i in range(0, len(rows), BATCH_SIZE):
            conn.execute(table.insert(), rows[i : i + BATCH_SIZE])
        logger.info("inserted {} rows into '{}'", len(rows), table.name)


def _refresh_sql(dialect: str, table: str, col: dict[str, Any]) -> str:
    gen = col["generator"]
    src = col["source"]
    if gen == "date_from_offset":
        if dialect == "sqlite":
            return f"UPDATE {table} SET {col['name']} = date('now', 'localtime', {src} || ' days')"
        if dialect in {"postgresql", "postgres"}:
            return (
                f"UPDATE {table} SET {col['name']} = "
                f"CURRENT_DATE + ({src} * INTERVAL '1 day')"
            )
    if gen == "datetime_from_offset":
        unit = col["unit"]
        if dialect == "sqlite":
            return (
                f"UPDATE {table} SET {col['name']} = "
                f"datetime('now', 'localtime', {src} || ' {unit}')"
            )
        if dialect in {"postgresql", "postgres"}:
            return (
                f"UPDATE {table} SET {col['name']} = "
                f"NOW() + ({src} * INTERVAL '1 {unit.rstrip('s')}')"
            )
    raise NotImplementedError(f"refresh not implemented for {gen} on '{dialect}'")


def cmd_refresh(db_cfg: dict[str, Any], schema: dict[str, Any]) -> None:
    engine: Engine = create_engine(db_cfg["url"])
    table_name = schema["table"]
    cols = _offset_columns(schema)
    if not cols:
        logger.warning("no offset-driven columns in schema; nothing to refresh")
        return

    dialect = engine.dialect.name
    with engine.begin() as conn:
        for col in cols:
            sql = _refresh_sql(dialect, table_name, col)
            result = conn.execute(text(sql))
            logger.info(
                "refreshed {}.{} from {} ({}; {} rows)",
                table_name,
                col["name"],
                col["source"],
                col["generator"],
                result.rowcount,
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="fakegen")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "refresh"):
        sp = sub.add_parser(name)
        sp.add_argument("--db-config", type=Path, required=True)
        sp.add_argument("--schema", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    db_cfg = _load_yaml(args.db_config)
    schema = _load_yaml(args.schema)
    if args.command == "generate":
        cmd_generate(db_cfg, schema)
    elif args.command == "refresh":
        cmd_refresh(db_cfg, schema)
    return 0


if __name__ == "__main__":
    sys.exit(main())
