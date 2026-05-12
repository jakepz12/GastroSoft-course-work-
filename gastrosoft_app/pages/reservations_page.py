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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ..style_utils import load_style
from ..widgets import SectionCard, apply_button_variant, tint_table_item


class ReservationsPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.table_buttons: dict[str, QPushButton] = {}
        self.setObjectName("reservationsPage")
        self.setStyleSheet(load_style("styles", "reservations", "style.css"))
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        left_column = QVBoxLayout()
        left_column.setSpacing(18)

        form_card = SectionCard("Форма брони", "Добавление, подтверждение и отмена работают отдельными кнопками.")
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.guest_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.table_combo = QComboBox()
        self.table_combo.addItems([table["code"] for table in self.store.tables])
        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.date_time_edit.setCalendarPopup(True)
        self.guests_spin = QSpinBox()
        self.guests_spin.setRange(1, 12)
        self.guests_spin.setValue(2)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Ожидается", "Подтверждена", "Гость в зале", "Отменена"])

        form_layout.addRow("Гость", self.guest_input)
        form_layout.addRow("Телефон", self.phone_input)
        form_layout.addRow("Стол", self.table_combo)
        form_layout.addRow("Дата и время", self.date_time_edit)
        form_layout.addRow("Гостей", self.guests_spin)
        form_layout.addRow("Статус", self.status_combo)
        form_card.content_layout.addLayout(form_layout)

        button_row = QHBoxLayout()
        add_button = QPushButton("Добавить бронь")
        apply_button_variant(add_button, "primary")
        add_button.clicked.connect(self.add_reservation)
        button_row.addWidget(add_button)

        confirm_button = QPushButton("Подтвердить")
        apply_button_variant(confirm_button, "secondary")
        confirm_button.clicked.connect(lambda: self.change_selected_status("Подтверждена"))
        button_row.addWidget(confirm_button)

        cancel_button = QPushButton("Отменить")
        apply_button_variant(cancel_button, "danger")
        cancel_button.clicked.connect(lambda: self.change_selected_status("Отменена"))
        button_row.addWidget(cancel_button)
        form_card.content_layout.addLayout(button_row)
        left_column.addWidget(form_card)

        map_card = SectionCard("Занятость столов", "У каждой кнопки свое состояние: свободен или занят.")
        grid = QGridLayout()
        grid.setSpacing(12)
        for index, table in enumerate(self.store.tables):
            button = QPushButton(f"{table['code']}\n{table['seats']} мест")
            button.setObjectName("tableButton")
            button.clicked.connect(lambda checked=False, code=table["code"]: self.select_table(code))
            self.table_buttons[table["code"]] = button
            grid.addWidget(button, index // 2, index % 2)
        map_card.content_layout.addLayout(grid)
        left_column.addWidget(map_card)

        root_layout.addLayout(left_column, 5)

        list_card = SectionCard("Список бронирований", "Выбери строку в таблице, чтобы менять её статус.")
        self.reservation_table = QTableWidget(0, 6)
        self.reservation_table.setHorizontalHeaderLabels(["Гость", "Телефон", "Стол", "Время", "Гостей", "Статус"])
        self.reservation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reservation_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.reservation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reservation_table.itemSelectionChanged.connect(self.sync_form_from_selection)
        self.reservation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_card.content_layout.addWidget(self.reservation_table)
        root_layout.addWidget(list_card, 7)

    def select_table(self, code: str) -> None:
        self.table_combo.setCurrentText(code)
        self.status_message.emit(f"Для новой брони выбран стол {code}.")

    def populate_reservations(self) -> None:
        self.reservation_table.setRowCount(len(self.store.reservations))
        for row_index, reservation in enumerate(self.store.reservations):
            values = [
                reservation["guest"],
                reservation["phone"],
                reservation["table"],
                reservation["time"],
                str(reservation["guests"]),
                reservation["status"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column_index == 5:
                    tone = "warning"
                    if value == "Подтверждена":
                        tone = "success"
                    elif value == "Гость в зале":
                        tone = "info"
                    elif value == "Отменена":
                        tone = "danger"
                    tint_table_item(item, tone)
                self.reservation_table.setItem(row_index, column_index, item)
        if self.store.reservations:
            self.reservation_table.selectRow(0)

    def refresh_table_map(self) -> None:
        self.store.recalculate_tables()
        for table in self.store.tables:
            button = self.table_buttons[table["code"]]
            button.setProperty("state", "busy" if table["occupied"] else "free")
            button.style().unpolish(button)
            button.style().polish(button)

    def selected_reservation_index(self) -> int:
        return self.reservation_table.currentRow()

    def sync_form_from_selection(self) -> None:
        row = self.selected_reservation_index()
        if row < 0 or row >= len(self.store.reservations):
            return
        reservation = self.store.reservations[row]
        self.guest_input.setText(reservation["guest"])
        self.phone_input.setText(reservation["phone"])
        self.table_combo.setCurrentText(reservation["table"])
        self.guests_spin.setValue(int(reservation["guests"]))
        self.status_combo.setCurrentText(reservation["status"])

    def add_reservation(self) -> None:
        guest = self.guest_input.text().strip()
        phone = self.phone_input.text().strip()
        if not guest or not phone:
            self.status_message.emit("Для брони нужно заполнить имя гостя и телефон.")
            return

        self.store.add_reservation(
            guest,
            phone,
            self.table_combo.currentText(),
            self.date_time_edit.dateTime().toPython(),
            self.guests_spin.value(),
            self.status_combo.currentText(),
        )
        self.refresh_page()
        self.status_message.emit(f"Бронь для гостя {guest} добавлена.")

    def change_selected_status(self, status: str) -> None:
        message = self.store.set_reservation_status(self.selected_reservation_index(), status)
        self.refresh_page()
        self.status_message.emit(message)

    def refresh_page(self) -> None:
        self.populate_reservations()
        self.refresh_table_map()
