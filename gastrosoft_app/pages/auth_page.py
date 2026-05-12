from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from ..style_utils import load_style
from ..widgets import apply_button_variant, StatusPill


class AuthPage(QWidget):
    authenticated = Signal(dict)
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.setObjectName("authPage")
        self.setStyleSheet(load_style("styles", "auth", "style.css"))
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(22)

        hero_panel = QFrame()
        hero_panel.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero_panel)
        hero_layout.setContentsMargins(36, 36, 36, 36)
        hero_layout.setSpacing(18)

        hero_title = QLabel("GastroSoft")
        hero_title.setObjectName("heroTitle")
        hero_layout.addWidget(hero_title)

        hero_text = QLabel(
            "Desktop-прототип для автоматизации зала, кухни, смен, бронирований и складских операций ресторана."
        )
        hero_text.setObjectName("heroText")
        hero_text.setWordWrap(True)
        hero_layout.addWidget(hero_text)

        for text, tone in [
            ("Официанты и кассиры работают с заказами без перегруженных экранов.", "info"),
            ("Шеф-повар и кухня видят статусы приготовления в одном окне.", "success"),
            ("Директор и бухгалтер получают сводку по выручке и остаткам.", "warning"),
        ]:
            pill = StatusPill(text, tone)
            pill.setMinimumHeight(40)
            hero_layout.addWidget(pill)

        hero_layout.addStretch(1)

        demo_hint = QLabel("Пользователи и роли загружаются из MySQL. Если вход не работает, проверь mysql_config.json и примененную схему.")
        demo_hint.setObjectName("heroHint")
        demo_hint.setTextFormat(Qt.TextFormat.PlainText)
        hero_layout.addWidget(demo_hint)

        root_layout.addWidget(hero_panel, 6)

        auth_card = QFrame()
        auth_card.setObjectName("authCard")
        auth_layout = QVBoxLayout(auth_card)
        auth_layout.setContentsMargins(28, 28, 28, 28)
        auth_layout.setSpacing(16)

        title = QLabel("Вход и регистрация")
        title.setObjectName("authTitle")
        auth_layout.addWidget(title)

        subtitle = QLabel("Каждый режим оформлен отдельно, но работает в одном desktop-приложении.")
        subtitle.setObjectName("authSubtitle")
        subtitle.setWordWrap(True)
        auth_layout.addWidget(subtitle)

        switch_layout = QHBoxLayout()
        switch_layout.setSpacing(12)
        self.login_mode_button = QPushButton("Вход")
        self.login_mode_button.clicked.connect(lambda: self.switch_mode(0))
        apply_button_variant(self.login_mode_button, "primary")
        switch_layout.addWidget(self.login_mode_button)

        self.register_mode_button = QPushButton("Регистрация")
        self.register_mode_button.clicked.connect(lambda: self.switch_mode(1))
        apply_button_variant(self.register_mode_button, "secondary")
        switch_layout.addWidget(self.register_mode_button)
        auth_layout.addLayout(switch_layout)

        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(self._build_login_form())
        self.mode_stack.addWidget(self._build_register_form())
        auth_layout.addWidget(self.mode_stack, 1)

        root_layout.addWidget(auth_card, 5)

    def _build_login_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.login_field = QLineEdit()
        self.login_field.setPlaceholderText("Например: director")
        self._add_labeled_field(layout, "Логин", self.login_field)

        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("Введи пароль")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._add_labeled_field(layout, "Пароль", self.password_field)

        login_button = QPushButton("Войти в систему")
        apply_button_variant(login_button, "primary")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        self.auth_feedback = QLabel("Введи логин и пароль пользователя из базы данных.")
        self.auth_feedback.setObjectName("formHint")
        self.auth_feedback.setWordWrap(True)
        layout.addWidget(self.auth_feedback)
        layout.addStretch(1)
        return page

    def _build_register_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.register_name_field = QLineEdit()
        self.register_name_field.setPlaceholderText("Фамилия Имя Отчество")
        self._add_labeled_field(layout, "ФИО сотрудника", self.register_name_field)

        self.register_login_field = QLineEdit()
        self.register_login_field.setPlaceholderText("Например: manager_hall")
        self._add_labeled_field(layout, "Логин", self.register_login_field)

        self.register_password_field = QLineEdit()
        self.register_password_field.setPlaceholderText("Придумай пароль")
        self.register_password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._add_labeled_field(layout, "Пароль", self.register_password_field)

        self.register_repeat_field = QLineEdit()
        self.register_repeat_field.setPlaceholderText("Повтори пароль еще раз")
        self.register_repeat_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._add_labeled_field(layout, "Подтверждение пароля", self.register_repeat_field)

        self.role_combo = QComboBox()
        self.role_combo.addItems(self.store.role_options)
        self._add_labeled_field(layout, "Роль пользователя", self.role_combo)

        button_row = QHBoxLayout()
        register_button = QPushButton("Создать аккаунт")
        apply_button_variant(register_button, "primary")
        register_button.clicked.connect(self.handle_register)
        button_row.addWidget(register_button)

        clear_button = QPushButton("Очистить")
        apply_button_variant(clear_button, "secondary")
        clear_button.clicked.connect(self.clear_register_form)
        button_row.addWidget(clear_button)
        layout.addLayout(button_row)

        self.register_feedback = QLabel("После регистрации будет выполнен автоматический вход в приложение.")
        self.register_feedback.setObjectName("formHint")
        self.register_feedback.setWordWrap(True)
        layout.addWidget(self.register_feedback)
        layout.addStretch(1)
        return page

    def _add_labeled_field(self, layout: QVBoxLayout, label_text: str, widget: QWidget) -> None:
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(widget)

    def switch_mode(self, index: int) -> None:
        self.mode_stack.setCurrentIndex(index)
        apply_button_variant(self.login_mode_button, "primary" if index == 0 else "secondary")
        apply_button_variant(self.register_mode_button, "primary" if index == 1 else "secondary")

    def handle_login(self) -> None:
        login = self.login_field.text().strip()
        password = self.password_field.text().strip()
        if not login or not password:
            self.auth_feedback.setText("Заполни логин и пароль.")
            self.status_message.emit("Не удалось войти: не заполнены поля.")
            return

        user = self.store.authenticate(login, password)
        if user is None:
            self.auth_feedback.setText("Неверный логин или пароль.")
            self.status_message.emit("Ошибка авторизации.")
            return

        self.auth_feedback.setText("Авторизация выполнена успешно.")
        self.authenticated.emit(user)

    def handle_register(self) -> None:
        full_name = self.register_name_field.text().strip()
        login = self.register_login_field.text().strip()
        password = self.register_password_field.text().strip()
        password_repeat = self.register_repeat_field.text().strip()
        role = self.role_combo.currentText()

        if not all([full_name, login, password, password_repeat]):
            self.register_feedback.setText("Заполни все поля регистрации.")
            self.status_message.emit("Регистрация не завершена.")
            return

        if password != password_repeat:
            self.register_feedback.setText("Пароли не совпадают.")
            self.status_message.emit("Пароли в регистрации не совпадают.")
            return

        success, message, user = self.store.register_user(full_name, login, password, role)
        self.register_feedback.setText(message)
        self.status_message.emit(message)
        if success and user:
            self.authenticated.emit(user)

    def clear_register_form(self) -> None:
        self.register_name_field.clear()
        self.register_login_field.clear()
        self.register_password_field.clear()
        self.register_repeat_field.clear()
        self.register_feedback.setText("Форма регистрации очищена.")
