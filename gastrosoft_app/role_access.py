KITCHEN_ROLES = {"Повар", "Шеф-повар"}
ORDER_CREATOR_ROLES = {"Официант", "Менеджер зала", "Администратор системы", "Директор"}
CASHIER_ROLES = {"Официант"}
ADMIN_ROLES = {"Администратор системы", "Директор"}
RESERVATION_ROLES = {"Менеджер зала", "Администратор системы", "Директор"}
INVENTORY_ROLES = {"Бухгалтер", "Администратор системы", "Директор"}
STAFF_ROLES = {"Администратор системы", "Директор"}
CHEF_ROLES = {"Шеф-повар"}


ROLE_ALLOWED_PAGES = {
    "Администратор системы": ["dashboard", "staff", "reservations", "orders", "inventory", "kitchen", "reports"],
    "Директор": ["dashboard", "staff", "reservations", "orders", "inventory", "kitchen", "reports"],
    "Менеджер зала": ["reservations", "orders"],
    "Официант": ["orders"],
    "Шеф-повар": ["kitchen", "orders", "reports"],
    "Повар": ["kitchen"],
    "Бухгалтер": ["inventory"],
}

ROLE_DEFAULT_PAGE = {
    "Администратор системы": "dashboard",
    "Директор": "dashboard",
    "Менеджер зала": "reservations",
    "Официант": "orders",
    "Шеф-повар": "kitchen",
    "Повар": "kitchen",
    "Бухгалтер": "inventory",
}


ROLE_PAGE_META = {
    ("Официант", "orders"): ("Оформление заказов", "Создание, контроль и закрытие заказов"),
    ("Менеджер зала", "orders"): ("Заказы зала", "Контроль оформления заказов и передачи на кухню"),
    ("Шеф-повар", "orders"): ("Просмотр заказов", "Просмотр заказов текущей смены"),
    ("Шеф-повар", "kitchen"): ("Кухонная панель", "Управление очередью кухни и распределение заказов"),
    ("Шеф-повар", "reports"): ("Отчёты кухни", "Статистика, история и текстовые отчёты"),
    ("Повар", "kitchen"): ("Кухонная очередь", "Приготовление заказов"),
    ("Бухгалтер", "inventory"): ("Склад и отчеты", "Складские операции и отчетность"),
}


def allowed_pages_for_role(role: str | None) -> list[str]:
    return ROLE_ALLOWED_PAGES.get(role or "", [])


def default_page_for_role(role: str | None) -> str:
    return ROLE_DEFAULT_PAGE.get(role or "", "auth")


def page_meta_for_role(role: str | None, page_key: str, fallback: tuple[str, str]) -> tuple[str, str]:
    return ROLE_PAGE_META.get((role or "", page_key), fallback)


def can_create_orders(role: str | None) -> bool:
    return role in ORDER_CREATOR_ROLES


def can_process_kitchen(role: str | None) -> bool:
    return role in KITCHEN_ROLES


def can_close_orders(role: str | None) -> bool:
    return role in CASHIER_ROLES or role in ADMIN_ROLES


def can_manage_inventory(role: str | None) -> bool:
    return role in INVENTORY_ROLES


def can_manage_reservations(role: str | None) -> bool:
    return role in RESERVATION_ROLES


def can_manage_staff(role: str | None) -> bool:
    return role in STAFF_ROLES


def can_manage_kitchen(role: str | None) -> bool:
    return role in KITCHEN_ROLES


def is_chef_role(role: str | None) -> bool:
    return role in CHEF_ROLES


def can_cancel_orders(role: str | None) -> bool:
    return role in ORDER_CREATOR_ROLES or role in KITCHEN_ROLES or role in ADMIN_ROLES
