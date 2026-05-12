from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
from ..widgets import MetricCard, SectionCard, apply_button_variant, tint_table_item


class StaffPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.setObjectName("staffPage")
        self.setStyleSheet(load_style("styles", "staff", "style.css"))
        self.summary_cards: dict[str, MetricCard] = {}
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        controls_card = SectionCard("Планирование смен", "Отдельный экран для руководителя зала и кухни.")
        controls_row = QHBoxLayout()

        self.role_filter = QComboBox()
        self.role_filter.addItems(["Все роли"] + self.store.role_options)
        self.role_filter.currentTextChanged.connect(self.populate_employees)
        controls_row.addWidget(self.role_filter)

        self.shift_combo = QComboBox()
        self.shift_combo.addItems(["Утро 08:00-14:00", "День 12:00-18:00", "Вечер 17:00-23:00"])
        controls_row.addWidget(self.shift_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        controls_row.addWidget(self.date_edit)

        assign_button = QPushButton("Назначить")
        apply_button_variant(assign_button, "primary")
        assign_button.clicked.connect(self.assign_shift)
        controls_row.addWidget(assign_button)

        swap_button = QPushButton("Подобрать замену")
        apply_button_variant(swap_button, "warning")
        swap_button.clicked.connect(self.swap_shift)
        controls_row.addWidget(swap_button)

        close_button = QPushButton("Закрыть смену")
        apply_button_variant(close_button, "ghost")
        close_button.clicked.connect(self.close_shift)
        controls_row.addWidget(close_button)

        controls_card.content_layout.addLayout(controls_row)
        root_layout.addWidget(controls_card)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, title, note in [
            ("employees", "Сотрудников в системе", "Включая управленческие роли"),
            ("assignments", "Назначений на смены", "План, подтверждение и закрытие"),
            ("free", "Доступны к замене", "Свободные сотрудники на текущий день"),
        ]:
            card = MetricCard(title, "0", note)
            self.summary_cards[key] = card
            summary_row.addWidget(card)
        root_layout.addLayout(summary_row)

        tables_row = QHBoxLayout()
        tables_row.setSpacing(18)

        employees_card = SectionCard("Сотрудники", "Выбери сотрудника и назначь его на смену.")
        self.employee_table = QTableWidget(0, 4)
        self.employee_table.setHorizontalHeaderLabels(["Сотрудник", "Роль", "Навык", "Статус"])
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        employees_card.content_layout.addWidget(self.employee_table)
        tables_row.addWidget(employees_card, 6)

        assignments_card = SectionCard("Текущие назначения", "Из этой таблицы можно запускать замену и закрытие смен.")
        self.assignment_table = QTableWidget(0, 5)
        self.assignment_table.setHorizontalHeaderLabels(["Дата", "Смена", "Сотрудник", "Роль", "Статус"])
        self.assignment_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.assignment_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.assignment_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.assignment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        assignments_card.content_layout.addWidget(self.assignment_table)

        self.assignment_hint = QLabel("Рабочие кнопки: назначение, подбор замены, закрытие смены.")
        self.assignment_hint.setObjectName("staffHint")
        self.assignment_hint.setWordWrap(True)
        assignments_card.content_layout.addWidget(self.assignment_hint)
        tables_row.addWidget(assignments_card, 7)

        root_layout.addLayout(tables_row, 1)

    def populate_employees(self) -> None:
        role_filter = self.role_filter.currentText()
        rows = [
            employee for employee in self.store.employees if role_filter == "Все роли" or employee["role"] == role_filter
        ]

        self.employee_table.setRowCount(len(rows))
        for row_index, employee in enumerate(rows):
            for column_index, key in enumerate(["name", "role", "skill", "status"]):
                item = QTableWidgetItem(str(employee[key]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if key == "status":
                    tone = "success" if employee[key] in {"Свободен", "В офисе"} else "warning"
                    if employee[key] == "На смене":
                        tone = "info"
                    tint_table_item(item, tone)
                self.employee_table.setItem(row_index, column_index, item)

        if rows:
            self.employee_table.selectRow(0)

    def populate_assignments(self) -> None:
        self.assignment_table.setRowCount(len(self.store.assignments))
        for row_index, assignment in enumerate(self.store.assignments):
            for column_index, key in enumerate(["date", "shift", "employee", "role", "status"]):
                item = QTableWidgetItem(str(assignment[key]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if key == "status":
                    tone = "warning"
                    if assignment[key] == "Подтверждена":
                        tone = "success"
                    elif assignment[key] == "Закрыта":
                        tone = "muted"
                    elif assignment[key] == "Замена согласована":
                        tone = "info"
                    tint_table_item(item, tone)
                self.assignment_table.setItem(row_index, column_index, item)

        if self.store.assignments:
            self.assignment_table.selectRow(len(self.store.assignments) - 1)

    def refresh_summary(self) -> None:
        free_count = len([item for item in self.store.employees if item["status"] in {"Свободен", "В офисе"}])
        self.summary_cards["employees"].set_value(str(len(self.store.employees)), "Роли загружены из предметной области")
        self.summary_cards["assignments"].set_value(str(len(self.store.assignments)), "План и фактические назначения")
        self.summary_cards["free"].set_value(str(free_count), "Сотрудники, которых можно подменить")

    def selected_employee_name(self) -> str | None:
        selected_row = self.employee_table.currentRow()
        if selected_row < 0:
            return None
        item = self.employee_table.item(selected_row, 0)
        return item.text() if item else None

    def selected_assignment_index(self) -> int:
        return self.assignment_table.currentRow()

    def assign_shift(self) -> None:
        employee_name = self.selected_employee_name()
        if not employee_name:
            self.status_message.emit("Выбери сотрудника для назначения на смену.")
            return

        date_text = self.date_edit.date().toString("dd.MM.yyyy")
        assignment = self.store.add_assignment(employee_name, self.shift_combo.currentText(), date_text)
        if assignment is None:
            self.status_message.emit("Не удалось назначить сотрудника.")
            return

        self.populate_employees()
        self.populate_assignments()
        self.refresh_summary()
        self.status_message.emit(f"Смена назначена: {employee_name}, {assignment['shift']}.")

    def swap_shift(self) -> None:
        message = self.store.swap_assignment(self.selected_assignment_index())
        self.populate_employees()
        self.populate_assignments()
        self.refresh_summary()
        self.status_message.emit(message)

    def close_shift(self) -> None:
        message = self.store.close_assignment(self.selected_assignment_index())
        self.populate_assignments()
        self.refresh_summary()
        self.status_message.emit(message)

    def refresh_page(self) -> None:
        self.populate_employees()
        self.populate_assignments()
        self.refresh_summary()
