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


KITCHEN_ROLES = {"Повар", "Шеф-повар"}
KITCHEN_ACTIVE_STATUSES = {"Принят", "Готовится", "Готов"}


class OrdersPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.visible_queue_indices: list[int] = []
        self.summary_pills: dict[str, StatusPill] = {}
        self.setObjectName("ordersPage")
        self.setStyleSheet(load_style("styles", "orders", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        self.menu_card = SectionCard("Меню", "Категории и блюда оформлены как отдельный рабочий экран.")
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.store.categories())
        self.category_combo.currentTextChanged.connect(self.populate_dishes)
        self.menu_card.content_layout.addWidget(self.category_combo)

        self.menu_table = QTableWidget(0, 3)
        self.menu_table.setHorizontalHeaderLabels(["Блюдо", "Цена", "Готовность"])
        self.menu_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.menu_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.menu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.menu_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.menu_card.content_layout.addWidget(self.menu_table)

        add_button = QPushButton("Добавить в заказ")
        apply_button_variant(add_button, "primary")
        add_button.clicked.connect(self.add_selected_dish)
        self.menu_card.content_layout.addWidget(add_button)
        root_layout.addWidget(self.menu_card, 5)

        self.order_card = SectionCard("Текущий заказ", "Черновик работает отдельно от кухонной очереди.")
        self.table_combo = QComboBox()
        self.table_combo.addItems([table["code"] for table in self.store.tables])
        self.order_card.content_layout.addWidget(self.table_combo)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "QR-оплата"])
        self.order_card.content_layout.addWidget(self.payment_combo)

        self.draft_table = QTableWidget(0, 4)
        self.draft_table.setHorizontalHeaderLabels(["Позиция", "Кол-во", "Цена", "Сумма"])
        self.draft_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.draft_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.draft_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.draft_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_card.content_layout.addWidget(self.draft_table)

        self.total_pill = StatusPill("Итого: 0 ₽", "info")
        self.order_card.content_layout.addWidget(self.total_pill)

        draft_buttons = QHBoxLayout()
        remove_button = QPushButton("Убрать позицию")
        apply_button_variant(remove_button, "secondary")
        remove_button.clicked.connect(self.remove_selected_dish)
        draft_buttons.addWidget(remove_button)

        clear_button = QPushButton("Очистить заказ")
        apply_button_variant(clear_button, "danger")
        clear_button.clicked.connect(self.clear_order)
        draft_buttons.addWidget(clear_button)
        self.order_card.content_layout.addLayout(draft_buttons)

        send_button = QPushButton("Передать на кухню")
        apply_button_variant(send_button, "primary")
        send_button.clicked.connect(self.send_to_kitchen)
        self.order_card.content_layout.addWidget(send_button)
        root_layout.addWidget(self.order_card, 5)

        self.kitchen_card = SectionCard("Очередь кухни", "Отдельные кнопки меняют статус заказа и закрывают его.")

        self.kitchen_controls = QWidget()
        kitchen_controls_layout = QHBoxLayout(self.kitchen_controls)
        kitchen_controls_layout.setContentsMargins(0, 0, 0, 0)
        kitchen_controls_layout.setSpacing(10)

        filter_label = QLabel("Фильтр")
        kitchen_controls_layout.addWidget(filter_label)

        self.kitchen_filter = QComboBox()
        self.kitchen_filter.addItems(["Все активные", "Принят", "Готовится", "Готов"])
        self.kitchen_filter.currentTextChanged.connect(lambda _text: self.populate_kitchen())
        kitchen_controls_layout.addWidget(self.kitchen_filter, 2)

        for key, label, tone in [
            ("accepted", "Принято: 0", "warning"),
            ("preparing", "В работе: 0", "info"),
            ("ready", "Готово: 0", "success"),
        ]:
            pill = StatusPill(label, tone)
            self.summary_pills[key] = pill
            kitchen_controls_layout.addWidget(pill)

        refresh_button = QPushButton("Обновить")
        apply_button_variant(refresh_button, "secondary")
        refresh_button.clicked.connect(self.refresh_kitchen_queue)
        kitchen_controls_layout.addWidget(refresh_button)
        self.kitchen_card.content_layout.addWidget(self.kitchen_controls)

        self.kitchen_table = QTableWidget(0, 4)
        self.kitchen_table.setHorizontalHeaderLabels(["Номер", "Стол", "Состав", "Статус"])
        self.kitchen_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kitchen_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.kitchen_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.kitchen_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.kitchen_table.itemSelectionChanged.connect(self.update_kitchen_actions)
        self.kitchen_card.content_layout.addWidget(self.kitchen_table)

        kitchen_buttons = QHBoxLayout()
        self.next_status_button = QPushButton("Следующий статус")
        apply_button_variant(self.next_status_button, "warning")
        self.next_status_button.clicked.connect(self.advance_status)
        kitchen_buttons.addWidget(self.next_status_button)

        self.close_order_button = QPushButton("Закрыть заказ")
        apply_button_variant(self.close_order_button, "ghost")
        self.close_order_button.clicked.connect(self.complete_order)
        kitchen_buttons.addWidget(self.close_order_button)
        self.kitchen_card.content_layout.addLayout(kitchen_buttons)

        root_layout.addWidget(self.kitchen_card, 6)

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
        is_kitchen = self._is_kitchen_user()
        headers = (
            ["Номер", "Стол", "Время", "Состав заказа", "Статус"]
            if is_kitchen
            else ["Номер", "Стол", "Состав", "Статус"]
        )
        self.kitchen_table.setColumnCount(len(headers))
        self.kitchen_table.setHorizontalHeaderLabels(headers)
        self.kitchen_table.verticalHeader().setDefaultSectionSize(58 if is_kitchen else 34)

        self.visible_queue_indices = self._filtered_queue_indices()
        self.kitchen_table.setRowCount(len(self.visible_queue_indices))
        for row_index, queue_index in enumerate(self.visible_queue_indices):
            queue_item = self.store.kitchen_queue[queue_index]
            values = (
                [
                    queue_item["order_no"],
                    queue_item["table"],
                    queue_item.get("created", "-"),
                    queue_item["items"],
                    queue_item["status"],
                ]
                if is_kitchen
                else [queue_item["order_no"], queue_item["table"], queue_item["items"], queue_item["status"]]
            )
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(str(value))
                if column_index == len(headers) - 1:
                    tone = "warning"
                    if value == "Готов":
                        tone = "success"
                    elif value == "Выдан":
                        tone = "muted"
                    elif value == "Готовится":
                        tone = "info"
                    tint_table_item(item, tone)
                self.kitchen_table.setItem(row_index, column_index, item)
        if self.visible_queue_indices:
            self.kitchen_table.selectRow(0)

        self.update_kitchen_summary()
        self.update_kitchen_actions()

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
        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.status_message.emit("Выбери заказ в очереди кухни.")
            return

        if self._is_kitchen_user() and hasattr(self.store, "advance_kitchen_order"):
            message = self.store.advance_kitchen_order(queue_index)
        else:
            message = self.store.advance_order_status(queue_index)
        self.populate_kitchen()
        self.status_message.emit(message)

    def complete_order(self) -> None:
        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.status_message.emit("Выбери заказ в очереди кухни.")
            return

        message = self.store.complete_order(queue_index)
        self.populate_kitchen()
        self.status_message.emit(message)

    def refresh_kitchen_queue(self) -> None:
        if hasattr(self.store, "reload_from_mysql"):
            self.store.reload_from_mysql()
        self.populate_kitchen()
        self.status_message.emit("Очередь кухни обновлена.")

    def refresh_page(self) -> None:
        self.apply_role_mode()
        self.populate_dishes()
        self.populate_draft()
        self.populate_kitchen()

    def apply_role_mode(self) -> None:
        is_kitchen = self._is_kitchen_user()
        self.menu_card.setVisible(not is_kitchen)
        self.order_card.setVisible(not is_kitchen)
        self.kitchen_controls.setVisible(is_kitchen)
        self.close_order_button.setVisible(not is_kitchen)
        self.next_status_button.setText("Взять в работу" if is_kitchen else "Следующий статус")

    def update_kitchen_summary(self) -> None:
        counts = {
            status: len([item for item in self.store.kitchen_queue if item["status"] == status])
            for status in KITCHEN_ACTIVE_STATUSES
        }
        self.summary_pills["accepted"].set_state(f"Принято: {counts['Принят']}", "warning")
        self.summary_pills["preparing"].set_state(f"В работе: {counts['Готовится']}", "info")
        self.summary_pills["ready"].set_state(f"Готово: {counts['Готов']}", "success")

    def update_kitchen_actions(self) -> None:
        if not self._is_kitchen_user():
            self.next_status_button.setEnabled(True)
            return

        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.next_status_button.setText("Выбери заказ")
            self.next_status_button.setEnabled(False)
            return

        status = self.store.kitchen_queue[queue_index]["status"]
        next_actions = {
            "Принят": ("Взять в работу", True),
            "Готовится": ("Отметить готовым", True),
            "Готов": ("Заказ готов", False),
            "Выдан": ("Уже выдан", False),
        }
        text, enabled = next_actions.get(status, ("Следующий этап", True))
        self.next_status_button.setText(text)
        self.next_status_button.setEnabled(enabled)

    def _filtered_queue_indices(self) -> list[int]:
        selected_status = self.kitchen_filter.currentText()
        indices = []
        for index, item in enumerate(self.store.kitchen_queue):
            status = item["status"]
            if self._is_kitchen_user() and status not in KITCHEN_ACTIVE_STATUSES:
                continue
            if self._is_kitchen_user() and selected_status != "Все активные" and status != selected_status:
                continue
            indices.append(index)
        return indices

    def _selected_queue_index(self) -> int:
        row = self.kitchen_table.currentRow()
        if row < 0 or row >= len(self.visible_queue_indices):
            return -1
        return self.visible_queue_indices[row]

    def _is_kitchen_user(self) -> bool:
        user = self.store.current_user or {}
        return user.get("role") in KITCHEN_ROLES
