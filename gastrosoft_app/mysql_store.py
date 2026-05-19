from __future__ import annotations

import hashlib
from datetime import datetime, time, timedelta
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

SHIFT_TO_CODE = {
    "Утро 08:00-14:00": "MORNING",
    "День 12:00-18:00": "DAY",
    "Вечер 17:00-23:00": "EVENING",
}

SHIFT_STATUS_TO_RU = {
    "PLANNED": "План",
    "IN_PROGRESS": "Подтверждена",
    "COMPLETED": "Закрыта",
    "CANCELLED": "Отменена",
}

ORDER_STATUS_SEQUENCE = ["ACCEPTED", "PREPARING", "READY", "SERVED"]


class MySQLBackedStore(DemoStore):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root
        self.mysql_enabled = False
        self.mysql_status = "MySQL: демо-режим, файл mysql_config.json не найден."
        self.last_error = ""
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
        self._load_operations()
        self._load_kitchen_queue()
        self._load_assignments()
        self._load_dashboard_data()
        self.recalculate_tables()

    def authenticate(self, login: str, password: str) -> dict | None:
        if not self.mysql_enabled:
            self.last_error = "MySQL не подключен. Вход по тестовым данным отключен."
            return None

        user = self._authenticate_mysql(login, password)
        if user is not None:
            self.current_user = user
            return user
        return None

    def refresh_dashboard(self) -> None:
        if self.mysql_enabled:
            self.reload_from_mysql()

    def metrics(self) -> dict:
        if not self.mysql_enabled:
            return super().metrics()

        row = self._fetch_one(
            """
            SELECT
                COALESCE(SUM(CASE WHEN os.code IN ('SERVED', 'CLOSED') THEN total.total_amount ELSE 0 END), 0) AS revenue,
                COUNT(co.order_id) AS orders_count
            FROM customer_order co
            JOIN order_status os ON os.order_status_id = co.order_status_id
            LEFT JOIN v_order_total total ON total.order_id = co.order_id
            WHERE DATE(co.created_at) = CURRENT_DATE()
            """
        )
        active_reservations = [item for item in self.reservations if item["status"] != "Отменена"]
        draft_total = self.get_draft_total()
        return {
            "revenue": f"{int(row['revenue'] or 0):,} ₽".replace(",", " "),
            "orders": str(int(row["orders_count"] or 0)),
            "reservations": str(len(active_reservations)),
            "low_stock": str(len(self.low_stock_items())),
            "draft_total": f"{draft_total:,} ₽".replace(",", " "),
        }

    def register_user(self, full_name: str, login: str, password: str, role: str) -> tuple[bool, str, dict | None]:
        if not self.mysql_enabled:
            return False, "MySQL не подключен. Пользователь не сохранен.", None

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

    def add_assignment(self, employee_name: str, shift: str, date_text: str) -> dict | None:
        if not self.mysql_enabled:
            self.last_error = "MySQL не подключен. Смена не сохранена."
            return None

        try:
            user_id = self._current_mysql_user_id()
            if user_id is None:
                self.last_error = "Нужно войти пользователем из MySQL, чтобы назначить смену."
                return None

            employee = self._get_employee_by_full_name(employee_name)
            if employee is None:
                self.last_error = f"Сотрудник не найден в MySQL: {employee_name}"
                return None

            shift_code = SHIFT_TO_CODE.get(shift, "DAY")
            shift_type = self._fetch_one(
                """
                SELECT shift_type_id, default_start_time, default_end_time
                FROM shift_type
                WHERE code = %s
                LIMIT 1
                """,
                (shift_code,),
            )
            if shift_type is None:
                self.last_error = f"Тип смены не найден в MySQL: {shift}"
                return None

            shift_date = datetime.strptime(date_text, "%d.%m.%Y").date()
            start_time = _as_time(shift_type["default_start_time"])
            end_time = _as_time(shift_type["default_end_time"])
            planned_start = datetime.combine(shift_date, start_time)
            planned_end = datetime.combine(shift_date, end_time)
            if planned_end <= planned_start:
                planned_end += timedelta(days=1)

            planned_status_id = self._get_id("shift_status", "shift_status_id", "code", "PLANNED")

            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO work_shift (
                            shift_type_id,
                            shift_status_id,
                            planned_start,
                            planned_end,
                            created_by_user_id
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (shift_type["shift_type_id"], planned_status_id, planned_start, planned_end, user_id),
                    )
                    shift_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO shift_assignment (shift_id, employee_id, assignment_role_id)
                        VALUES (%s, %s, %s)
                        """,
                        (shift_id, employee["employee_id"], employee["role_id"]),
                    )
                    assignment_id = cursor.lastrowid
                connection.commit()

            self.reload_from_mysql()
            return next((item for item in self.assignments if item.get("assignment_id") == assignment_id), None)
        except (Error, ValueError) as exc:
            self.last_error = f"Ошибка записи смены в MySQL: {exc}"
            return None

    def swap_assignment(self, assignment_index: int) -> str:
        if not self.mysql_enabled or assignment_index < 0 or assignment_index >= len(self.assignments):
            return "MySQL не подключен или назначение не выбрано."

        assignment = self.assignments[assignment_index]
        try:
            replacement = self._fetch_one(
                """
                SELECT e.employee_id
                FROM employee e
                JOIN employee_role er ON er.role_id = e.role_id
                WHERE er.code = %s
                  AND e.employee_id <> %s
                  AND e.is_active = 1
                ORDER BY e.employee_id
                LIMIT 1
                """,
                (RU_ROLE_TO_CODE.get(assignment["role"], assignment["role"]), assignment["employee_id"]),
            )
            if replacement is None:
                return "Подходящей замены для выбранной роли не найдено."

            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE shift_assignment SET employee_id = %s WHERE assignment_id = %s",
                        (replacement["employee_id"], assignment["assignment_id"]),
                    )
                connection.commit()
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка подбора замены в MySQL: {exc}"

        updated = next(
            (item for item in self.assignments if item.get("assignment_id") == assignment["assignment_id"]),
            None,
        )
        if updated is None:
            return "Замена сохранена в MySQL."
        return f"Назначена замена: {updated['employee']}."

    def close_assignment(self, assignment_index: int) -> str:
        if not self.mysql_enabled or assignment_index < 0 or assignment_index >= len(self.assignments):
            return "MySQL не подключен или смена не выбрана."

        assignment = self.assignments[assignment_index]
        try:
            completed_status_id = self._get_id("shift_status", "shift_status_id", "code", "COMPLETED")
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE work_shift SET shift_status_id = %s WHERE shift_id = %s",
                        (completed_status_id, assignment["shift_id"]),
                    )
                    cursor.execute(
                        """
                        UPDATE shift_assignment
                        SET check_out_time = COALESCE(check_out_time, NOW())
                        WHERE assignment_id = %s
                        """,
                        (assignment["assignment_id"],),
                    )
                connection.commit()
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка закрытия смены в MySQL: {exc}"
        return "Смена помечена как закрытая в MySQL."

    def add_reservation(
        self, guest: str, phone: str, table: str, date_time: datetime, guests: int, status: str
    ) -> dict:
        if not self.mysql_enabled:
            self.last_error = "MySQL не подключен. Бронь не сохранена."
            return {}

        try:
            user_id = self._current_mysql_user_id()
            if user_id is None:
                self.last_error = "Нужно войти пользователем из MySQL, чтобы создать бронь."
                return {}

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
                    reservation_id = cursor.lastrowid
                connection.commit()
            self.reload_from_mysql()
            return next(
                (item for item in self.reservations if item.get("reservation_id") == reservation_id),
                {},
            )
        except Error as exc:
            self.last_error = f"Ошибка записи брони в MySQL: {exc}"
            return {}

        return {}

    def set_reservation_status(self, index: int, status: str) -> str:
        if not self.mysql_enabled or index < 0 or index >= len(self.reservations):
            return "MySQL не подключен или бронь не выбрана."

        reservation_id = self.reservations[index].get("reservation_id")
        if reservation_id is None:
            return "Эта бронь не связана с записью в MySQL."

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
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка изменения статуса брони в MySQL: {exc}"
        return f"Статус брони изменён: {status}."

    def send_draft_to_kitchen(self, table_code: str, payment_method: str) -> tuple[bool, str]:
        draft_snapshot = [item.copy() for item in self.order_draft]
        if not draft_snapshot:
            return False, "Сначала добавь блюда в заказ."
        if not self.mysql_enabled:
            return False, "MySQL не подключен. Заказ не сохранен."

        try:
            user_id = self._current_mysql_user_id()
            if user_id is None:
                return False, "Нужно войти пользователем из MySQL, чтобы создать заказ."

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
            self.clear_draft()
            self.reload_from_mysql()
            return True, f"Заказ GS-{order_id} сохранен в MySQL и отправлен на кухню."
        except Error as exc:
            return False, f"Ошибка записи заказа в MySQL: {exc}"

        return False, "Заказ не сохранен."

    def advance_order_status(self, index: int) -> str:
        if not self.mysql_enabled or index < 0 or index >= len(self.kitchen_queue):
            return "MySQL не подключен или заказ не выбран."

        order = self.kitchen_queue[index]
        current_code = ORDER_STATUS_TO_CODE.get(order["status"], "ACCEPTED")
        try:
            current_pos = ORDER_STATUS_SEQUENCE.index(current_code)
        except ValueError:
            current_pos = 0
        next_code = ORDER_STATUS_SEQUENCE[min(current_pos + 1, len(ORDER_STATUS_SEQUENCE) - 1)]

        return self._set_order_status(order, next_code)

    def advance_kitchen_order(self, index: int) -> str:
        if not self.mysql_enabled or index < 0 or index >= len(self.kitchen_queue):
            return "MySQL не подключен или заказ не выбран."

        order = self.kitchen_queue[index]
        current_code = ORDER_STATUS_TO_CODE.get(order["status"], "ACCEPTED")
        if current_code == "READY":
            return "Заказ уже отмечен как готовый."
        if current_code in {"SERVED", "CLOSED"}:
            return "Заказ уже выдан или закрыт."

        next_code = "READY" if current_code == "PREPARING" else "PREPARING"
        return self._set_order_status(order, next_code)

    def _set_order_status(self, order: dict, next_code: str) -> str:
        try:
            status_id = self._get_id("order_status", "order_status_id", "code", next_code)
            item_status_code = {
                "ACCEPTED": "QUEUED",
                "PREPARING": "COOKING",
                "READY": "READY",
                "SERVED": "SERVED",
            }[next_code]
            item_status_id = self._get_id("order_item_status", "order_item_status_id", "code", item_status_code)
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE customer_order SET order_status_id = %s WHERE order_id = %s",
                        (status_id, order["order_id"]),
                    )
                    cursor.execute(
                        "UPDATE order_item SET order_item_status_id = %s WHERE order_id = %s",
                        (item_status_id, order["order_id"]),
                    )
                connection.commit()
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка изменения статуса заказа в MySQL: {exc}"
        return f"Статус заказа изменён: {_order_status_ru(next_code)}."

    def complete_order(self, index: int) -> str:
        if not self.mysql_enabled or index < 0 or index >= len(self.kitchen_queue):
            return "MySQL не подключен или заказ не выбран."

        order = self.kitchen_queue[index]
        try:
            closed_status_id = self._get_id("order_status", "order_status_id", "code", "CLOSED")
            served_item_status_id = self._get_id("order_item_status", "order_item_status_id", "code", "SERVED")
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE customer_order
                        SET order_status_id = %s, closed_at = COALESCE(closed_at, NOW())
                        WHERE order_id = %s
                        """,
                        (closed_status_id, order["order_id"]),
                    )
                    cursor.execute(
                        "UPDATE order_item SET order_item_status_id = %s WHERE order_id = %s",
                        (served_item_status_id, order["order_id"]),
                    )
                connection.commit()
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка закрытия заказа в MySQL: {exc}"
        return f"Заказ GS-{order['order_id']} закрыт в MySQL."

    def apply_inventory_operation(self, ingredient: str, operation_type: str, amount: float, note: str) -> str:
        if not self.mysql_enabled:
            return "MySQL не подключен. Операция не сохранена."

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
            self.reload_from_mysql()
        except Error as exc:
            return f"Ошибка записи складской операции в MySQL: {exc}"

        return "Операция по складу сохранена в MySQL."

    def _load_roles(self) -> None:
        rows = self._fetch_all("SELECT code FROM employee_role ORDER BY role_id")
        self.role_options = [ROLE_CODE_TO_RU.get(row["code"], row["code"]) for row in rows]

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
                e.employee_id,
                e.is_active,
                GROUP_CONCAT(s.name ORDER BY es.skill_level DESC, s.name SEPARATOR ', ') AS skills,
                MAX(CASE
                    WHEN ss.code IN ('PLANNED', 'IN_PROGRESS')
                     AND ws.planned_end >= NOW()
                    THEN 1 ELSE 0
                END) AS has_active_shift
            FROM employee e
            JOIN employee_role er ON er.role_id = e.role_id
            LEFT JOIN employee_skill es ON es.employee_id = e.employee_id
            LEFT JOIN skill s ON s.skill_id = es.skill_id
            LEFT JOIN shift_assignment sa ON sa.employee_id = e.employee_id
            LEFT JOIN work_shift ws ON ws.shift_id = sa.shift_id
            LEFT JOIN shift_status ss ON ss.shift_status_id = ws.shift_status_id
            GROUP BY e.employee_id, e.last_name, e.first_name, e.middle_name, er.code, e.is_active
            ORDER BY e.last_name, e.first_name
            """
        )
        self.employees = [
            {
                "employee_id": row["employee_id"],
                "name": _join_full_name(row["last_name"], row["first_name"], row["middle_name"]),
                "role": ROLE_CODE_TO_RU.get(row["role_code"], row["role_code"]),
                "skill": row["skills"] or "Из базы данных",
                "status": _employee_status(row["is_active"], row["has_active_shift"]),
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
        self.inventory = [
            {
                "ingredient": row["ingredient"],
                "stock": _to_float(row["stock"]),
                "unit": _unit_ru(row["unit_code"], row["unit_name"]),
                "threshold": _to_float(row["critical_level"]),
            }
            for row in rows
        ]

    def _load_operations(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                io.operation_datetime,
                i.name AS ingredient,
                sot.code AS operation_code,
                io.quantity,
                io.note
            FROM inventory_operation io
            JOIN ingredient i ON i.ingredient_id = io.ingredient_id
            JOIN stock_operation_type sot ON sot.stock_operation_type_id = io.stock_operation_type_id
            ORDER BY io.operation_datetime DESC, io.operation_id DESC
            LIMIT 50
            """
        )
        self.operations = [
            {
                "time": row["operation_datetime"].strftime("%d.%m %H:%M"),
                "ingredient": row["ingredient"],
                "type": _stock_operation_ru(row["operation_code"]),
                "amount": _to_float(row["quantity"]),
                "note": row["note"] or "",
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
                co.created_at,
                COALESCE(total.total_amount, 0) AS total_amount,
                GROUP_CONCAT(d.name ORDER BY d.name SEPARATOR ', ') AS items
            FROM customer_order co
            LEFT JOIN restaurant_table rt ON rt.table_id = co.table_id
            JOIN order_status os ON os.order_status_id = co.order_status_id
            LEFT JOIN order_item oi ON oi.order_id = co.order_id
            LEFT JOIN dish d ON d.dish_id = oi.dish_id
            LEFT JOIN v_order_total total ON total.order_id = co.order_id
            WHERE os.code <> 'CLOSED'
            GROUP BY co.order_id, rt.code, os.code, co.created_at, total.total_amount
            ORDER BY FIELD(os.code, 'ACCEPTED', 'PREPARING', 'READY', 'SERVED'), co.created_at ASC
            LIMIT 30
            """
        )
        self.kitchen_queue = [
            {
                "order_id": row["order_id"],
                "order_no": f"GS-{row['order_id']}",
                "table": row["table_code"] or "-",
                "created": row["created_at"].strftime("%H:%M") if row["created_at"] else "-",
                "items": row["items"] or "Позиции не указаны",
                "status": _order_status_ru(row["status_code"]),
                "total": int(row["total_amount"] or 0),
            }
            for row in rows
        ]

    def _load_assignments(self) -> None:
        rows = self._fetch_all(
            """
            SELECT
                sa.assignment_id,
                sa.shift_id,
                sa.employee_id,
                ws.planned_start,
                ws.planned_end,
                st.code AS shift_type_code,
                ss.code AS shift_status_code,
                e.last_name,
                e.first_name,
                e.middle_name,
                er.code AS role_code
            FROM shift_assignment sa
            JOIN work_shift ws ON ws.shift_id = sa.shift_id
            JOIN shift_type st ON st.shift_type_id = ws.shift_type_id
            JOIN shift_status ss ON ss.shift_status_id = ws.shift_status_id
            JOIN employee e ON e.employee_id = sa.employee_id
            JOIN employee_role er ON er.role_id = sa.assignment_role_id
            ORDER BY ws.planned_start DESC, sa.assignment_id DESC
            LIMIT 50
            """
        )
        self.assignments = [
            {
                "assignment_id": row["assignment_id"],
                "shift_id": row["shift_id"],
                "employee_id": row["employee_id"],
                "date": row["planned_start"].strftime("%d.%m.%Y"),
                "shift": _shift_label(row["shift_type_code"], row["planned_start"], row["planned_end"]),
                "employee": _join_full_name(row["last_name"], row["first_name"], row["middle_name"]),
                "role": ROLE_CODE_TO_RU.get(row["role_code"], row["role_code"]),
                "status": SHIFT_STATUS_TO_RU.get(row["shift_status_code"], row["shift_status_code"]),
            }
            for row in rows
        ]

    def _load_dashboard_data(self) -> None:
        hourly_rows = self._fetch_all(
            """
            SELECT HOUR(co.created_at) AS order_hour, COUNT(*) AS order_count
            FROM customer_order co
            WHERE DATE(co.created_at) = CURRENT_DATE()
            GROUP BY HOUR(co.created_at)
            ORDER BY order_hour
            """
        )
        hour_counts = {int(row["order_hour"]): int(row["order_count"]) for row in hourly_rows}
        self.sales_by_hour = [hour_counts.get(hour, 0) for hour in range(8, 24, 2)]

        top_rows = self._fetch_all(
            """
            SELECT d.name, SUM(oi.quantity) AS dish_count
            FROM order_item oi
            JOIN dish d ON d.dish_id = oi.dish_id
            JOIN customer_order co ON co.order_id = oi.order_id
            WHERE DATE(co.created_at) = CURRENT_DATE()
            GROUP BY d.dish_id, d.name
            ORDER BY dish_count DESC, d.name
            LIMIT 5
            """
        )
        if top_rows:
            self.top_dishes = {row["name"]: int(row["dish_count"]) for row in top_rows}
        else:
            self.top_dishes = {item["name"]: 0 for item in self.menu[:5]} or {"Нет данных": 0}

        self.alerts = []
        for item in self.low_stock_items()[:4]:
            self.alerts.append(
                f"Низкий остаток: {item['ingredient']} ({item['stock']} {item['unit']}, минимум {item['threshold']})."
            )
        if not self.alerts:
            self.alerts.append("Критичных складских остатков нет.")

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

    def _get_employee_by_full_name(self, full_name: str) -> dict | None:
        for employee in self.employees:
            if employee["name"] == full_name:
                return self._fetch_one(
                    """
                    SELECT e.employee_id, e.role_id
                    FROM employee e
                    WHERE e.employee_id = %s
                    LIMIT 1
                    """,
                    (employee["employee_id"],),
                )

        last_name, first_name, middle_name = _split_full_name(full_name)
        return self._fetch_one(
            """
            SELECT employee_id, role_id
            FROM employee
            WHERE last_name = %s
              AND first_name = %s
              AND (middle_name <=> %s)
            LIMIT 1
            """,
            (last_name, first_name, middle_name),
        )

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


def _stock_operation_ru(code: str) -> str:
    return {
        "RECEIPT": "Поступление",
        "WRITE_OFF": "Списание",
        "ADJUSTMENT_IN": "Корректировка",
        "ADJUSTMENT_OUT": "Корректировка",
    }.get(code, code)


def _employee_status(is_active: int, has_active_shift: int | None) -> str:
    if not is_active:
        return "Неактивен"
    if has_active_shift:
        return "На смене"
    return "Свободен"


def _shift_label(code: str, planned_start: datetime, planned_end: datetime) -> str:
    name = {
        "MORNING": "Утро",
        "DAY": "День",
        "EVENING": "Вечер",
        "NIGHT": "Ночь",
    }.get(code, "Смена")
    return f"{name} {planned_start:%H:%M}-{planned_end:%H:%M}"


def _as_time(value) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return time(hour=hours % 24, minute=minutes, second=seconds)
    return value


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
