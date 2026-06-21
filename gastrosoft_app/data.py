from __future__ import annotations

from datetime import datetime
from pathlib import Path


class DemoStore:
    """Base application state.

    The real data source is MySQLBackedStore. This class intentionally keeps
    empty collections so the UI cannot silently work with hardcoded seed data.
    """

    def __init__(self) -> None:
        self.role_options: list[str] = []
        self.users: list[dict] = []
        self.current_user: dict | None = None

        self.sales_by_hour: list[int] = [0] * 8
        self.top_dishes: dict[str, int] = {"Нет данных": 0}
        self.alerts: list[str] = ["MySQL не подключен: данные не загружены."]

        self.employees: list[dict] = []
        self.assignments: list[dict] = []
        self.tables: list[dict] = []
        self.reservations: list[dict] = []
        self.menu: list[dict] = []
        self.order_draft: list[dict] = []
        self.kitchen_queue: list[dict] = []
        self.inventory: list[dict] = []
        self.operations: list[dict] = []

    def authenticate(self, login: str, password: str) -> dict | None:
        for user in self.users:
            if user["login"] == login and user["password"] == password:
                self.current_user = user
                return user
        return None

    def register_user(self, full_name: str, login: str, password: str, role: str) -> tuple[bool, str, dict | None]:
        return False, "База данных не подключена. Регистрация доступна после настройки MySQL.", None

    def refresh_dashboard(self) -> None:
        return

    def metrics(self) -> dict:
        draft_total = self.get_draft_total()
        active_reservations = [item for item in self.reservations if item["status"] != "Отменена"]
        closed_orders_total = sum(item.get("total", 0) for item in self.kitchen_queue if item["status"] in {"Выдан", "Закрыт"})
        return {
            "revenue": f"{closed_orders_total:,} ₽".replace(",", " "),
            "orders": str(len(self.kitchen_queue)),
            "reservations": str(len(active_reservations)),
            "low_stock": str(len(self.low_stock_items())),
            "draft_total": f"{draft_total:,} ₽".replace(",", " "),
        }

    def add_assignment(self, employee_name: str, shift: str, date_text: str) -> dict | None:
        return None

    def swap_assignment(self, assignment_index: int) -> str:
        return "База данных не подключена или назначение не выбрано."

    def close_assignment(self, assignment_index: int) -> str:
        return "База данных не подключена или смена не выбрана."

    def add_reservation(self, guest: str, phone: str, table: str, date_time: datetime, guests: int, status: str) -> dict:
        return {}

    def set_reservation_status(self, index: int, status: str) -> str:
        return "База данных не подключена или бронь не выбрана."

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
            self.order_draft.append({"name": dish_name, "qty": 1, "price": dish["price"], "sum": dish["price"], "note": ""})
        return f"В заказ добавлено: {dish_name}."

    def set_draft_item_note(self, index: int, note: str) -> str:
        if index < 0 or index >= len(self.order_draft):
            return "Позиция не найдена."
        self.order_draft[index]["note"] = note
        return "Примечание сохранено."

    def clear_draft(self) -> None:
        self.order_draft.clear()

    def get_draft_total(self) -> int:
        return sum(item["sum"] for item in self.order_draft)

    def send_draft_to_kitchen(self, table_code: str, payment_method: str) -> tuple[bool, str]:
        return False, "База данных не подключена. Заказ не сохранен."

    def advance_order_status(self, index: int) -> str:
        return "База данных не подключена или заказ не выбран."

    def advance_kitchen_order(self, index: int) -> str:
        return "База данных не подключена или заказ не выбран."

    def complete_order(self, index: int) -> str:
        return "База данных не подключена или заказ не выбран."

    def get_order_items(self, order_id: int) -> list[dict]:
        return []

    def cancel_order_item(self, order_item_id: int) -> str:
        return "База данных не подключена."

    def cancel_order(self, order_id: int) -> str:
        return "База данных не подключена."

    def update_item_status(self, order_item_id: int, status_code: str) -> str:
        return "База данных не подключена."

    def assign_cook_to_order(self, order_id: int, cook_employee_id: int) -> str:
        return "База данных не подключена."

    def set_order_priority(self, order_id: int, priority: str) -> str:
        return "База данных не подключена."

    def start_order(self, order_id: int) -> str:
        return "База данных не подключена."

    def mark_item_ready(self, order_item_id: int) -> str:
        return "База данных не подключена."

    def add_order_item_note(self, order_item_id: int, note: str) -> str:
        return "База данных не подключена."

    def get_kitchen_stats(self) -> dict:
        return {"avg_prep_time": 0, "in_progress": 0, "completed_today": 0, "rush_active": 0}

    def get_active_orders_for_kitchen(self) -> list[dict]:
        return self.kitchen_queue

    def get_order_history(self, limit: int = 50) -> list[dict]:
        return []

    def log_kitchen_action(self, order_id: int, action: str, note: str = "") -> None:
        pass

    def get_cooks(self) -> list[dict]:
        return []

    def apply_inventory_operation(self, ingredient: str, operation_type: str, amount: float, note: str) -> str:
        return "База данных не подключена. Операция не сохранена."

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
