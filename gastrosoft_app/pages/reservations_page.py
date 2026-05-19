from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ..style_utils import load_style
from ..widgets import MetricCard, SectionCard, apply_button_variant, tint_table_item


RESERVATION_STATUSES = [
    "Ожидается",
    "Подтверждена",
    "Гость в зале",
    "Завершена",
    "Отменена",
    "Не пришел",
]

ACTIVE_STATUSES = {"Ожидается", "Подтверждена", "Гость в зале"}


class ReservationsPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.summary_cards: dict[str, MetricCard] = {}
        self.table_buttons: dict[str, QPushButton] = {}
        self.setObjectName("reservationsPage")
        self.setStyleSheet(load_style("styles", "reservations", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, title, note in [
            ("active", "Активные брони", "Ожидаются, подтверждены или гости уже в зале"),
            ("tables", "Столы в зале", "Доступность пересчитывается по броням"),
            ("today", "Брони в списке", "Последние записи из MySQL"),
        ]:
            card = MetricCard(title, "0", note)
            self.summary_cards[key] = card
            summary_row.addWidget(card)
        root_layout.addLayout(summary_row)

        top_row = QHBoxLayout()
        top_row.setSpacing(18)

        form_card = SectionCard("Форма брони", "Создание новой брони и изменение статуса выбранной записи.")
        form_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.guest_input = QLineEdit()
        self.guest_input.setPlaceholderText("Фамилия Имя")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7...")

        self.table_combo = QComboBox()

        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.date_time_edit.setCalendarPopup(True)
        self.date_time_edit.setDisplayFormat("dd.MM.yyyy HH:mm")

        self.guests_spin = QSpinBox()
        self.guests_spin.setRange(1, 30)
        self.guests_spin.setValue(2)

        self.status_combo = QComboBox()
        self.status_combo.addItems(RESERVATION_STATUSES)

        form_layout.addRow("Гость", self.guest_input)
        form_layout.addRow("Телефон", self.phone_input)
        form_layout.addRow("Стол", self.table_combo)
        form_layout.addRow("Дата и время", self.date_time_edit)
        form_layout.addRow("Гостей", self.guests_spin)
        form_layout.addRow("Статус", self.status_combo)
        form_card.content_layout.addLayout(form_layout)

        create_row = QHBoxLayout()
        self.add_button = QPushButton("Добавить бронь")
        apply_button_variant(self.add_button, "primary")
        self.add_button.clicked.connect(self.add_reservation)
        create_row.addWidget(self.add_button)

        self.clear_button = QPushButton("Очистить")
        apply_button_variant(self.clear_button, "secondary")
        self.clear_button.clicked.connect(self.clear_form)
        create_row.addWidget(self.clear_button)
        form_card.content_layout.addLayout(create_row)

        status_row = QHBoxLayout()
        self.confirm_button = QPushButton("Подтвердить")
        apply_button_variant(self.confirm_button, "secondary")
        self.confirm_button.clicked.connect(lambda: self.change_selected_status("Подтверждена"))
        status_row.addWidget(self.confirm_button)

        self.seat_button = QPushButton("Гость в зале")
        apply_button_variant(self.seat_button, "primary")
        self.seat_button.clicked.connect(lambda: self.change_selected_status("Гость в зале"))
        status_row.addWidget(self.seat_button)

        self.cancel_button = QPushButton("Отменить")
        apply_button_variant(self.cancel_button, "danger")
        self.cancel_button.clicked.connect(lambda: self.change_selected_status("Отменена"))
        status_row.addWidget(self.cancel_button)
        form_card.content_layout.addLayout(status_row)
        top_row.addWidget(form_card, 5)

        map_card = SectionCard("Занятость столов", "Свободные столы можно выбрать одним нажатием.")
        self.table_hint = QLabel()
        self.table_hint.setObjectName("sectionCardSubtitle")
        self.table_hint.setWordWrap(True)
        map_card.content_layout.addWidget(self.table_hint)

        self.table_grid = QGridLayout()
        self.table_grid.setSpacing(12)
        map_card.content_layout.addLayout(self.table_grid)
        top_row.addWidget(map_card, 5)

        root_layout.addLayout(top_row)

        list_card = SectionCard("Список бронирований", "Выбери строку, чтобы заполнить форму и изменить статус.")
        self.reservation_table = QTableWidget(0, 6)
        self.reservation_table.setHorizontalHeaderLabels(["Гость", "Телефон", "Стол", "Время", "Гостей", "Статус"])
        self.reservation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reservation_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.reservation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reservation_table.itemSelectionChanged.connect(self.sync_form_from_selection)
        self.reservation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_card.content_layout.addWidget(self.reservation_table)
        root_layout.addWidget(list_card, 1)

    def refresh_selectors(self) -> None:
        self._sync_combo(
            self.table_combo,
            [table["code"] for table in self.store.tables],
            "Нет активных столов",
        )
        self._rebuild_table_buttons()

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

    def _rebuild_table_buttons(self) -> None:
        while self.table_grid.count():
            item = self.table_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.table_buttons.clear()
        for index, table in enumerate(self.store.tables):
            code = str(table["code"])
            seats = table.get("seats", "-")
            button = QPushButton(f"{code}\n{seats} мест")
            button.setObjectName("tableButton")
            button.clicked.connect(lambda checked=False, table_code=code: self.select_table(table_code))
            self.table_buttons[code] = button
            self.table_grid.addWidget(button, index // 3, index % 3)

    def select_table(self, code: str) -> None:
        self.table_combo.setCurrentText(code)
        self.status_message.emit(f"Для новой брони выбран стол {code}.")

    def populate_reservations(self) -> None:
        selected_id = self._selected_reservation_id()
        self.reservation_table.blockSignals(True)
        self.reservation_table.setRowCount(len(self.store.reservations))

        selected_row = 0 if self.store.reservations else -1
        for row_index, reservation in enumerate(self.store.reservations):
            if selected_id is not None and reservation.get("reservation_id") == selected_id:
                selected_row = row_index

            values = [
                reservation.get("guest", ""),
                reservation.get("phone", ""),
                reservation.get("table", "-"),
                reservation.get("time", "-"),
                str(reservation.get("guests", "")),
                reservation.get("status", ""),
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(value)
                if column_index == 5:
                    tint_table_item(item, self._status_tone(value))
                self.reservation_table.setItem(row_index, column_index, item)

        self.reservation_table.blockSignals(False)
        if selected_row >= 0:
            self.reservation_table.selectRow(selected_row)
        else:
            self.clear_form(keep_datetime=True)
        self.update_actions()

    def refresh_table_map(self) -> None:
        self.store.recalculate_tables()
        free_count = 0
        for table in self.store.tables:
            code = str(table["code"])
            occupied = bool(table.get("occupied", False))
            if not occupied:
                free_count += 1
            button = self.table_buttons.get(code)
            if button is None:
                continue
            button.setProperty("state", "busy" if occupied else "free")
            button.setToolTip("Занят" if occupied else "Свободен")
            button.style().unpolish(button)
            button.style().polish(button)

        if self.store.tables:
            self.table_hint.setText(f"Свободно: {free_count} из {len(self.store.tables)}.")
        else:
            self.table_hint.setText("В базе нет активных столов. Добавление брони временно недоступно.")

    def refresh_summary(self) -> None:
        active_count = len([item for item in self.store.reservations if item.get("status") in ACTIVE_STATUSES])
        free_tables = len([table for table in self.store.tables if not table.get("occupied", False)])
        total_tables = len(self.store.tables)
        self.summary_cards["active"].set_value(str(active_count), "Не отменены и не завершены")
        self.summary_cards["tables"].set_value(f"{free_tables}/{total_tables}", "Свободно из общего числа столов")
        self.summary_cards["today"].set_value(str(len(self.store.reservations)), "Загружено в таблицу бронирований")

    def selected_reservation_index(self) -> int:
        return self.reservation_table.currentRow()

    def _selected_reservation_id(self) -> int | None:
        row = self.selected_reservation_index()
        if row < 0 or row >= len(self.store.reservations):
            return None
        reservation_id = self.store.reservations[row].get("reservation_id")
        return int(reservation_id) if reservation_id is not None else None

    def sync_form_from_selection(self) -> None:
        row = self.selected_reservation_index()
        if row < 0 or row >= len(self.store.reservations):
            self.update_actions()
            return

        reservation = self.store.reservations[row]
        self.guest_input.setText(str(reservation.get("guest", "")))
        self.phone_input.setText(str(reservation.get("phone", "")))
        self.table_combo.setCurrentText(str(reservation.get("table", "")))
        self.guests_spin.setValue(int(reservation.get("guests", 1) or 1))

        status = str(reservation.get("status", "Ожидается"))
        if status in RESERVATION_STATUSES:
            self.status_combo.setCurrentText(status)
        self.update_actions()

    def clear_form(self, keep_datetime: bool = False) -> None:
        self.guest_input.clear()
        self.phone_input.clear()
        self.guests_spin.setValue(2)
        self.status_combo.setCurrentText("Ожидается")
        if not keep_datetime:
            self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        if self.table_combo.isEnabled() and self.table_combo.count() > 0:
            self.table_combo.setCurrentIndex(0)
        self.reservation_table.clearSelection()
        self.update_actions()

    def add_reservation(self) -> None:
        guest = self.guest_input.text().strip()
        phone = self.phone_input.text().strip()
        table = self.table_combo.currentText().strip()

        if not guest or not phone:
            self.status_message.emit("Для брони нужно заполнить имя гостя и телефон.")
            return
        if not self.table_combo.isEnabled() or not table or table == "Нет активных столов":
            self.status_message.emit("Для брони нужен активный стол из базы данных.")
            return

        created = self.store.add_reservation(
            guest,
            phone,
            table,
            self.date_time_edit.dateTime().toPython(),
            self.guests_spin.value(),
            self.status_combo.currentText(),
        )
        self.refresh_page()

        if created:
            self.status_message.emit(f"Бронь для гостя {guest} добавлена.")
            self.clear_form()
            return

        message = getattr(self.store, "last_error", "") or "Бронь не сохранена. Проверь подключение к MySQL."
        self.status_message.emit(message)

    def change_selected_status(self, status: str) -> None:
        if self.selected_reservation_index() < 0:
            self.status_message.emit("Выбери бронь в таблице, чтобы изменить статус.")
            return

        message = self.store.set_reservation_status(self.selected_reservation_index(), status)
        self.refresh_page()
        self.status_message.emit(message)

    def update_actions(self) -> None:
        has_tables = bool(self.store.tables)
        has_selection = self.selected_reservation_index() >= 0
        self.add_button.setEnabled(has_tables and self.table_combo.isEnabled())
        self.confirm_button.setEnabled(has_selection)
        self.seat_button.setEnabled(has_selection)
        self.cancel_button.setEnabled(has_selection)

    def refresh_page(self) -> None:
        if hasattr(self.store, "reload_from_mysql") and getattr(self.store, "mysql_enabled", False):
            self.store.reload_from_mysql()
        self.refresh_selectors()
        self.populate_reservations()
        self.refresh_table_map()
        self.refresh_summary()
        self.update_actions()

    def _status_tone(self, status: str) -> str:
        if status == "Подтверждена":
            return "success"
        if status == "Гость в зале":
            return "info"
        if status in {"Отменена", "Не пришел"}:
            return "danger"
        if status == "Завершена":
            return "muted"
        return "warning"
