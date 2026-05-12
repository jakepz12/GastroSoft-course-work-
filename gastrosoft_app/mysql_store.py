from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from mysql.connector import Error

from mysql_connection import DEFAULT_CONFIG_PATH, MySQLConnectionManager

from .data import DemoStore


ROLE_CODE_TO_RU = {
    "ADMIN": "Администратор системы",
    "DIRECTOR": "Директор",
    "CHEF": "Шеф-повар",
    "HALL_MANAGER": "Менеджер зала",
    "ACCOUNTANT": "Бухгалтер",
    "WAITER": "Официант",
    "COOK": "Повар",
    "CASHIER": "Кассир",
}

RU_ROLE_TO_CODE = {value: key for key, value in ROLE_CODE_TO_RU.items()}

RESERVATION_STATUS_TO_CODE = {
    "Ожидается": "ACTIVE",
    "Подтверждена": "ACTIVE",
    "Гость в зале": "ACTIVE",
    "Завершена": "COMPLETED",
    "Отменена": "CANCELLED",
    "Не пришел": "NO_SHOW",
}

ORDER_STATUS_TO_CODE = {
    "Принят": "ACCEPTED",
    "Готовится": "PREPARING",
    "Готов": "READY",
    "Выдан": "SERVED",
    "Закрыт": "CLOSED",
}

PAYMENT_TO_CODE = {
    "Наличные": "CASH",
    "Карта": "CARD",
    "QR-оплата": "ONLINE",
}

STOCK_OPERATION_TO_CODE = {
    "Поступление": "RECEIPT",
    "Списание": "WRITE_OFF",
    "Корректировка": "ADJUSTMENT_IN",
}


class MySQLBackedStore(DemoStore):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root
        self.mysql_enabled = False
        self.mysql_status = "MySQL: демо-режим, файл mysql_config.json не найден."
        self.manager: MySQLConnectionManager | None = None

        config_path = project_root / DEFAULT_CONFIG_PATH.name
        if not config_path.exists():
            return

        try:
            self.manager = MySQLConnectionManager(config_path=config_path)
            ok, message = self.manager.test_database_access()
            self.mysql_status = message
            if ok:
                self.mysql_enabled = True
                self.reload_from_mysql()
        except Exception as exc:
            self.mysql_enabled = False
            self.mysql_status = f"MySQL: демо-режим, {exc}"

    def reload_from_mysql(self) -> None:
        if not self.mysql_enabled:
            return

        self._load_roles()
        self._load_users()
        self._load_employees()
        self._load_tables()
        self._load_reservations()
        self._load_menu()
        self._load_inventory()
        self._load_kitchen_queue()
        self.recalculate_tables()

    def authenticate(self, login: str, password: str) -> dict | None:
        if self.mysql_enabled:
            user = self._authenticate_mysql(login, password)
            if user is not None:
                self.current_user = user
                return user

            if self._login_exists_in_mysql(login):
                return None

        return super().authenticate(login, password)

    def register_user(self, full_name: str, login: str, password: str, role: str) -> tuple[bool, str, dict | None]:
        if not self.mysql_enabled:
            return super().register_user(full_name, login, password, role)

        try:
            if self._login_exists_in_mysql(login):
                return False, "Логин уже занят в базе данных MySQL.", None

            role_id = self._get_id("employee_role", "role_id", "code", RU_ROLE_TO_CODE.get(role, "WAITER"))
            last_name, first_name, middle_name = _split_full_name(full_name)
            password_hash = _hash_password(password)

            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO employee (role_id, last_name, first_name, middle_name, is_active)
                        VALUES (%s, %s, %s, %s, 1)
                        """,
                        (role_id, last_name, first_name, middle_name),
                    )
                    employee_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO app_user (employee_id, login, password_hash, is_active)
                        VALUES (%s, %s, %s, 1)
                        """,
                        (employee_id, login, password_hash),
                    )
                    user_id = cursor.lastrowid
                connection.commit()

            user = {
                "user_id": user_id,
                "employee_id": employee_id,
                "full_name": full_name,
                "login": login,
                "password": password,
                "role": role,
            }
            self.users.append(user)
            self.employees.append({"name": full_name, "role": role, "skill": "Новый сотрудник", "status": "Свободен"})
            self.current_user = user
            return True, "Пользователь зарегистрирован в MySQL и вошел в систему.", user
        except Error as exc:
            return False, f"Ошибка записи пользователя в MySQL: {exc}", None

    def add_reservation(
        self, guest: str, phone: str, table: str, date_time: datetime, guests: int, status: str
    ) -> dict:
        reservation = super().add_reservation(guest, phone, table, date_time, guests, status)
        if not self.mysql_enabled:
            return reservation

        try:
            user_id = self._current_mysql_user_id()
            if user_id is None:
                return reservation

            status_id = self._get_id(
                "reservation_status",
                "reservation_status_id",
                "code",
                RESERVATION_STATUS_TO_CODE.get(status, "ACTIVE"),
            )
            table_id = self._get_id("restaurant_table", "table_id", "code", table)
            reserved_to = date_time + timedelta(hours=2)

            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO guest (full_name, phone)
                        VALUES (%s, %s)
                        """,
                        (guest, phone),
                    )
                    guest_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO reservation (
                            guest_id,
                            table_id,
                            reservation_status_id,
                            reserved_from,
                            reserved_to,
                            guest_count,
                            created_by_user_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (guest_id, table_id, status_id, date_time, reserved_to, guests, user_id),
                    )
                    reservation["reservation_id"] = cursor.lastrowid
                connection.commit()
        except Error:
            pass

        return reservation

    def set_reservation_status(self, index: int, status: str) -> str:
        message = super().set_reservation_status(index, status)
        if not self.mysql_enabled or index < 0 or index >= len(self.reservations):
            return message

        reservation_id = self.reservations[index].get("reservation_id")
        if reservation_id is None:
            return message

        try:
            status_id = self._get_id(
                "reservation_status",
                "reservation_status_id",
                "code",
                RESERVATION_STATUS_TO_CODE.get(status, "ACTIVE"),
            )
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE reservation SET reservation_status_id = %s WHERE reservation_id = %s",
                        (status_id, reservation_id),
                    )
                connection.commit()
        except Error:
            pass
        return message

    def send_draft_to_kitchen(self, table_code: str, payment_method: str) -> tuple[bool, str]:
        draft_snapshot = [item.copy() for item in self.order_draft]
        success, message = super().send_draft_to_kitchen(table_code, payment_method)
        if not success or not self.mysql_enabled:
            return success, message

        try:
            user_id = self._current_mysql_user_id()
            if user_id is None:
                return success, message

            table_id = self._get_id("restaurant_table", "table_id", "code", table_code)
            order_status_id = self._get_id("order_status", "order_status_id", "code", "ACCEPTED")
            item_status_id = self._get_id("order_item_status", "order_item_status_id", "code", "QUEUED")
            payment_method_id = self._get_id(
                "payment_method",
                "payment_method_id",
                "code",
                PAYMENT_TO_CODE.get(payment_method, "CASH"),
            )

            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO customer_order (
                            table_id,
                            order_status_id,
                            created_by_user_id,
                            payment_method_id
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (table_id, order_status_id, user_id, payment_method_id),
                    )
                    order_id = cursor.lastrowid
                    for item in draft_snapshot:
                        dish_id = self._get_dish_id(item["name"])
                        if dish_id is None:
                            continue
                        cursor.execute(
                            """
                            INSERT INTO order_item (
                                order_id,
                                dish_id,
                                order_item_status_id,
                                quantity,
                                unit_price
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (order_id, dish_id, item_status_id, item["qty"], item["price"]),
                        )
                connection.commit()
        except Error:
            pass

        return success, message

    def apply_inventory_operation(self, ingredient: str, operation_type: str, amount: float, note: str) -> str:
        message = super().apply_inventory_operation(ingredient, operation_type, amount, note)
        if not self.mysql_enabled:
            return message

        try:
            ingredient_id = self._get_id("ingredient", "ingredient_id", "name", ingredient)
            operation_type_id = self._get_id(
                "stock_operation_type",
                "stock_operation_type_id",
                "code",
                STOCK_OPERATION_TO_CODE.get(operation_type, "ADJUSTMENT_IN"),
            )
            quantity = abs(amount)
            user_id = self._current_mysql_user_id()
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO inventory_operation (
                            ingredient_id,
                            stock_operation_type_id,
                            quantity,
                            performed_by_user_id,
                            note
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (ingredient_id, operation_type_id, quantity, user_id, note or "Операция из интерфейса"),
                    )
                connection.commit()
        except Error:
            pass

        return message

    def _load_roles(self) -> None:
        rows = self._fetch_all("SELECT code FROM employee_role ORDER BY role_id")
        roles = [ROLE_CODE_TO_RU.get(row["code"], row["code"]) for row in rows]
        if roles:
            self.role_options = roles

    def _load_users(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                au.user_id,
                au.employee_id,
                au.login,
                au.password_hash,
                e.last_name,
                e.first_name,
                e.middle_name,
                er.code AS role_code
            FROM app_user au
            JOIN employee e ON e.employee_id = au.employee_id
            JOIN employee_role er ON er.role_id = e.role_id
            WHERE au.is_active = 1 AND e.is_active = 1
            ORDER BY au.user_id
            """
        )
        if rows:
            self.users = [
                {
                    "user_id": row["user_id"],
                    "employee_id": row["employee_id"],
                    "full_name": _join_full_name(row["last_name"], row["first_name"], row["middle_name"]),
                    "login": row["login"],
                    "password": row["password_hash"],
                    "role": ROLE_CODE_TO_RU.get(row["role_code"], row["role_code"]),
                }
                for row in rows
            ]

    def _load_employees(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                e.last_name,
                e.first_name,
                e.middle_name,
                er.code AS role_code,
                e.is_active
            FROM employee e
            JOIN employee_role er ON er.role_id = e.role_id
            ORDER BY e.last_name, e.first_name
            """
        )
        if rows:
            self.employees = [
                {
                    "name": _join_full_name(row["last_name"], row["first_name"], row["middle_name"]),
                    "role": ROLE_CODE_TO_RU.get(row["role_code"], row["role_code"]),
                    "skill": "Из базы данных",
                    "status": "Свободен" if row["is_active"] else "Неактивен",
                }
                for row in rows
            ]

    def _load_tables(self) -> None:
        rows = self._fetch_all(
            """
            SELECT code, seats_count, is_active
            FROM restaurant_table
            WHERE is_active = 1
            ORDER BY code
            """
        )
        if rows:
            self.tables = [
                {"code": row["code"], "seats": row["seats_count"], "occupied": False}
                for row in rows
            ]

    def _load_reservations(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                r.reservation_id,
                g.full_name AS guest,
                g.phone,
                rt.code AS table_code,
                r.reserved_from,
                r.guest_count,
                rs.code AS status_code
            FROM reservation r
            JOIN guest g ON g.guest_id = r.guest_id
            LEFT JOIN restaurant_table rt ON rt.table_id = r.table_id
            JOIN reservation_status rs ON rs.reservation_status_id = r.reservation_status_id
            ORDER BY r.reserved_from DESC
            LIMIT 50
            """
        )
        if rows:
            self.reservations = [
                {
                    "reservation_id": row["reservation_id"],
                    "guest": row["guest"],
                    "phone": row["phone"] or "",
                    "table": row["table_code"] or "-",
                    "time": row["reserved_from"].strftime("%d.%m %H:%M"),
                    "guests": row["guest_count"],
                    "status": _reservation_status_ru(row["status_code"]),
                }
                for row in rows
            ]

    def _load_menu(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                mc.name AS category,
                d.name,
                d.base_price,
                d.prep_time_minutes
            FROM dish d
            JOIN menu_category mc ON mc.category_id = d.category_id
            WHERE d.is_active = 1
            ORDER BY mc.sort_order, mc.name, d.name
            """
        )
        if rows:
            self.menu = [
                {
                    "category": row["category"],
                    "name": row["name"],
                    "price": int(row["base_price"]),
                    "ready": f"{row['prep_time_minutes'] or 10} мин",
                }
                for row in rows
            ]

    def _load_inventory(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                i.name AS ingredient,
                i.critical_level,
                mu.name AS unit_name,
                mu.code AS unit_code,
                COALESCE(stock.current_quantity, 0) AS stock
            FROM ingredient i
            JOIN measurement_unit mu ON mu.measurement_unit_id = i.measurement_unit_id
            LEFT JOIN v_ingredient_stock_balance stock ON stock.ingredient_id = i.ingredient_id
            WHERE i.is_active = 1
            ORDER BY i.name
            """
        )
        if rows:
            self.inventory = [
                {
                    "ingredient": row["ingredient"],
                    "stock": _to_float(row["stock"]),
                    "unit": _unit_ru(row["unit_code"], row["unit_name"]),
                    "threshold": _to_float(row["critical_level"]),
                }
                for row in rows
            ]

    def _load_kitchen_queue(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                co.order_id,
                rt.code AS table_code,
                os.code AS status_code,
                COALESCE(total.total_amount, 0) AS total_amount,
                GROUP_CONCAT(d.name ORDER BY d.name SEPARATOR ', ') AS items
            FROM customer_order co
            LEFT JOIN restaurant_table rt ON rt.table_id = co.table_id
            JOIN order_status os ON os.order_status_id = co.order_status_id
            LEFT JOIN order_item oi ON oi.order_id = co.order_id
            LEFT JOIN dish d ON d.dish_id = oi.dish_id
            LEFT JOIN v_order_total total ON total.order_id = co.order_id
            WHERE os.code <> 'CLOSED'
            GROUP BY co.order_id, rt.code, os.code, total.total_amount
            ORDER BY co.created_at DESC
            LIMIT 30
            """
        )
        if rows:
            self.kitchen_queue = [
                {
                    "order_no": f"GS-{row['order_id']}",
                    "table": row["table_code"] or "-",
                    "items": row["items"] or "Позиции не указаны",
                    "status": _order_status_ru(row["status_code"]),
                    "total": int(row["total_amount"] or 0),
                }
                for row in rows
            ]

    def _authenticate_mysql(self, login: str, password: str) -> dict | None:
        row = self._fetch_one(
            """
            SELECT
                au.user_id,
                au.employee_id,
                au.login,
                au.password_hash,
                e.last_name,
                e.first_name,
                e.middle_name,
                er.code AS role_code
            FROM app_user au
            JOIN employee e ON e.employee_id = au.employee_id
            JOIN employee_role er ON er.role_id = e.role_id
            WHERE au.login = %s
              AND au.is_active = 1
              AND e.is_active = 1
            LIMIT 1
            """,
            (login,),
        )
        if row is None:
            return None

        stored_hash = row["password_hash"]
        if stored_hash not in {password, _hash_password(password)}:
            return None

        return {
            "user_id": row["user_id"],
            "employee_id": row["employee_id"],
            "full_name": _join_full_name(row["last_name"], row["first_name"], row["middle_name"]),
            "login": row["login"],
            "password": stored_hash,
            "role": ROLE_CODE_TO_RU.get(row["role_code"], row["role_code"]),
        }

    def _login_exists_in_mysql(self, login: str) -> bool:
        row = self._fetch_one("SELECT user_id FROM app_user WHERE login = %s LIMIT 1", (login,))
        return row is not None

    def _current_mysql_user_id(self) -> int | None:
        if not self.current_user:
            return None
        user_id = self.current_user.get("user_id")
        return int(user_id) if user_id else None

    def _get_dish_id(self, dish_name: str) -> int | None:
        row = self._fetch_one("SELECT dish_id FROM dish WHERE name = %s LIMIT 1", (dish_name,))
        return int(row["dish_id"]) if row else None

    def _get_id(self, table: str, id_column: str, lookup_column: str, lookup_value: str) -> int:
        row = self._fetch_one(
            f"SELECT {id_column} FROM {table} WHERE {lookup_column} = %s LIMIT 1",
            (lookup_value,),
        )
        if row is None:
            raise Error(f"Не найдено значение {table}.{lookup_column} = {lookup_value}")
        return int(row[id_column])

    def _connect(self):
        if self.manager is None:
            raise RuntimeError("MySQL manager is not configured.")
        return self.manager.connect(include_database=True)

    def _fetch_all(self, query: str, params: tuple | None = None) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return list(cursor.fetchall())

    def _fetch_one(self, query: str, params: tuple | None = None) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _split_full_name(full_name: str) -> tuple[str, str, str | None]:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return "Пользователь", "Новый", None
    if len(parts) == 1:
        return parts[0], "Новый", None
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], parts[1], " ".join(parts[2:])


def _join_full_name(last_name: str, first_name: str, middle_name: str | None) -> str:
    return " ".join(part for part in [last_name, first_name, middle_name] if part)


def _reservation_status_ru(code: str) -> str:
    return {
        "ACTIVE": "Подтверждена",
        "COMPLETED": "Завершена",
        "CANCELLED": "Отменена",
        "NO_SHOW": "Не пришел",
    }.get(code, code)


def _order_status_ru(code: str) -> str:
    return {
        "NEW": "Принят",
        "ACCEPTED": "Принят",
        "PREPARING": "Готовится",
        "READY": "Готов",
        "SERVED": "Выдан",
        "CLOSED": "Закрыт",
        "CANCELLED": "Отменен",
    }.get(code, code)


def _unit_ru(code: str, name: str) -> str:
    return {
        "g": "г",
        "kg": "кг",
        "ml": "мл",
        "l": "л",
        "pcs": "шт",
    }.get(code, name)


def _to_float(value) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)
