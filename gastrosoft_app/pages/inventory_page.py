from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
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


class InventoryPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store, project_root: Path) -> None:
        super().__init__()
        self.store = store
        self.project_root = project_root
        self.summary_cards: dict[str, MetricCard] = {}
        self.setObjectName("inventoryPage")
        self.setStyleSheet(load_style("styles", "inventory", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        summary_row = QHBoxLayout()
        for key, title, note in [
            ("items", "Позиций на складе", "Всего ингредиентов под контролем"),
            ("critical", "Низкие остатки", "Требуют оперативной реакции"),
            ("operations", "Операций сегодня", "Поступления, списания и корректировки"),
        ]:
            card = MetricCard(title, "0", note)
            self.summary_cards[key] = card
            summary_row.addWidget(card)
        root_layout.addLayout(summary_row)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(18)

        stock_card = SectionCard("Складские остатки", "Отдельная страница для учета ингредиентов и статусов.")
        self.inventory_table = QTableWidget(0, 5)
        self.inventory_table.setHorizontalHeaderLabels(["Ингредиент", "Остаток", "Ед.", "Минимум", "Статус"])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        stock_card.content_layout.addWidget(self.inventory_table)
        middle_row.addWidget(stock_card, 7)

        side_column = QVBoxLayout()
        side_column.setSpacing(18)

        operation_card = SectionCard("Операция по складу", "Кнопка сохраняет движение ингредиента в MySQL.")
        self.ingredient_combo = QComboBox()
        operation_card.content_layout.addWidget(self.ingredient_combo)

        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Поступление", "Списание", "Корректировка"])
        operation_card.content_layout.addWidget(self.operation_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.1, 9999.0)
        self.amount_spin.setDecimals(1)
        self.amount_spin.setValue(1.0)
        operation_card.content_layout.addWidget(self.amount_spin)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Комментарий к операции")
        operation_card.content_layout.addWidget(self.note_input)

        apply_button = QPushButton("Провести операцию")
        apply_button_variant(apply_button, "primary")
        apply_button.clicked.connect(self.apply_operation)
        operation_card.content_layout.addWidget(apply_button)
        side_column.addWidget(operation_card)

        report_card = SectionCard("Отчет и экспорт", "Файл формируется в папке exports проекта.")
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        report_card.content_layout.addWidget(self.report_preview)

        report_buttons = QHBoxLayout()
        refresh_report = QPushButton("Обновить отчет")
        apply_button_variant(refresh_report, "secondary")
        refresh_report.clicked.connect(self.refresh_report)
        report_buttons.addWidget(refresh_report)

        export_button = QPushButton("Экспортировать")
        apply_button_variant(export_button, "ghost")
        export_button.clicked.connect(self.export_report)
        report_buttons.addWidget(export_button)
        report_card.content_layout.addLayout(report_buttons)
        side_column.addWidget(report_card)

        middle_row.addLayout(side_column, 5)
        root_layout.addLayout(middle_row, 1)

        journal_card = SectionCard("Журнал операций", "Последние движения по складу в одном месте.")
        self.operations_table = QTableWidget(0, 5)
        self.operations_table.setHorizontalHeaderLabels(["Время", "Ингредиент", "Операция", "Количество", "Комментарий"])
        self.operations_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.operations_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.operations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.operations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        journal_card.content_layout.addWidget(self.operations_table)
        root_layout.addWidget(journal_card)

    def populate_inventory(self) -> None:
        self.inventory_table.setRowCount(len(self.store.inventory))
        self.ingredient_combo.clear()
        self.ingredient_combo.addItems([item["ingredient"] for item in self.store.inventory])
        for row_index, item_data in enumerate(self.store.inventory):
            status = "Норма"
            if item_data["stock"] <= item_data["threshold"]:
                status = "Низкий остаток"
            values = [
                item_data["ingredient"],
                f"{item_data['stock']}",
                item_data["unit"],
                f"{item_data['threshold']}",
                status,
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column_index == 4:
                    tint_table_item(item, "danger" if status == "Низкий остаток" else "success")
                self.inventory_table.setItem(row_index, column_index, item)

    def populate_operations(self) -> None:
        self.operations_table.setRowCount(len(self.store.operations))
        for row_index, operation in enumerate(self.store.operations):
            values = [
                operation["time"],
                operation["ingredient"],
                operation["type"],
                str(operation["amount"]),
                operation["note"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.operations_table.setItem(row_index, column_index, item)

    def refresh_summary(self) -> None:
        self.summary_cards["items"].set_value(str(len(self.store.inventory)), "Позиции в inventory_operation и рецептурах")
        self.summary_cards["critical"].set_value(str(len(self.store.low_stock_items())), "Ниже или на уровне минимального порога")
        self.summary_cards["operations"].set_value(str(len(self.store.operations)), "Журнал хранит движения из базы данных")

    def apply_operation(self) -> None:
        message = self.store.apply_inventory_operation(
            self.ingredient_combo.currentText(),
            self.operation_combo.currentText(),
            self.amount_spin.value(),
            self.note_input.text().strip(),
        )
        self.note_input.clear()
        self.refresh_page()
        self.status_message.emit(message)

    def refresh_report(self, silent: bool = False) -> None:
        self.report_preview.setPlainText(self.store.build_report())
        if not silent:
            self.status_message.emit("Текстовый отчет обновлен.")

    def export_report(self) -> None:
        export_path = self.store.export_report(self.project_root)
        self.status_message.emit(f"Отчет сохранен: {export_path}")

    def refresh_page(self) -> None:
        self.populate_inventory()
        self.populate_operations()
        self.refresh_summary()
        self.refresh_report(silent=True)
