from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import mysql.connector
from mysql.connector import Error


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "mysql_config.json"
DEFAULT_SQL_PATH = PROJECT_ROOT / "gastrosoft_mysql.sql"


@dataclass(slots=True)
class MySQLConfig:
    host: str = "127.0.0.1"
    port: int = 3307
    user: str = "root"
    password: str = ""
    database: str = "gastrosoft_course"
    charset: str = "utf8mb4"

    @classmethod
    def from_file(cls, path: Path) -> "MySQLConfig":
        if not path.exists():
            raise FileNotFoundError(
                f"Файл конфигурации не найден: {path}. Создай его по примеру mysql_config.example.json"
            )

        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            host=raw.get("host", cls.host),
            port=int(raw.get("port", cls.port)),
            user=raw.get("user", cls.user),
            password=raw.get("password", cls.password),
            database=raw.get("database", cls.database),
            charset=raw.get("charset", cls.charset),
        )

    def as_connector_kwargs(self, include_database: bool = True) -> dict:
        kwargs = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "charset": self.charset,
            "use_unicode": True,
            "autocommit": False,
        }
        if include_database:
            kwargs["database"] = self.database
        return kwargs


class MySQLConnectionManager:
    def __init__(
        self,
        config_path: Path | None = None,
        sql_path: Path | None = None,
    ) -> None:
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.sql_path = sql_path or DEFAULT_SQL_PATH
        self.config = MySQLConfig.from_file(self.config_path)

    def connect(self, include_database: bool = True):
        return mysql.connector.connect(**self.config.as_connector_kwargs(include_database=include_database))

    def test_connection(self) -> tuple[bool, str]:
        try:
            with self.connect(include_database=False) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
            return True, f"MySQL подключен успешно. Версия сервера: {version}"
        except Error as exc:
            return False, f"Ошибка подключения к MySQL: {exc}"

    def test_database_access(self) -> tuple[bool, str]:
        try:
            with self.connect(include_database=True) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT DATABASE()")
                    database_name = cursor.fetchone()[0]
            return True, f"База данных доступна: {database_name}"
        except Error as exc:
            return False, f"Ошибка доступа к базе данных {self.config.database}: {exc}"

    def initialize_schema(self) -> tuple[bool, str]:
        if not self.sql_path.exists():
            return False, f"SQL-файл не найден: {self.sql_path}"

        return self.execute_sql_file(self.sql_path, include_database=False)

    def execute_sql_file(self, sql_path: Path, include_database: bool = True) -> tuple[bool, str]:
        if not sql_path.exists():
            return False, f"SQL-файл не найден: {sql_path}"

        script = sql_path.read_text(encoding="utf-8")
        statements = _split_sql_script(script)
        if not statements:
            return False, "SQL-файл пустой или не содержит исполняемых команд."

        try:
            with self.connect(include_database=include_database) as connection:
                with connection.cursor() as cursor:
                    for statement in statements:
                        cursor.execute(statement)
                        if cursor.with_rows:
                            for row in cursor.fetchall():
                                print(" | ".join(str(value) for value in row))
                connection.commit()
            return True, f"SQL-файл {sql_path.name} успешно выполнен."
        except Error as exc:
            return False, f"Не удалось выполнить SQL-файл: {exc}"


def _split_sql_script(script: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--"):
            continue

        buffer.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(buffer).strip()
            if statement.endswith(";"):
                statement = statement[:-1]
            if statement:
                statements.append(statement)
            buffer = []

    if buffer:
        statement = "\n".join(buffer).strip()
        if statement:
            statements.append(statement)

    return statements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Подключение и инициализация MySQL для проекта GastroSoft."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Путь к mysql_config.json",
    )
    parser.add_argument(
        "--sql",
        default=str(DEFAULT_SQL_PATH),
        help="Путь к SQL-файлу схемы",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Применить SQL-схему из gastrosoft_mysql.sql",
    )
    parser.add_argument(
        "--test-db",
        action="store_true",
        help="Проверить доступ к указанной базе данных",
    )
    parser.add_argument(
        "--run-sql",
        help="Выполнить указанный SQL-файл через mysql_config.json без консольного клиента mysql",
    )
    args = parser.parse_args()

    manager = MySQLConnectionManager(
        config_path=Path(args.config),
        sql_path=Path(args.sql),
    )

    ok, message = manager.test_connection()
    print(message)
    if not ok:
        return 1

    if args.init:
        ok, message = manager.initialize_schema()
        print(message)
        if not ok:
            return 1

    if args.test_db:
        ok, message = manager.test_database_access()
        print(message)
        if not ok:
            return 1

    if args.run_sql:
        run_sql_path = Path(args.run_sql)
        if not run_sql_path.is_absolute():
            run_sql_path = PROJECT_ROOT / run_sql_path
        ok, message = manager.execute_sql_file(run_sql_path)
        print(message)
        if not ok:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
