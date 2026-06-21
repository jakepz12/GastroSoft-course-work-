from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ..style_utils import load_style
from ..widgets import MetricCard, SectionCard, apply_button_variant, tint_table_item


class ReportsPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store, project_root: Path) -> None:
        super().__init__()
        self.store = store
        self.project_root = project_root
        self.summary_cards: dict[str, MetricCard] = {}
        self.setObjectName("reportsPage")
        self.setStyleSheet(load_style("styles", "reports", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        title = QLabel("Отчёты кухни")
        title.setObjectName("reportsTitle")
        root_layout.addWidget(title)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, title_text, note in [
            ("avg_time", "Среднее время", "Приготовления блюда"),
            ("completed", "Выполнено", "Заказов за сегодня"),
            ("rush", "Срочных", "С приоритетом rush"),
            ("in_progress", "В работе", "Сейчас на кухне"),
            ("revenue", "Выручка", "Сегодня"),
        ]:
            card = MetricCard(title_text, "0", note)
            self.summary_cards[key] = card
            summary_row.addWidget(card)
        root_layout.addLayout(summary_row)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(18)

        history_card = SectionCard("История заказов", "Последние заказы с деталями.")
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Номер", "Стол", "Статус", "Приоритет", "Сумма"])
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.itemSelectionChanged.connect(self._on_order_selected)
        history_card.content_layout.addWidget(self.history_table)
        middle_row.addWidget(history_card, 7)

        detail_column = QVBoxLayout()
        detail_column.setSpacing(16)

        detail_card = SectionCard("Состав заказа", "Позиции выбранного заказа.")
        self.detail_table = QTableWidget(0, 4)
        self.detail_table.setHorizontalHeaderLabels(["Блюдо", "Кол-во", "Статус", "Примечание"])
        self.detail_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        detail_card.content_layout.addWidget(self.detail_table)
        detail_column.addWidget(detail_card)

        report_card = SectionCard("Текстовый отчёт", "Сводка по кухне за сегодня.")
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        report_card.content_layout.addWidget(self.report_preview)

        report_buttons = QHBoxLayout()
        refresh_report = QPushButton("Обновить отчёт")
        apply_button_variant(refresh_report, "secondary")
        refresh_report.clicked.connect(self.refresh_report)
        report_buttons.addWidget(refresh_report)

        export_button = QPushButton("Экспортировать")
        apply_button_variant(export_button, "primary")
        export_button.clicked.connect(self.export_report)
        report_buttons.addWidget(export_button)
        report_card.content_layout.addLayout(report_buttons)
        detail_column.addWidget(report_card)

        middle_row.addLayout(detail_column, 5)
        root_layout.addLayout(middle_row, 1)

    def refresh_page(self) -> None:
        if hasattr(self.store, "reload_from_mysql") and getattr(self.store, "mysql_enabled", False):
            self.store.reload_from_mysql()
        self._refresh_stats()
        self._populate_history()
        self.refresh_report(silent=True)

    def _refresh_stats(self) -> None:
        if hasattr(self.store, "get_kitchen_stats"):
            stats = self.store.get_kitchen_stats()
            self.summary_cards["avg_time"].set_value(f"{stats['avg_prep_time']} мин", "Среднее время приготовления")
            self.summary_cards["completed"].set_value(str(stats["completed_today"]), "Заказов выполнено за сегодня")
            self.summary_cards["rush"].set_value(str(stats["rush_active"]), "Срочных заказов")
            self.summary_cards["in_progress"].set_value(str(stats["in_progress"]), "Сейчас на кухне")

        revenue = 0
        if hasattr(self.store, "get_order_history"):
            history = self.store.get_order_history(limit=100)
            for order in history:
                if order.get("status") in ("Закрыт", "Выдан"):
                    revenue += order.get("total", 0)
        self.summary_cards["revenue"].set_value(f"{revenue:,} \u20bd".replace(",", " "), "Выручка за сегодня")

    def _populate_history(self) -> None:
        if hasattr(self.store, "get_order_history"):
            history = self.store.get_order_history(limit=30)
        else:
            history = []

        self.history_table.setRowCount(len(history))
        for row_index, order in enumerate(history):
            values = [
                order.get("order_no", f"GS-{order.get('order_id', '?')}"),
                order.get("table", "-"),
                order.get("status", "-"),
                order.get("priority", "normal"),
                f"{order.get('total', 0):,} \u20bd".replace(",", " "),
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column_index == 2:
                    tone = {
                        "Принят": "warning",
                        "Готовится": "info",
                        "Готов": "success",
                        "Выдан": "muted",
                        "Закрыт": "muted",
                    }.get(value, "info")
                    tint_table_item(item, tone)
                if column_index == 3:
                    tone = "danger" if value == "rush" else "muted"
                    tint_table_item(item, tone)
                self.history_table.setItem(row_index, column_index, item)

        if history:
            self.history_table.selectRow(0)

    def _on_order_selected(self) -> None:
        row = self.history_table.currentRow()
        if row < 0:
            return

        order_no = self.history_table.item(row, 0)
        if order_no is None:
            return

        order_no_text = order_no.text()
        try:
            order_id = int(order_no_text.replace("GS-", ""))
        except ValueError:
            return

        items = self.store.get_order_items(order_id) if hasattr(self.store, "get_order_items") else []

        self.detail_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            values = [
                item.get("dish", "?"),
                str(item.get("quantity", 1)),
                item.get("status", "-"),
                item.get("note", ""),
            ]
            for column_index, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column_index == 2:
                    tone = {
                        "В очереди": "warning",
                        "Готовится": "info",
                        "Готово": "success",
                        "Подано": "muted",
                    }.get(value, "info")
                    tint_table_item(cell, tone)
                self.detail_table.setItem(row_index, column_index, cell)

    def refresh_report(self, silent: bool = False) -> None:
        self.report_preview.setPlainText(self._build_report())
        if not silent:
            self.status_message.emit("Отчёт обновлён.")

    def _build_report(self) -> str:
        stats = self.store.get_kitchen_stats() if hasattr(self.store, "get_kitchen_stats") else {}
        orders = self.store.get_active_orders_for_kitchen() if hasattr(self.store, "get_active_orders_for_kitchen") else []
        history = self.store.get_order_history(limit=50) if hasattr(self.store, "get_order_history") else []

        revenue = sum(o.get("total", 0) for o in history if o.get("status") in ("Закрыт", "Выдан"))
        dish_counts: dict[str, int] = {}
        for o in orders:
            items = o.get("items", [])
            if isinstance(items, list):
                for item in items:
                    name = item.get("dish", "?")
                    dish_counts[name] = dish_counts.get(name, 0) + item.get("quantity", 1)

        lines = [
            "ОТЧЁТ КУХНИ GASTROSoft",
            f"Дата: {datetime.now():%d.%m.%Y %H:%M}",
            "",
            "=== СТАТИСТИКА ===",
            f"Среднее время приготовления: {stats.get('avg_prep_time', 0)} мин",
            f"Заказов в работе: {stats.get('in_progress', 0)}",
            f"Выполнено за сегодня: {stats.get('completed_today', 0)}",
            f"Срочных заказов: {stats.get('rush_active', 0)}",
            f"Выручка: {revenue:,} \u20bd".replace(",", " "),
            "",
            "=== ТОП БЛЮД (в работе) ===",
        ]

        if dish_counts:
            sorted_dishes = sorted(dish_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for name, count in sorted_dishes:
                lines.append(f"  {name}: {count} шт.")
        else:
            lines.append("  Нет активных блюд")

        lines.extend(["", "=== АКТИВНЫЕ ЗАКАЗЫ ==="])

        if orders:
            for order in orders:
                priority = " [СРОЧНО]" if order.get("priority") == "rush" else ""
                cook = f" (повар: {order['cook_name']})" if order.get("cook_name") else ""
                lines.append(f"  {order['order_no']} — Стол {order['table']} — {order['status']}{priority}{cook}")
                items = order.get("items", [])
                if isinstance(items, list):
                    for item in items:
                        note = f" [{item['note']}]" if item.get("note") else ""
                        lines.append(f"    - {item['dish']} x{item['quantity']} — {item['status']}{note}")
        else:
            lines.append("  Нет активных заказов")

        lines.extend(["", "=== ПОСЛЕДНИЕ ЗАКРЫТЫЕ ==="])
        closed = [o for o in history if o.get("status") in ("Закрыт", "Выдан")][:10]
        if closed:
            for order in closed:
                lines.append(f"  {order['order_no']} — {order['table']} — {order['status']} — {order.get('total', 0)} \u20bd")
        else:
            lines.append("  Нет закрытых заказов")

        return "\n".join(lines)

    def export_report(self) -> None:
        export_dir = self.project_root / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "kitchen_report.txt"
        export_path.write_text(self._build_report(), encoding="utf-8")
        self.status_message.emit(f"Отчёт сохранён: {export_path}")
