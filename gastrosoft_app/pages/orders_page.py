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
from ..role_access import can_close_orders, can_create_orders, can_process_kitchen


KITCHEN_ACTIVE_STATUSES = {"Принят", "Готовится", "Готов"}
CASHIER_VISIBLE_STATUSES = {"Готов", "Выдан"}


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

        self.menu_hint = QLabel("Выбери категорию и блюдо, затем добавь позицию в текущий заказ.")
        self.menu_hint.setObjectName("sectionCardSubtitle")
        self.menu_hint.setWordWrap(True)
        self.menu_card.content_layout.addWidget(self.menu_hint)

        self.add_button = QPushButton("Добавить в заказ")
        apply_button_variant(self.add_button, "primary")
        self.add_button.clicked.connect(self.add_selected_dish)
        self.menu_card.content_layout.addWidget(self.add_button)
        root_layout.addWidget(self.menu_card, 5)

        self.order_card = SectionCard("Текущий заказ", "Черновик работает отдельно от кухонной очереди.")
        self.table_combo = QComboBox()
        self.table_combo.addItems([table["code"] for table in self.store.tables])
        self.order_card.content_layout.addWidget(self.table_combo)

        self.order_hint = QLabel("Выбери стол и способ оплаты перед передачей заказа на кухню.")
        self.order_hint.setObjectName("sectionCardSubtitle")
        self.order_hint.setWordWrap(True)
        self.order_card.content_layout.addWidget(self.order_hint)

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
        self.remove_button = QPushButton("Убрать позицию")
        apply_button_variant(self.remove_button, "secondary")
        self.remove_button.clicked.connect(self.remove_selected_dish)
        draft_buttons.addWidget(self.remove_button)

        self.clear_button = QPushButton("Очистить заказ")
        apply_button_variant(self.clear_button, "danger")
        self.clear_button.clicked.connect(self.clear_order)
        draft_buttons.addWidget(self.clear_button)
        self.order_card.content_layout.addLayout(draft_buttons)

        self.send_button = QPushButton("Передать на кухню")
        apply_button_variant(self.send_button, "primary")
        self.send_button.clicked.connect(self.send_to_kitchen)
        self.order_card.content_layout.addWidget(self.send_button)
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

        self.refresh_queue_button = QPushButton("Обновить")
        apply_button_variant(self.refresh_queue_button, "secondary")
        self.refresh_queue_button.clicked.connect(self.refresh_kitchen_queue)
        kitchen_controls_layout.addWidget(self.refresh_queue_button)
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

    def refresh_selectors(self) -> None:
        self._sync_combo(self.category_combo, self.store.categories(), "Нет блюд в базе")
        self._sync_combo(self.table_combo, [table["code"] for table in self.store.tables], "Нет активных столов")

    def _sync_combo(self, combo: QComboBox, values: list[str], empty_text: str) -> None:
        current_value = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        if values:
            combo.addItems(values)
            combo.setEnabled(True)
            if current_value in values:
                combo.setCurrentText(current_value)
        else:
            combo.addItem(empty_text)
            combo.setEnabled(False)
        combo.blockSignals(False)

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
            self.menu_hint.setText("Выбери категорию и блюдо, затем добавь позицию в текущий заказ.")
        else:
            self.menu_hint.setText("В базе нет активных блюд для оформления заказа. Заполни справочник меню в MySQL.")
        self.add_button.setEnabled(bool(dishes) and can_create_orders(self._current_role()))

    def populate_draft(self) -> None:
        self.draft_table.setRowCount(len(self.store.order_draft))
        for row_index, item_data in enumerate(self.store.order_draft):
            values = [item_data["name"], str(item_data["qty"]), f"{item_data['price']} ₽", f"{item_data['sum']} ₽"]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.draft_table.setItem(row_index, column_index, item)

        self.total_pill.set_state(f"Итого: {self.store.get_draft_total()} ₽", "info")
        has_draft = bool(self.store.order_draft)
        has_tables = bool(self.store.tables)
        self.remove_button.setEnabled(has_draft)
        self.clear_button.setEnabled(has_draft)
        self.send_button.setEnabled(has_draft and has_tables and can_create_orders(self._current_role()))
        if not has_tables:
            self.order_hint.setText("В базе нет активных столов. Без стола заказ нельзя передать на кухню.")
        elif not has_draft:
            self.order_hint.setText("Добавь хотя бы одно блюдо в текущий заказ.")
        else:
            self.order_hint.setText("Заказ готов к передаче на кухню.")

    def populate_kitchen(self) -> None:
        role = self._current_role()
        is_kitchen = can_process_kitchen(role)
        headers = (
            ["Номер", "Стол", "Время", "Состав заказа", "Статус"]
            if is_kitchen
            else ["Номер", "Стол", "Время", "Состав", "Статус"]
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
                else [
                    queue_item["order_no"],
                    queue_item["table"],
                    queue_item.get("created", "-"),
                    queue_item["items"],
                    queue_item["status"],
                ]
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
        if not can_create_orders(self._current_role()):
            self.status_message.emit("У этой роли нет права оформлять заказы.")
            return
        if not self.store.tables:
            self.status_message.emit("В базе нет активных столов. Заказ не может быть создан.")
            return
        success, message = self.store.send_draft_to_kitchen(self.table_combo.currentText(), self.payment_combo.currentText())
        self.populate_draft()
        self.populate_kitchen()
        self.status_message.emit(message)
        if success:
            self.total_pill.set_state("Итого: 0 ₽", "info")

    def advance_status(self) -> None:
        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.status_message.emit("Выбери заказ в списке.")
            return

        if can_process_kitchen(self._current_role()) and hasattr(self.store, "advance_kitchen_order"):
            message = self.store.advance_kitchen_order(queue_index)
        else:
            message = self.store.advance_order_status(queue_index)
        self.populate_kitchen()
        self.status_message.emit(message)

    def complete_order(self) -> None:
        if not can_close_orders(self._current_role()):
            self.status_message.emit("У этой роли нет права закрывать заказ.")
            return
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
        if hasattr(self.store, "reload_from_mysql") and getattr(self.store, "mysql_enabled", False):
            self.store.reload_from_mysql()
        self.apply_role_mode()
        self.refresh_selectors()
        self.populate_dishes()
        self.populate_draft()
        self.populate_kitchen()

    def apply_role_mode(self) -> None:
        role = self._current_role()
        can_create = can_create_orders(role)
        is_kitchen = can_process_kitchen(role)
        can_close = can_close_orders(role)
        show_order_list = is_kitchen or can_close

        self.menu_card.setVisible(can_create)
        self.order_card.setVisible(can_create)
        self.kitchen_card.setVisible(show_order_list)
        self.kitchen_controls.setVisible(is_kitchen)
        self.next_status_button.setVisible(is_kitchen)
        self.close_order_button.setVisible(can_close)

        if is_kitchen:
            self.kitchen_card.set_header("Кухонная очередь", "Повар и шеф-повар меняют только статусы приготовления.")
            self.next_status_button.setText("Взять в работу")
        elif can_close:
            self.kitchen_card.set_header("Заказы к оплате", "Кассир закрывает готовые и выданные заказы.")
        else:
            self.kitchen_card.set_header("Очередь заказов", "Просмотр заказов текущей смены.")

    def update_kitchen_summary(self) -> None:
        counts = {
            status: len([item for item in self.store.kitchen_queue if item["status"] == status])
            for status in KITCHEN_ACTIVE_STATUSES
        }
        self.summary_pills["accepted"].set_state(f"Принято: {counts['Принят']}", "warning")
        self.summary_pills["preparing"].set_state(f"В работе: {counts['Готовится']}", "info")
        self.summary_pills["ready"].set_state(f"Готово: {counts['Готов']}", "success")

    def update_kitchen_actions(self) -> None:
        role = self._current_role()
        if not can_process_kitchen(role):
            self.next_status_button.setEnabled(False)
            self.close_order_button.setEnabled(self._selected_queue_index() >= 0 and can_close_orders(role))
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
        role = self._current_role()
        for index, item in enumerate(self.store.kitchen_queue):
            status = item["status"]
            if can_process_kitchen(role) and status not in KITCHEN_ACTIVE_STATUSES:
                continue
            if can_process_kitchen(role) and selected_status != "Все активные" and status != selected_status:
                continue
            if role == "Кассир" and status not in CASHIER_VISIBLE_STATUSES:
                continue
            indices.append(index)
        return indices

    def _selected_queue_index(self) -> int:
        row = self.kitchen_table.currentRow()
        if row < 0 or row >= len(self.visible_queue_indices):
            return -1
        return self.visible_queue_indices[row]

    def _current_role(self) -> str | None:
        user = self.store.current_user or {}
        return user.get("role")
