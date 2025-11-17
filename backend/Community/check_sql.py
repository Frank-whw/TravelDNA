"""
Quick PostgreSQL sanity checker.

Usage:
    python check_sql.py --url postgresql://user:pass@host:port/dbname

If --url is omitted the script will fall back to the DATABASE_URL environment
variable. Requires psycopg (included in backend/Community/requirements.txt).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

# 关键：加载同级目录的.env文件
from dotenv import load_dotenv
# 获取脚本所在目录，然后加载该目录下的.env文件
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
# 使用 override=True 确保环境变量被正确加载
load_dotenv(env_path, override=True)

import psycopg
from psycopg import sql
from psycopg.rows import dict_row



DEFAULT_TABLES: Iterable[str] = (
    "mbti_type",
    "hobby",
    "destination",
    "schedule",
    "budget",
    "user",
    "team",
    "match_record",
    "message",
)


def format_dsn_info(conn: psycopg.Connection) -> str:
    info = conn.info
    return (
        f"user={info.user} host={info.host} port={info.port} "
        f"dbname={info.dbname} options={info.options or '-'}"
    )


def fetch_table_columns(conn: psycopg.Connection, table: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return cur.fetchall()


def describe_tables(conn: psycopg.Connection, tables: Iterable[str]) -> None:
    with conn.cursor(row_factory=dict_row) as cur:
        print("Table overview:")
        for name in tables:
            print(f"\n{name}")
            try:
                cur.execute(sql.SQL("SELECT COUNT(*) AS count FROM {}").format(sql.Identifier(name)))
                row = cur.fetchone()
                print(f"  Rows: {row['count']}")
            except psycopg.errors.UndefinedTable:
                conn.rollback()
                print("  <missing>")
                continue

            columns = fetch_table_columns(conn, name)
            if not columns:
                print("  Columns: <none>")
                continue

            print("  Columns:")
            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                default = col["column_default"] or "-"
                print(
                    f"    {col['column_name']:<20} {col['data_type']:<18} "
                    f"{nullable:<8} default={default}"
                )


def sample_users(conn: psycopg.Connection, limit: int = 5) -> None:
    with conn.cursor(row_factory=dict_row) as cur:
        try:
            cur.execute(
                sql.SQL(
                    """
                    SELECT id, name, gender, age, create_time
                    FROM {}
                    ORDER BY id
                    LIMIT %s
                    """
                ).format(sql.Identifier("user")),
                (limit,),
            )
        except psycopg.errors.UndefinedTable:
            conn.rollback()
            print("\nNo user table found, skip sampling.")
            return

        rows = cur.fetchall()
        if not rows:
            print("\nNo users found.")
            return

        print("\nSample users:")
        for row in rows:
            print(
                f"  id={row['id']:<3} name={row['name']:<12} "
                f"gender={row.get('gender','-'):<2} age={row.get('age','-'):<3} "
                f"created={row.get('create_time')}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PostgreSQL tables and row counts.")
    parser.add_argument(
        "--url",
        help="PostgreSQL connection string. "
        "If omitted, the DATABASE_URL environment variable will be used.",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Optional list of tables to inspect. "
        "Defaults to the main Community tables.",
    )
    args = parser.parse_args()

    dsn = args.url or os.getenv("DATABASE_URL")
    if not dsn:
        print("ERROR: Provide --url or set DATABASE_URL in the environment.", file=sys.stderr)
        sys.exit(1)

    tables = args.tables or DEFAULT_TABLES

    try:
        print(f"正在连接数据库...")
        print(f"连接字符串: {dsn.split('@')[0]}@***" if '@' in dsn else dsn)
        with psycopg.connect(dsn, connect_timeout=10, autocommit=True) as conn:
            print(f"✅ Connected to PostgreSQL ({format_dsn_info(conn)})\n")
            describe_tables(conn, tables)
            sample_users(conn)
    except psycopg.OperationalError as exc:
        print(f"❌ 数据库连接错误: {exc}", file=sys.stderr)
        print("\n可能的解决方案：", file=sys.stderr)
        print("1. 检查网络连接", file=sys.stderr)
        print("2. 确认 Supabase 数据库是否开启了连接池", file=sys.stderr)
        print("3. 检查 Supabase Dashboard -> Settings -> Database -> Connection Pooling", file=sys.stderr)
        print("4. 确认数据库密码和主机名是否正确", file=sys.stderr)
        sys.exit(2)
    except psycopg.Error as exc:
        print(f"Database error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

