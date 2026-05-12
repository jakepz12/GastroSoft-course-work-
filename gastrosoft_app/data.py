from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


class DemoStore:
    def __init__(self) -> None:
        self.role_options = [
            "Администратор системы",
            "Директор",
            "Шеф-повар",
            "Менеджер зала",
            "Бухгалтер",
            "Официант",
            "Повар",
            "Кассир",
        ]

        self.users = [
            {
                "full_name": "Анна Смирнова",
                "login": "director",
                "password": "1234",
                "role": "Директор",
            },
            {
                "full_name": "Илья Волков",
                "login": "chef",
                "password": "1234",
                "role": "Шеф-повар",
            },
            {
                "full_name": "Мария Белова",
                "login": "waiter",
                "password": "1234",
                "role": "Официант",
            },
            {
                "full_name": "Олег Корнеев",
                "login": "cashier",
                "password": "1234",
                "role": "Кассир",
            },
        ]

        self.current_user: dict | None = None
        self.refresh_seed = 0
        self.order_sequence = 118

        self.sales_by_hour = [9, 12, 15, 19, 25, 31, 28, 35]
        self.top_dishes = {
            "Паста": 32,
            "Том Ям": 26,
            "Бургер": 21,
            "Лимонад": 18,
        }
        self.alerts = [
            "Низкий остаток томатов на складе.",
            "На вечернюю смену не хватает 1 официанта.",
            "Бронь на стол T-06 требует подтверждения.",
        ]

        self.employees = [
            {"name": "Анна Смирнова", "role": "Директор", "skill": "Аналитика", "status": "На смене"},
            {"name": "Илья Волков", "role": "Шеф-повар", "skill": "Горячий цех", "status": "На смене"},
            {"name": "Мария Белова", "role": "Официант", "skill": "Гости VIP", "status": "Свободен"},
            {"name": "Олег Корнеев", "role": "Кассир", "skill": "Закрытие смены", "status": "Свободен"},
            {"name": "Ксения Орлова", "role": "Менеджер зала", "skill": "Бронирования", "status": "На смене"},
            {"name": "Павел Громов", "role": "Повар", "skill": "Холодный цех", "status": "Свободен"},
            {"name": "Даниил Котов", "role": "Повар", "skill": "Гриль", "status": "На смене"},
            {"name": "Светлана Руднева", "role": "Бухгалтер", "skill": "Отчеты", "status": "В офисе"},
        ]

        today = datetime.now().date()
        self.assignments = [
            {
                "date": today.strftime("%d.%m.%Y"),
                "shift": "Утро 08:00-14:00",
                "employee": "Илья Волков",
                "role": "Шеф-повар",
                "status": "Подтверждена",
            },
            {
                "date": today.strftime("%d.%m.%Y"),
                "shift": "День 12:00-18:00",
                "employee": "Мария Белова",
                "role": "Официант",
                "status": "План",
            },
        ]

        self.tables = [
            {"code": "T-01", "seats": 2, "occupied": False},
            {"code": "T-02", "seats": 2, "occupied": True},
            {"code": "T-03", "seats": 4, "occupied": True},
            {"code": "T-04", "seats": 4, "occupied": False},
            {"code": "T-05", "seats": 6, "occupied": False},
            {"code": "T-06", "seats": 6, "occupied": True},
        ]

        now = datetime.now()
        self.reservations = [
            {
                "guest": "Екатерина Миронова",
                "phone": "+7 912 555-11-22",
                "table": "T-06",
                "time": (now + timedelta(hours=1)).strftime("%d.%m %H:%M"),
                "guests": 5,
                "status": "Ожидается",
            },
            {
                "guest": "Денис Петров",
                "phone": "+7 922 100-50-40",
                "table": "T-02",
                "time": (now + timedelta(hours=2)).strftime("%d.%m %H:%M"),
                "guests": 2,
                "status": "Подтверждена",
            },
        ]

        self.menu = [
            {"category": "Закуски", "name": "Брускетта с томатами", "price": 390, "ready": "7 мин"},
            {"category": "Закуски", "name": "Тар-тар из лосося", "price": 540, "ready": "10 мин"},
            {"category": "Супы", "name": "Том Ям", "price": 620, "ready": "12 мин"},
            {"category": "Супы", "name": "Крем-суп из грибов", "price": 430, "ready": "9 мин"},
            {"category": "Горячее", "name": "Паста Альфредо", "price": 590, "ready": "15 мин"},
            {"category": "Горячее", "name": "Бургер GastroSoft", "price": 670, "ready": "14 мин"},
            {"category": "Напитки", "name": "Лимонад базилик-лайм", "price": 260, "ready": "3 мин"},
            {"category": "Напитки", "name": "Эспрессо", "price": 170, "ready": "2 мин"},
        ]

        self.order_draft: list[dict] = []
        self.kitchen_queue = [
            {
                "order_no": "GS-117",
                "table": "T-03",
                "items": "Том Ям, Лимонад",
                "status": "Готовится",
                "total": 880,
            }
        ]

        self.inventory = [
            {"ingredient": "Томаты", "stock": 4.6, "unit": "кг", "threshold": 5.0},
            {"ingredient": "Сливки", "stock": 7.5, "unit": "л", "threshold": 3.0},
            {"ingredient": "Лосось", "stock": 3.1, "unit": "кг", "threshold": 2.5},
            {"ingredient": "Булочки бриошь", "stock": 14, "unit": "шт", "threshold": 10},
            {"ingredient": "Кофе зерно", "stock": 2.2, "unit": "кг", "threshold": 1.5},
        ]

        self.operations = [
            {
                "time": now.strftime("%d.%m %H:%M"),
                "ingredient": "Томаты",
                "type": "Списание",
                "amount": 1.2,
                "note": "Расход по заказам",
            },
            {
                "time": now.strftime("%d.%m %H:%M"),
                "ingredient": "Сливки",
                "type": "Поступление",
                "amount": 4.0,
                "note": "Утренний приход",
            },
        ]

    def authenticate(self, login: str, password: str) -> dict | None:
        for user in self.users:
            if user["login"] == login and user["password"] == password:
                self.current_user = user
                return user
        return None

    def register_user(self, full_name: str, login: str, password: str, role: str) -> tuple[bool, str, dict | None]:
        if any(user["login"] == login for user in self.users):
            return False, "Логин уже занят. Выбери другой.", None

        user = {"full_name": full_name, "login": login, "password": password, "role": role}
        self.users.append(user)

        employee_roles = {"Администратор системы", "Директор", "Шеф-повар", "Менеджер зала", "Бухгалтер", "Официант", "Повар", "Кассир"}
        if role in employee_roles:
            self.employees.append(
                {"name": full_name, "role": role, "skill": "Новый сотрудник", "status": "Свободен"}
            )

        self.current_user = user
        return True, "Пользователь зарегистрирован и вошел в систему.", user

    def refresh_dashboard(self) -> None:
        self.refresh_seed += 1
        self.sales_by_hour = [value + (self.refresh_seed % 3) for value in self.sales_by_hour]
        self.top_dishes["Паста"] += 1
        if self.refresh_seed % 2 == 0:
            self.alerts[0] = "Низкий остаток томатов и сливок. Нужна корректировка заказа поставщику."

    def metrics(self) -> dict:
        draft_total = self.get_draft_total()
        return {
            "revenue": f"{124_800 + self.refresh_seed * 2_500:,} ₽".replace(",", " "),
            "orders": str(46 + self.refresh_seed),
            "reservations": str(len([item for item in self.reservations if item['status'] != 'Отменена'])),
            "low_stock": str(len(self.low_stock_items())),
            "draft_total": f"{draft_total:,} ₽".replace(",", " "),
        }

    def add_assignment(self, employee_name: str, shift: str, date_text: str) -> dict | None:
        employee = next((item for item in self.employees if item["name"] == employee_name), None)
        if employee is None:
            return None

        assignment = {
            "date": date_text,
            "shift": shift,
            "employee": employee_name,
            "role": employee["role"],
            "status": "План",
        }
        self.assignments.append(assignment)
        employee["status"] = "Назначен"
        return assignment

    def swap_assignment(self, assignment_index: int) -> str:
        if assignment_index < 0 or assignment_index >= len(self.assignments):
            return "Сначала выбери назначение, для которого нужна замена."

        assignment = self.assignments[assignment_index]
        replacement = next(
            (
                employee
                for employee in self.employees
                if employee["role"] == assignment["role"] and employee["name"] != assignment["employee"]
            ),
            None,
        )

        if replacement is None:
            return "Подходящей замены для выбранной роли не найдено."

        assignment["employee"] = replacement["name"]
        assignment["status"] = "Замена согласована"
        replacement["status"] = "Назначен"
        return f"Назначена замена: {replacement['name']}."

    def close_assignment(self, assignment_index: int) -> str:
        if assignment_index < 0 or assignment_index >= len(self.assignments):
            return "Выбери смену, которую нужно закрыть."

        self.assignments[assignment_index]["status"] = "Закрыта"
        return "Смена помечена как закрытая."

    def add_reservation(
        self, guest: str, phone: str, table: str, date_time: datetime, guests: int, status: str
    ) -> dict:
        reservation = {
            "guest": guest,
            "phone": phone,
            "table": table,
            "time": date_time.strftime("%d.%m %H:%M"),
            "guests": guests,
            "status": status,
        }
        self.reservations.append(reservation)
        self.recalculate_tables()
        return reservation

    def set_reservation_status(self, index: int, status: str) -> str:
        if index < 0 or index >= len(self.reservations):
            return "Выбери бронь в таблице."
        self.reservations[index]["status"] = status
        self.recalculate_tables()
        return f"Статус брони изменён: {status}."

    def recalculate_tables(self) -> None:
        occupied_tables = {
            reservation["table"]
            for reservation in self.reservations
            if reservation["status"] in {"Ожидается", "Подтверждена", "Гость в зале"}
        }
        for table in self.tables:
            table["occupied"] = table["code"] in occupied_tables

    def categories(self) -> list[str]:
        return sorted({dish["category"] for dish in self.menu})

    def dishes_by_category(self, category: str) -> list[dict]:
        return [dish for dish in self.menu if dish["category"] == category]

    def add_dish_to_draft(self, dish_name: str) -> str:
        dish = next((item for item in self.menu if item["name"] == dish_name), None)
        if dish is None:
            return "Блюдо не найдено."

        existing = next((item for item in self.order_draft if item["name"] == dish_name), None)
        if existing:
            existing["qty"] += 1
            existing["sum"] = existing["qty"] * existing["price"]
        else:
            self.order_draft.append({"name": dish_name, "qty": 1, "price": dish["price"], "sum": dish["price"]})
        return f"В заказ добавлено: {dish_name}."

    def clear_draft(self) -> None:
        self.order_draft.clear()

    def get_draft_total(self) -> int:
        return sum(item["sum"] for item in self.order_draft)

    def send_draft_to_kitchen(self, table_code: str, payment_method: str) -> tuple[bool, str]:
        if not self.order_draft:
            return False, "Сначала добавь блюда в заказ."

        self.order_sequence += 1
        order_no = f"GS-{self.order_sequence}"
        items = ", ".join(item["name"] for item in self.order_draft)
        self.kitchen_queue.append(
            {
                "order_no": order_no,
                "table": table_code,
                "items": items,
                "status": "Принят",
                "total": self.get_draft_total(),
                "payment": payment_method,
            }
        )
        self.clear_draft()
        return True, f"Заказ {order_no} отправлен на кухню."

    def advance_order_status(self, index: int) -> str:
        if index < 0 or index >= len(self.kitchen_queue):
            return "Выбери заказ в очереди кухни."

        sequence = ["Принят", "Готовится", "Готов", "Выдан"]
        current = self.kitchen_queue[index]["status"]
        try:
            current_pos = sequence.index(current)
        except ValueError:
            current_pos = 0

        next_pos = min(current_pos + 1, len(sequence) - 1)
        self.kitchen_queue[index]["status"] = sequence[next_pos]
        return f"Статус заказа изменён: {sequence[next_pos]}."

    def complete_order(self, index: int) -> str:
        if index < 0 or index >= len(self.kitchen_queue):
            return "Выбери заказ для закрытия."

        self.kitchen_queue[index]["status"] = "Выдан"
        return f"Заказ {self.kitchen_queue[index]['order_no']} закрыт."

    def apply_inventory_operation(self, ingredient: str, operation_type: str, amount: float, note: str) -> str:
        row = next((item for item in self.inventory if item["ingredient"] == ingredient), None)
        if row is None:
            return "Ингредиент не найден."

        if operation_type == "Поступление":
            row["stock"] += amount
        elif operation_type == "Списание":
            row["stock"] = max(0.0, row["stock"] - amount)
        else:
            row["stock"] = amount

        self.operations.insert(
            0,
            {
                "time": datetime.now().strftime("%d.%m %H:%M"),
                "ingredient": ingredient,
                "type": operation_type,
                "amount": amount,
                "note": note or "Ручная операция",
            },
        )
        return "Операция по складу проведена."

    def low_stock_items(self) -> list[dict]:
        return [item for item in self.inventory if item["stock"] <= item["threshold"]]

    def build_report(self) -> str:
        low_stock = self.low_stock_items()
        report_lines = [
            "Оперативный отчет GastroSoft",
            f"Сформирован: {datetime.now():%d.%m.%Y %H:%M}",
            "",
            f"Всего позиций на складе: {len(self.inventory)}",
            f"Проблемных остатков: {len(low_stock)}",
            f"Броней в работе: {len([item for item in self.reservations if item['status'] != 'Отменена'])}",
            f"Заказов на кухне: {len(self.kitchen_queue)}",
            "",
            "Критичные остатки:",
        ]

        if not low_stock:
            report_lines.append("- Критичных остатков нет.")
        else:
            for item in low_stock:
                report_lines.append(
                    f"- {item['ingredient']}: {item['stock']} {item['unit']} (минимум {item['threshold']})"
                )

        report_lines.extend(["", "Последние операции:"])
        for operation in self.operations[:5]:
            report_lines.append(
                f"- {operation['time']} | {operation['ingredient']} | {operation['type']} | {operation['amount']}"
            )
        return "\n".join(report_lines)

    def export_report(self, project_root: Path) -> Path:
        export_dir = project_root / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "inventory_report.txt"
        export_path.write_text(self.build_report(), encoding="utf-8")
        return export_path

