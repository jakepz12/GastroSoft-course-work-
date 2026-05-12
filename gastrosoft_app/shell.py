from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .mysql_store import MySQLBackedStore
from .pages.auth_page import AuthPage
from .pages.dashboard_page import DashboardPage
from .pages.inventory_page import InventoryPage
from .pages.orders_page import OrdersPage
from .pages.reservations_page import ReservationsPage
from .pages.staff_page import StaffPage
from .style_utils import load_style
from .widgets import apply_button_variant


class GastroSoftWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project_root = Path(__file__).resolve().parent.parent
        self.store = MySQLBackedStore(self.project_root)
        self.page_widgets: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}

        self.page_meta = {
            "auth": ("Авторизация", "Вход в систему и создание учетной записи"),
            "dashboard": ("Главный экран", "Ключевые показатели и быстрый доступ к модулям"),
            "staff": ("Смены и персонал", "Планирование графиков и контроль сотрудников"),
            "reservations": ("Бронирования", "Работа со столами и посадкой гостей"),
            "orders": ("Заказы и кухня", "Оформление заказов и статусы приготовления"),
            "inventory": ("Склад и отчеты", "Остатки, операции и экспорт сводки"),
        }

        self.setWindowTitle("GastroSoft Desktop")
        self.resize(1580, 980)
        self._build_ui()
        self._create_pages()
        self.setStyleSheet(load_style("styles", "shell", "style.css"))
        self.navigate("auth")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("shellRoot")
        self.setCentralWidget(root)

        outer_layout = QHBoxLayout(root)
        outer_layout.setContentsMargins(22, 22, 22, 22)
        outer_layout.setSpacing(18)

        self.nav_panel = QFrame()
        self.nav_panel.setObjectName("navPanel")
        self.nav_panel.setFixedWidth(260)
        nav_layout = QVBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(20, 24, 20, 24)
        nav_layout.setSpacing(16)

        brand = QLabel("GastroSoft")
        brand.setObjectName("brandLabel")
        nav_layout.addWidget(brand)

        brand_sub = QLabel("Restaurant desktop prototype on Python / PySide6")
        brand_sub.setObjectName("brandSubLabel")
        brand_sub.setWordWrap(True)
        nav_layout.addWidget(brand_sub)

        nav_layout.addSpacing(8)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for page_key, button_title in [
            ("dashboard", "Главная панель"),
            ("staff", "Смены и персонал"),
            ("reservations", "Бронирования"),
            ("orders", "Заказы и кухня"),
            ("inventory", "Склад и отчеты"),
        ]:
            button = QPushButton(button_title)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, key=page_key: self.navigate(key))
            self.nav_group.addButton(button)
            self.nav_buttons[page_key] = button
            nav_layout.addWidget(button)

        nav_layout.addStretch(1)

        footer = QLabel(f"Источник данных:\n{self.store.mysql_status}")
        footer.setObjectName("brandSubLabel")
        footer.setWordWrap(True)
        nav_layout.addWidget(footer)

        outer_layout.addWidget(self.nav_panel)

        content_column = QVBoxLayout()
        content_column.setSpacing(18)

        self.header_card = QFrame()
        self.header_card.setObjectName("headerCard")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.setSpacing(16)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        title_block.addWidget(self.page_title)

        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("pageSubtitle")
        title_block.addWidget(self.page_subtitle)
        header_layout.addLayout(title_block, 1)

        self.user_card = QFrame()
        self.user_card.setObjectName("userBadge")
        user_layout = QVBoxLayout(self.user_card)
        user_layout.setContentsMargins(16, 12, 16, 12)
        user_layout.setSpacing(2)
        self.user_name = QLabel("Не авторизован")
        self.user_name.setObjectName("userNameLabel")
        user_layout.addWidget(self.user_name)
        self.user_role = QLabel("Гость")
        self.user_role.setObjectName("userRoleLabel")
        user_layout.addWidget(self.user_role)
        header_layout.addWidget(self.user_card)

        self.logout_button = QPushButton("Выйти")
        apply_button_variant(self.logout_button, "ghost")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)

        content_column.addWidget(self.header_card)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_column.addWidget(self.stack, 1)
        outer_layout.addLayout(content_column, 1)

    def _create_pages(self) -> None:
        auth_page = AuthPage(self.store)
        dashboard_page = DashboardPage(self.store)
        staff_page = StaffPage(self.store)
        reservations_page = ReservationsPage(self.store)
        orders_page = OrdersPage(self.store)
        inventory_page = InventoryPage(self.store, self.project_root)

        auth_page.authenticated.connect(self.on_authenticated)
        dashboard_page.navigate_requested.connect(self.navigate)

        for page in [auth_page, dashboard_page, staff_page, reservations_page, orders_page, inventory_page]:
            if hasattr(page, "status_message"):
                page.status_message.connect(self.show_status)

        self.page_widgets = {
            "auth": auth_page,
            "dashboard": dashboard_page,
            "staff": staff_page,
            "reservations": reservations_page,
            "orders": orders_page,
            "inventory": inventory_page,
        }

        for page in self.page_widgets.values():
            self.stack.addWidget(page)

    def on_authenticated(self, user: dict) -> None:
        self.store.current_user = user
        self.user_name.setText(user["full_name"])
        self.user_role.setText(user["role"])
        self.show_status(f"Выполнен вход: {user['full_name']} ({user['role']})")
        self.navigate("dashboard")

    def logout(self) -> None:
        self.store.current_user = None
        self.user_name.setText("Не авторизован")
        self.user_role.setText("Гость")
        self.navigate("auth")
        self.show_status("Сеанс завершен.")

    def navigate(self, page_key: str) -> None:
        widget = self.page_widgets[page_key]
        self.stack.setCurrentWidget(widget)

        title, subtitle = self.page_meta[page_key]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        is_auth = page_key == "auth"
        self.nav_panel.setVisible(not is_auth)
        self.header_card.setVisible(not is_auth)
        self.statusBar().setVisible(not is_auth)

        for key, button in self.nav_buttons.items():
            button.setChecked(key == page_key)

        if hasattr(widget, "refresh_page"):
            widget.refresh_page()

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 4500)
