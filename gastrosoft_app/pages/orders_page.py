from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ..style_utils import load_style
from ..widgets import SectionCard, StatusPill, apply_button_variant, tint_table_item
from ..role_access import can_close_orders, can_create_orders, can_process_kitchen


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
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("ordersTabs")
        root_layout.addWidget(self.tabs)

        self._build_menu_tab()
        self._build_draft_tab()
        self._build_queue_tab()

    def _build_menu_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Меню ресторана")
        header.setObjectName("ordersTabHeader")
        layout.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.store.categories())
        self.category_combo.currentTextChanged.connect(self.populate_dishes)
        controls.addWidget(QLabel("Категория:"))
        controls.addWidget(self.category_combo, 1)
        controls.addStretch(1)

        controls.addWidget(QLabel("Кол-во:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99)
        self.qty_spin.setValue(1)
        self.qty_spin.setMinimumWidth(60)
        controls.addWidget(self.qty_spin)

        self.add_button = QPushButton("Добавить в заказ")
        apply_button_variant(self.add_button, "primary")
        self.add_button.clicked.connect(self.add_selected_dish)
        controls.addWidget(self.add_button)
        layout.addLayout(controls)

        self.menu_table = QTableWidget(0, 3)
        self.menu_table.setHorizontalHeaderLabels(["Блюдо", "Цена", "Время приготовления"])
        self.menu_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.menu_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.menu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.menu_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.menu_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.menu_table, 1)

        self.menu_hint = QLabel("Выбери категорию и блюдо, затем нажми «Добавить в заказ».")
        self.menu_hint.setObjectName("sectionCardSubtitle")
        layout.addWidget(self.menu_hint)

        self.tabs.addTab(page, "Меню")
        self.tabs.setTabToolTip(0, "Выбор блюд из меню ресторана")

    def _build_draft_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Текущий заказ")
        header.setObjectName("ordersTabHeader")
        layout.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        controls.addWidget(QLabel("Стол:"))
        self.table_combo = QComboBox()
        self.table_combo.addItems([table["code"] for table in self.store.tables])
        controls.addWidget(self.table_combo)

        controls.addWidget(QLabel("Оплата:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "QR-оплата"])
        controls.addWidget(self.payment_combo)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.draft_table = QTableWidget(0, 5)
        self.draft_table.setHorizontalHeaderLabels(["Позиция", "Кол-во", "Цена", "Сумма", "Примечание"])
        self.draft_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.draft_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.draft_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.draft_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.draft_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.draft_table, 1)

        note_row = QHBoxLayout()
        note_row.setSpacing(8)
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Примечание к выбранной позиции (без лука, острее...)")
        note_row.addWidget(self.note_input, 1)
        self.note_button = QPushButton("Примечание")
        apply_button_variant(self.note_button, "secondary")
        self.note_button.clicked.connect(self.set_note_for_selected)
        note_row.addWidget(self.note_button)
        layout.addLayout(note_row)

        self.total_pill = StatusPill("Итого: 0 \u20bd", "info")
        layout.addWidget(self.total_pill)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.remove_button = QPushButton("Убрать позицию")
        apply_button_variant(self.remove_button, "secondary")
        self.remove_button.clicked.connect(self.remove_selected_dish)
        buttons.addWidget(self.remove_button)

        self.clear_button = QPushButton("Очистить заказ")
        apply_button_variant(self.clear_button, "danger")
        self.clear_button.clicked.connect(self.clear_order)
        buttons.addWidget(self.clear_button)

        buttons.addStretch(1)

        self.send_button = QPushButton("Передать на кухню")
        apply_button_variant(self.send_button, "primary")
        self.send_button.clicked.connect(self.send_to_kitchen)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)

        self.order_hint = QLabel("Добавь блюда из вкладки «Меню».")
        self.order_hint.setObjectName("sectionCardSubtitle")
        layout.addWidget(self.order_hint)

        self.tabs.addTab(page, "Текущий заказ")
        self.tabs.setTabToolTip(1, "Черновик заказа перед отправкой на кухню")

    def _build_queue_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Очередь заказов")
        header.setObjectName("ordersTabHeader")
        layout.addWidget(header)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        controls.addWidget(QLabel("Фильтр:"))
        self.kitchen_filter = QComboBox()
        self.kitchen_filter.addItems(["Все активные", "Принят", "Готовится", "Готов"])
        self.kitchen_filter.currentTextChanged.connect(lambda _text: self.populate_kitchen())
        controls.addWidget(self.kitchen_filter, 1)

        for key, label, tone in [
            ("accepted", "Принято: 0", "warning"),
            ("preparing", "В работе: 0", "info"),
            ("ready", "Готово: 0", "success"),
        ]:
            pill = StatusPill(label, tone)
            self.summary_pills[key] = pill
            controls.addWidget(pill)

        self.refresh_queue_button = QPushButton("Обновить")
        apply_button_variant(self.refresh_queue_button, "secondary")
        self.refresh_queue_button.clicked.connect(self.refresh_kitchen_queue)
        controls.addWidget(self.refresh_queue_button)
        layout.addLayout(controls)

        self.kitchen_table = QTableWidget(0, 5)
        self.kitchen_table.setHorizontalHeaderLabels(["Номер", "Стол", "Время", "Состав заказа", "Статус"])
        self.kitchen_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kitchen_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.kitchen_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.kitchen_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.kitchen_table.verticalHeader().setDefaultSectionSize(50)
        self.kitchen_table.itemSelectionChanged.connect(self.update_kitchen_actions)
        layout.addWidget(self.kitchen_table, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.next_status_button = QPushButton("Следующий статус")
        apply_button_variant(self.next_status_button, "warning")
        self.next_status_button.clicked.connect(self.advance_status)
        buttons.addWidget(self.next_status_button)

        self.close_order_button = QPushButton("Закрыть заказ")
        apply_button_variant(self.close_order_button, "danger")
        self.close_order_button.clicked.connect(self.complete_order)
        buttons.addWidget(self.close_order_button)

        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.tabs.addTab(page, "Заказы")
        self.tabs.setTabToolTip(2, "Просмотр заказов и закрытие выданных")

    def refresh_selectors(self) -> None:
        self._sync_combo(self.category_combo, self.store.categories(), "Нет блюд в базе")
        self._sync_combo(self.table_combo, [table["code"] for table in self.store.tables], "Нет столов")

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
            for column_index, value in enumerate([dish["name"], f"{dish['price']} \u20bd", dish["ready"]]):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.menu_table.setItem(row_index, column_index, item)
        if dishes:
            self.menu_table.selectRow(0)
            self.menu_hint.setText("Выбери блюдо и нажми «Добавить в заказ».")
        else:
            self.menu_hint.setText("Нет блюд в выбранной категории.")
        self.add_button.setEnabled(bool(dishes) and can_create_orders(self._current_role()))

    def populate_draft(self) -> None:
        self.draft_table.setRowCount(len(self.store.order_draft))
        for row_index, item_data in enumerate(self.store.order_draft):
            values = [item_data["name"], str(item_data["qty"]), f"{item_data['price']} \u20bd", f"{item_data['sum']} \u20bd", item_data.get("note", "")]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.draft_table.setItem(row_index, column_index, item)

        self.total_pill.set_state(f"\u0418того: {self.store.get_draft_total()} \u20bd", "info")
        has_draft = bool(self.store.order_draft)
        has_tables = bool(self.store.tables)
        self.remove_button.setEnabled(has_draft)
        self.clear_button.setEnabled(has_draft)
        self.note_button.setEnabled(has_draft)
        self.send_button.setEnabled(has_draft and has_tables and can_create_orders(self._current_role()))
        if not has_tables:
            self.order_hint.setText("Нет столов. Заказ нельзя передать на кухню.")
        elif not has_draft:
            self.order_hint.setText("Добавь блюда из вкладки «Меню».")
        else:
            self.order_hint.setText("Заказ готов к передаче на кухню.")

    def populate_kitchen(self) -> None:
        role = self._current_role()
        is_kitchen = can_process_kitchen(role)

        self.visible_queue_indices = self._filtered_queue_indices()
        self.kitchen_table.setRowCount(len(self.visible_queue_indices))
        for row_index, queue_index in enumerate(self.visible_queue_indices):
            queue_item = self.store.kitchen_queue[queue_index]
            values = [
                queue_item["order_no"],
                queue_item["table"],
                queue_item.get("created", "-"),
                queue_item["items"],
                queue_item["status"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(str(value))
                if column_index == 4:
                    tone = {"Готов": "success", "Готовится": "info", "Выдан": "muted"}.get(value, "warning")
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
        qty = self.qty_spin.value()
        for _ in range(qty):
            self.store.add_dish_to_draft(dish_item.text())
        self.qty_spin.setValue(1)
        self.populate_draft()
        self.status_message.emit(f"Добавлено: {dish_item.text()} x{qty}")

    def remove_selected_dish(self) -> None:
        row = self.draft_table.currentRow()
        if row < 0 or row >= len(self.store.order_draft):
            self.status_message.emit("Выбери позицию в черновике.")
            return
        self.store.order_draft.pop(row)
        self.populate_draft()
        self.status_message.emit("Позиция удалена.")

    def clear_order(self) -> None:
        self.store.clear_draft()
        self.populate_draft()
        self.status_message.emit("Черновик очищен.")

    def set_note_for_selected(self) -> None:
        row = self.draft_table.currentRow()
        if row < 0 or row >= len(self.store.order_draft):
            self.status_message.emit("Выбери позицию для примечания.")
            return
        note = self.note_input.text().strip()
        if hasattr(self.store, "set_draft_item_note"):
            self.store.set_draft_item_note(row, note)
        else:
            self.store.order_draft[row]["note"] = note
        self.note_input.clear()
        self.populate_draft()
        self.status_message.emit("Примечание добавлено.")

    def send_to_kitchen(self) -> None:
        if not can_create_orders(self._current_role()):
            self.status_message.emit("Нет прав на создание заказов.")
            return
        if not self.store.tables:
            self.status_message.emit("Нет столов в базе.")
            return
        success, message = self.store.send_draft_to_kitchen(self.table_combo.currentText(), self.payment_combo.currentText())
        self.populate_draft()
        self.populate_kitchen()
        self.status_message.emit(message)
        if success:
            self.total_pill.set_state("\u0418того: 0 \u20bd", "info")
            self.tabs.setCurrentIndex(2)

    def advance_status(self) -> None:
        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.status_message.emit("Выбери заказ.")
            return
        if can_process_kitchen(self._current_role()) and hasattr(self.store, "advance_kitchen_order"):
            message = self.store.advance_kitchen_order(queue_index)
        else:
            message = self.store.advance_order_status(queue_index)
        self.populate_kitchen()
        self.status_message.emit(message)

    def complete_order(self) -> None:
        if not can_close_orders(self._current_role()):
            self.status_message.emit("Нет прав на закрытие заказа.")
            return
        queue_index = self._selected_queue_index()
        if queue_index < 0:
            self.status_message.emit("Выбери заказ.")
            return
        message = self.store.complete_order(queue_index)
        self.populate_kitchen()
        self.status_message.emit(message)

    def refresh_kitchen_queue(self) -> None:
        if hasattr(self.store, "reload_from_mysql"):
            self.store.reload_from_mysql()
        self.populate_kitchen()
        self.status_message.emit("Очередь обновлена.")

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

        self.tabs.setTabVisible(0, can_create)
        self.tabs.setTabVisible(1, can_create)
        self.tabs.setTabVisible(2, True)
        self.next_status_button.setVisible(is_kitchen)
        self.close_order_button.setVisible(can_close)

        if is_kitchen:
            self.next_status_button.setText("Взять в работу")

    def update_kitchen_summary(self) -> None:
        counts = {
            status: len([item for item in self.store.kitchen_queue if item["status"] == status])
            for status in KITCHEN_ACTIVE_STATUSES
        }
        self.summary_pills["accepted"].set_state(f"\u041fринято: {counts['Принят']}", "warning")
        self.summary_pills["preparing"].set_state(f"\u0412 работе: {counts['Готовится']}", "info")
        self.summary_pills["ready"].set_state(f"\u0413отово: {counts['Готов']}", "success")

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
