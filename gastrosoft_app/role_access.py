KITCHEN_ROLES = {"Повар", "Шеф-повар"}
ORDER_CREATOR_ROLES = {"Официант", "Менеджер зала", "Администратор системы", "Директор"}
CASHIER_ROLES = {"Кассир"}
ADMIN_ROLES = {"Администратор системы", "Директор"}
RESERVATION_ROLES = {"Менеджер зала", "Администратор системы", "Директор"}
INVENTORY_ROLES = {"Бухгалтер", "Администратор системы", "Директор"}
STAFF_ROLES = {"Администратор системы", "Директор"}


ROLE_ALLOWED_PAGES = {
    "Администратор системы": ["dashboard", "staff", "reservations", "orders", "inventory"],
    "Директор": ["dashboard", "staff", "reservations", "orders", "inventory"],
    "Менеджер зала": ["reservations", "orders"],
    "Официант": ["orders"],
    "Кассир": ["orders"],
    "Шеф-повар": ["orders"],
    "Повар": ["orders"],
    "Бухгалтер": ["inventory"],
}

ROLE_DEFAULT_PAGE = {
    "Администратор системы": "dashboard",
    "Директор": "dashboard",
    "Менеджер зала": "reservations",
    "Официант": "orders",
    "Кассир": "orders",
    "Шеф-повар": "orders",
    "Повар": "orders",
    "Бухгалтер": "inventory",
}


ROLE_PAGE_META = {
    ("Официант", "orders"): ("Оформление заказа", "Выбор блюд, столика и передача заказа на кухню"),
    ("Менеджер зала", "orders"): ("Заказы зала", "Контроль оформления заказов и передачи на кухню"),
    ("Кассир", "orders"): ("Закрытие заказов", "Просмотр готовых заказов и закрытие оплаты"),
    ("Шеф-повар", "orders"): ("Кухонная очередь", "Контроль активных заказов кухни"),
    ("Повар", "orders"): ("Кухонная очередь", "Быстрая обработка заказов кухни"),
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
