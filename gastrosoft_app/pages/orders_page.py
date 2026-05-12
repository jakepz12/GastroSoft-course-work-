from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ..style_utils import load_style
from ..widgets import SectionCard, StatusPill, apply_button_variant, tint_table_item


class OrdersPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.setObjectName("ordersPage")
        self.setStyleSheet(load_style("styles", "orders", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        menu_card = SectionCard("Меню", "Категории и блюда оформлены как отдельный рабочий экран.")
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.store.categories())
        self.category_combo.currentTextChanged.connect(self.populate_dishes)
        menu_card.content_layout.addWidget(self.category_combo)

        self.menu_table = QTableWidget(0, 3)
        self.menu_table.setHorizontalHeaderLabels(["Блюдо", "Цена", "Готовность"])
        self.menu_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.menu_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.menu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.menu_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        menu_card.content_layout.addWidget(self.menu_table)

        add_button = QPushButton("Добавить в заказ")
        apply_button_variant(add_button, "primary")
        add_button.clicked.connect(self.add_selected_dish)
        menu_card.content_layout.addWidget(add_button)
        root_layout.addWidget(menu_card, 5)

        order_card = SectionCard("Текущий заказ", "Черновик работает отдельно от кухонной очереди.")
        self.table_combo = QComboBox()
        self.table_combo.addItems([table["code"] for table in self.store.tables])
        order_card.content_layout.addWidget(self.table_combo)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "QR-оплата"])
        order_card.content_layout.addWidget(self.payment_combo)

        self.draft_table = QTableWidget(0, 4)
        self.draft_table.setHorizontalHeaderLabels(["Позиция", "Кол-во", "Цена", "Сумма"])
        self.draft_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.draft_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.draft_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.draft_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        order_card.content_layout.addWidget(self.draft_table)

        self.total_pill = StatusPill("Итого: 0 ₽", "info")
        order_card.content_layout.addWidget(self.total_pill)

        draft_buttons = QHBoxLayout()
        remove_button = QPushButton("Убрать позицию")
        apply_button_variant(remove_button, "secondary")
        remove_button.clicked.connect(self.remove_selected_dish)
        draft_buttons.addWidget(remove_button)

        clear_button = QPushButton("Очистить заказ")
        apply_button_variant(clear_button, "danger")
        clear_button.clicked.connect(self.clear_order)
        draft_buttons.addWidget(clear_button)
        order_card.content_layout.addLayout(draft_buttons)

        send_button = QPushButton("Передать на кухню")
        apply_button_variant(send_button, "primary")
        send_button.clicked.connect(self.send_to_kitchen)
        order_card.content_layout.addWidget(send_button)
        root_layout.addWidget(order_card, 5)

        kitchen_card = SectionCard("Очередь кухни", "Отдельные кнопки меняют статус заказа и закрывают его.")
        self.kitchen_table = QTableWidget(0, 4)
        self.kitchen_table.setHorizontalHeaderLabels(["Номер", "Стол", "Состав", "Статус"])
        self.kitchen_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kitchen_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.kitchen_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.kitchen_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        kitchen_card.content_layout.addWidget(self.kitchen_table)

        kitchen_buttons = QHBoxLayout()
        next_status = QPushButton("Следующий статус")
        apply_button_variant(next_status, "warning")
        next_status.clicked.connect(self.advance_status)
        kitchen_buttons.addWidget(next_status)

        close_button = QPushButton("Закрыть заказ")
        apply_button_variant(close_button, "ghost")
        close_button.clicked.connect(self.complete_order)
        kitchen_buttons.addWidget(close_button)
        kitchen_card.content_layout.addLayout(kitchen_buttons)

        root_layout.addWidget(kitchen_card, 6)

    def populate_dishes(self) -> None:
        dishes = self.store.dishes_by_category(self.category_combo.currentText())
        self.menu_table.setRowCount(len(dishes))
        for row_index, dish in enumerate(dishes):
            for column_index, value in enumerate([dish["name"], f"{dish['price']} ₽", dish["ready"]]):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.menu_table.setItem(row_index, column_index, item)
        if dishes:
            self.menu_table.selectRow(0)

    def populate_draft(self) -> None:
        self.draft_table.setRowCount(len(self.store.order_draft))
        for row_index, item_data in enumerate(self.store.order_draft):
            values = [item_data["name"], str(item_data["qty"]), f"{item_data['price']} ₽", f"{item_data['sum']} ₽"]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.draft_table.setItem(row_index, column_index, item)

        self.total_pill.set_state(f"Итого: {self.store.get_draft_total()} ₽", "info")

    def populate_kitchen(self) -> None:
        self.kitchen_table.setRowCount(len(self.store.kitchen_queue))
        for row_index, queue_item in enumerate(self.store.kitchen_queue):
            values = [queue_item["order_no"], queue_item["table"], queue_item["items"], queue_item["status"]]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column_index == 3:
                    tone = "warning"
                    if value == "Готов":
                        tone = "success"
                    elif value == "Выдан":
                        tone = "muted"
                    elif value == "Готовится":
                        tone = "info"
                    tint_table_item(item, tone)
                self.kitchen_table.setItem(row_index, column_index, item)

    def add_selected_dish(self) -> None:
        row = self.menu_table.currentRow()
        if row < 0:
            self.status_message.emit("Выбери блюдо из меню.")
            return

        dish_item = self.menu_table.item(row, 0)
        if dish_item is None:
            self.status_message.emit("Блюдо не найдено.")
            return

        message = self.store.add_dish_to_draft(dish_item.text())
        self.populate_draft()
        self.status_message.emit(message)

    def remove_selected_dish(self) -> None:
        row = self.draft_table.currentRow()
        if row < 0 or row >= len(self.store.order_draft):
            self.status_message.emit("Выбери позицию в черновике заказа.")
            return

        self.store.order_draft.pop(row)
        self.populate_draft()
        self.status_message.emit("Позиция удалена из текущего заказа.")

    def clear_order(self) -> None:
        self.store.clear_draft()
        self.populate_draft()
        self.status_message.emit("Черновик заказа очищен.")

    def send_to_kitchen(self) -> None:
        success, message = self.store.send_draft_to_kitchen(self.table_combo.currentText(), self.payment_combo.currentText())
        self.populate_draft()
        self.populate_kitchen()
        self.status_message.emit(message)
        if success:
            self.total_pill.set_state("Итого: 0 ₽", "info")

    def advance_status(self) -> None:
        message = self.store.advance_order_status(self.kitchen_table.currentRow())
        self.populate_kitchen()
        self.status_message.emit(message)

    def complete_order(self) -> None:
        message = self.store.complete_order(self.kitchen_table.currentRow())
        self.populate_kitchen()
        self.status_message.emit(message)

    def refresh_page(self) -> None:
        self.populate_dishes()
        self.populate_draft()
        self.populate_kitchen()
