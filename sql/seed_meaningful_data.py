from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mysql_connection import MySQLConnectionManager


PASSWORD_1234_HASH = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"


def main() -> int:
    manager = MySQLConnectionManager()
    with manager.connect(include_database=True) as connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                seed_reference_data(cursor)
                seed_staff(cursor)
                seed_hall(cursor)
                seed_menu_and_inventory(cursor)
                seed_reservations(cursor)
                seed_orders(cursor)
                seed_shifts(cursor)
                seed_forecasts(cursor)
                print_counts(cursor)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return 0


def seed_reference_data(cursor) -> None:
    insert_many_ignore(
        cursor,
        "skill",
        ["name", "description"],
        [
            ("Аналитика", "Работа с показателями и отчетами"),
            ("Горячий цех", "Приготовление горячих блюд"),
            ("Холодный цех", "Салаты, закуски и холодные блюда"),
            ("Гриль", "Работа с гриль-станцией"),
            ("Бронирования", "Организация посадки гостей"),
            ("Кассовая дисциплина", "Закрытие смены и работа с оплатами"),
            ("Бар", "Напитки и кофейная станция"),
            ("Склад", "Учет остатков и списаний"),
            ("VIP-сервис", "Обслуживание постоянных гостей"),
            ("Санитарный контроль", "Контроль чистоты и чек-листов"),
            ("Су-вид", "Низкотемпературное приготовление"),
            ("Обучение стажеров", "Наставничество в смене"),
        ],
    )
    insert_many_ignore(
        cursor,
        "shift_status",
        ["code", "name"],
        [
            ("DRAFT", "Draft"),
            ("OPEN", "Open"),
            ("ON_BREAK", "On break"),
            ("DELAYED", "Delayed"),
            ("NO_SHOW", "No show"),
            ("ARCHIVED", "Archived"),
        ],
    )
    insert_many_ignore(
        cursor,
        "reservation_status",
        ["code", "name"],
        [
            ("PENDING", "Pending"),
            ("CONFIRMED", "Confirmed"),
            ("SEATED", "Seated"),
            ("COMPLETED", "Completed"),
            ("CANCELLED", "Cancelled"),
            ("NO_SHOW", "No show"),
            ("WAITLIST", "Waitlist"),
            ("HOLD", "Temporary hold"),
            ("EXPIRED", "Expired"),
            ("TRANSFERRED", "Transferred"),
        ],
    )
    insert_many_ignore(
        cursor,
        "order_status",
        ["code", "name"],
        [
            ("PAID", "Paid"),
            ("REFUNDED", "Refunded"),
            ("VOIDED", "Voided"),
        ],
    )
    insert_many_ignore(
        cursor,
        "order_item_status",
        ["code", "name"],
        [
            ("HOLD", "On hold"),
            ("REPLACED", "Replaced"),
            ("RETURNED", "Returned"),
            ("WASTE", "Waste"),
            ("REFUNDED", "Refunded"),
        ],
    )
    insert_many_ignore(
        cursor,
        "payment_method",
        ["code", "name"],
        [
            ("SBP", "SBP"),
            ("QR", "QR payment"),
            ("BONUS", "Bonus points"),
            ("VOUCHER", "Voucher"),
            ("MIXED", "Mixed payment"),
            ("TRANSFER", "Bank transfer"),
            ("CORPORATE", "Corporate account"),
        ],
    )
    insert_many_ignore(
        cursor,
        "measurement_unit",
        ["code", "name", "description"],
        [
            ("box", "Box", "Packaged box"),
            ("bottle", "Bottle", "Bottle unit"),
            ("portion", "Portion", "Prepared portion"),
            ("tray", "Tray", "Kitchen tray"),
            ("pack", "Pack", "Supplier pack"),
            ("bunch", "Bunch", "Greens bunch"),
        ],
    )
    insert_many_ignore(
        cursor,
        "stock_operation_type",
        ["code", "name", "operation_sign"],
        [
            ("TRANSFER_IN", "Transfer in", 1),
            ("TRANSFER_OUT", "Transfer out", -1),
            ("RETURN_TO_SUPPLIER", "Return to supplier", -1),
            ("SPOILAGE", "Spoilage", -1),
            ("INVENTORY_COUNT", "Inventory count correction", 1),
            ("PRODUCTION_USE", "Production use", -1),
        ],
    )
    insert_many_ignore(
        cursor,
        "shift_type",
        ["code", "name", "default_start_time", "default_end_time", "description"],
        [
            ("BREAKFAST", "Breakfast shift", "07:00:00", "12:00:00", "Morning breakfast service"),
            ("LUNCH_PEAK", "Lunch peak", "11:00:00", "16:00:00", "Lunch rush support"),
            ("DINNER_PEAK", "Dinner peak", "18:00:00", "23:30:00", "Dinner rush support"),
            ("BANQUET", "Banquet shift", "15:00:00", "23:00:00", "Events and banquets"),
            ("PREP", "Prep shift", "06:00:00", "12:00:00", "Kitchen preparation"),
            ("CLOSING", "Closing shift", "20:00:00", "02:00:00", "Closing operations"),
        ],
    )
    insert_many_ignore(
        cursor,
        "swap_request_status",
        ["code", "name"],
        [
            ("OFFERED", "Offered"),
            ("ASSIGNED", "Assigned"),
            ("EXPIRED", "Expired"),
            ("WITHDRAWN", "Withdrawn"),
            ("NEED_APPROVAL", "Need approval"),
            ("ESCALATED", "Escalated"),
        ],
    )


def seed_staff(cursor) -> None:
    employees = [
        ("ADMIN", "Иванова", "Елена", "Сергеевна", "+7 900 200-10-01", "admin@gastrosoft.local", "admin"),
        ("HALL_MANAGER", "Никифорова", "Алла", "Петровна", "+7 900 200-10-02", "hall2@gastrosoft.local", "hall2"),
        ("WAITER", "Соколов", "Артем", "Игоревич", "+7 900 200-10-03", "waiter2@gastrosoft.local", "waiter2"),
        ("WAITER", "Морозова", "Дарья", "Андреевна", "+7 900 200-10-04", "waiter3@gastrosoft.local", "waiter3"),
        ("WAITER", "Лебедев", "Никита", "Олегович", "+7 900 200-10-05", "waiter4@gastrosoft.local", "waiter4"),
        ("CHEF", "Синицын", "Роман", "Владимирович", "+7 900 200-10-07", "chef2@gastrosoft.local", "chef2"),
        ("COOK", "Захаров", "Михаил", "Павлович", "+7 900 200-10-08", "cook2@gastrosoft.local", "cook2"),
        ("COOK", "Ершова", "Лидия", "Максимовна", "+7 900 200-10-09", "cook3@gastrosoft.local", "cook3"),
        ("COOK", "Тимофеев", "Глеб", "Денисович", "+7 900 200-10-10", "cook4@gastrosoft.local", "cook4"),
        ("ACCOUNTANT", "Гаврилова", "Марина", "Романовна", "+7 900 200-10-11", "accountant2@gastrosoft.local", "accountant2"),
        ("WAITER", "Алимова", "Софья", "Ринатовна", "+7 900 200-10-12", "waiter5@gastrosoft.local", "waiter5"),
    ]
    for role_code, last_name, first_name, middle_name, phone, email, login in employees:
        role_id = id_by(cursor, "employee_role", "role_id", "code", role_code)
        employee_id = employee_id_by_email(cursor, email)
        if employee_id is None:
            cursor.execute(
                """
                INSERT INTO employee (role_id, last_name, first_name, middle_name, phone, email, hire_date, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY), 1)
                """,
                (role_id, last_name, first_name, middle_name, phone, email),
            )
            employee_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT IGNORE INTO app_user (employee_id, login, password_hash, is_active)
            VALUES (%s, %s, %s, 1)
            """,
            (employee_id, login, PASSWORD_1234_HASH),
        )

    skill_names = [
        "Аналитика",
        "Горячий цех",
        "Холодный цех",
        "Гриль",
        "Бронирования",
        "Кассовая дисциплина",
        "Бар",
        "Склад",
        "VIP-сервис",
        "Санитарный контроль",
        "Су-вид",
        "Обучение стажеров",
    ]
    skill_ids = {name: id_by(cursor, "skill", "skill_id", "name", name) for name in skill_names}
    cursor.execute("SELECT employee_id, role_id FROM employee WHERE is_active = 1 ORDER BY employee_id")
    all_employees = cursor.fetchall()
    for index, employee in enumerate(all_employees):
        first_skill = skill_names[index % len(skill_names)]
        second_skill = skill_names[(index + 4) % len(skill_names)]
        for offset, skill_name in enumerate([first_skill, second_skill]):
            cursor.execute(
                """
                INSERT IGNORE INTO employee_skill (employee_id, skill_id, skill_level, note)
                VALUES (%s, %s, %s, %s)
                """,
                (employee["employee_id"], skill_ids[skill_name], 5 - offset, "seed:staff-skill"),
            )

    shift_codes = ["MORNING", "DAY", "EVENING", "LUNCH_PEAK", "DINNER_PEAK", "BANQUET"]
    for index, employee in enumerate(all_employees):
        for shift_code in [shift_codes[index % len(shift_codes)], shift_codes[(index + 2) % len(shift_codes)]]:
            cursor.execute(
                """
                INSERT IGNORE INTO employee_shift_preference (employee_id, shift_type_id, preference_level, note)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    employee["employee_id"],
                    id_by(cursor, "shift_type", "shift_type_id", "code", shift_code),
                    4 if index % 2 == 0 else 3,
                    "seed:preference",
                ),
            )


def seed_hall(cursor) -> None:
    tables = [
        ("T-01", 2, "Окно, тихая зона"),
        ("T-02", 2, "Барная зона"),
        ("T-03", 4, "Основной зал"),
        ("T-04", 4, "Основной зал"),
        ("T-05", 6, "Семейный стол"),
        ("T-06", 6, "VIP-угол"),
        ("T-07", 2, "У окна"),
        ("T-08", 4, "Центр зала"),
        ("T-09", 4, "Рядом с кухней"),
        ("T-10", 8, "Банкетная зона"),
        ("T-11", 2, "Лаунж"),
        ("T-12", 6, "Большая компания"),
        ("T-13", 4, "Терраса"),
        ("T-14", 4, "Терраса"),
        ("T-15", 10, "Общий стол"),
    ]
    insert_many_ignore(cursor, "restaurant_table", ["code", "seats_count", "is_active", "note"], [(c, s, 1, n) for c, s, n in tables])

    guests = [
        ("Екатерина Миронова", "+7 912 555-11-22", "ekaterina@example.com", "Любит стол у окна"),
        ("Денис Петров", "+7 922 100-50-40", "denis@example.com", "Частый гость на обед"),
        ("Александр Котов", "+7 987 300-44-10", "kotov@example.com", "Предпочитает мясные блюда"),
        ("Ольга Смирнова", "+7 903 222-19-35", "olga@example.com", "Бронь на семью"),
        ("Мария Белова", "+7 927 440-33-12", "maria@example.com", "Без орехов"),
        ("Илья Воронов", "+7 905 770-18-80", "voronov@example.com", "VIP"),
        ("Ксения Орлова", "+7 917 880-11-40", "ksenia@example.com", "Терраса летом"),
        ("Павел Громов", "+7 909 450-77-33", "pavel@example.com", "Бизнес-ланч"),
        ("Наталья Руднева", "+7 961 300-65-90", "natalia@example.com", "Вегетарианское меню"),
        ("Сергей Комаров", "+7 919 800-41-20", "komarov@example.com", "Любит острое"),
        ("Анна Волкова", "+7 910 700-55-11", "anna@example.com", "Детский стул"),
        ("Виктор Лазарев", "+7 920 222-88-44", "lazarev@example.com", "Корпоративные ужины"),
        ("Полина Егорова", "+7 904 100-29-71", "polina@example.com", "Праздники"),
        ("Роман Синицын", "+7 927 310-90-24", "roman@example.com", "Банкет"),
        ("Алина Морозова", "+7 937 230-45-19", "alina@example.com", "Без глютена"),
        ("Глеб Тимофеев", "+7 911 222-10-10", "gleb@example.com", "Тихий стол"),
        ("Софья Алимова", "+7 909 333-21-42", "sofia@example.com", "Любит десерты"),
        ("Дмитрий Ершов", "+7 951 400-20-30", "ershov@example.com", "Стол на двоих"),
        ("Лидия Захарова", "+7 927 654-18-45", "lidia@example.com", "Без лука"),
        ("Артур Фролов", "+7 903 808-70-60", "artur@example.com", "QR-оплата"),
    ]
    for guest in guests:
        ensure_guest(cursor, *guest)


def seed_menu_and_inventory(cursor) -> None:
    categories = [
        ("Закуски", "Небольшие блюда для начала ужина", 10),
        ("Салаты", "Свежие салаты и холодный цех", 20),
        ("Супы", "Супы на каждый день", 30),
        ("Горячее", "Основные блюда", 40),
        ("Паста и ризотто", "Итальянская линия", 50),
        ("Гриль", "Блюда с гриль-станции", 60),
        ("Десерты", "Сладкое завершение", 70),
        ("Напитки", "Безалкогольные напитки", 80),
        ("Кофе и чай", "Горячие напитки", 90),
        ("Детское меню", "Легкие блюда для детей", 100),
    ]
    insert_many_ignore(cursor, "menu_category", ["name", "description", "sort_order"], categories)

    ingredients = [
        ("kg", "Говядина вырезка", "1450.00", "8.000"),
        ("kg", "Куриное филе", "420.00", "12.000"),
        ("kg", "Лосось филе", "1600.00", "5.000"),
        ("kg", "Креветки", "1200.00", "4.000"),
        ("kg", "Томаты", "180.00", "15.000"),
        ("kg", "Огурцы", "130.00", "12.000"),
        ("kg", "Картофель", "75.00", "25.000"),
        ("kg", "Морковь", "65.00", "10.000"),
        ("kg", "Лук репчатый", "60.00", "8.000"),
        ("kg", "Сыр пармезан", "1900.00", "3.000"),
        ("kg", "Сыр моцарелла", "850.00", "4.000"),
        ("kg", "Рис арборио", "330.00", "6.000"),
        ("kg", "Паста тальятелле", "260.00", "8.000"),
        ("l", "Сливки 33%", "290.00", "6.000"),
        ("l", "Молоко", "95.00", "10.000"),
        ("kg", "Мука", "80.00", "15.000"),
        ("pcs", "Яйцо куриное", "12.00", "60.000"),
        ("kg", "Сахар", "90.00", "10.000"),
        ("kg", "Шоколад темный", "780.00", "3.000"),
        ("kg", "Клубника", "620.00", "4.000"),
        ("bunch", "Базилик", "95.00", "8.000"),
        ("bunch", "Руккола", "110.00", "8.000"),
        ("l", "Оливковое масло", "690.00", "5.000"),
        ("kg", "Хлеб чиабатта", "210.00", "6.000"),
        ("kg", "Грибы шампиньоны", "240.00", "8.000"),
        ("kg", "Бекон", "720.00", "4.000"),
        ("kg", "Тунец", "980.00", "3.000"),
        ("kg", "Свекла", "85.00", "8.000"),
        ("kg", "Тыква", "110.00", "8.000"),
        ("l", "Апельсиновый сок", "150.00", "12.000"),
        ("l", "Морс ягодный", "130.00", "12.000"),
        ("kg", "Кофе зерно", "1350.00", "4.000"),
        ("kg", "Чай черный", "980.00", "2.000"),
        ("kg", "Чай зеленый", "1050.00", "2.000"),
        ("kg", "Соль морская", "70.00", "6.000"),
        ("kg", "Перец черный", "540.00", "2.000"),
    ]
    for unit_code, name, cost, critical in ingredients:
        cursor.execute(
            """
            INSERT IGNORE INTO ingredient (measurement_unit_id, name, cost_per_unit, critical_level, is_active)
            VALUES (%s, %s, %s, %s, 1)
            """,
            (id_by(cursor, "measurement_unit", "measurement_unit_id", "code", unit_code), name, Decimal(cost), Decimal(critical)),
        )

    dishes = [
        ("Закуски", "Брускетта с томатами", "Хрустящая чиабатта, томаты и базилик", "390.00", 7),
        ("Закуски", "Тар-тар из лосося", "Лосось, оливковое масло и зелень", "690.00", 12),
        ("Закуски", "Креветки темпура", "Креветки в легком кляре", "640.00", 10),
        ("Салаты", "Цезарь с курицей", "Куриное филе, салат и пармезан", "520.00", 11),
        ("Салаты", "Салат с тунцом", "Тунец, яйцо, овощи и зелень", "590.00", 9),
        ("Салаты", "Руккола с креветками", "Руккола, креветки и томаты", "720.00", 10),
        ("Супы", "Крем-суп из тыквы", "Тыква, сливки и пряности", "360.00", 14),
        ("Супы", "Куриный бульон", "Курица, овощи и зелень", "320.00", 12),
        ("Супы", "Грибной крем-суп", "Шампиньоны и сливки", "390.00", 13),
        ("Горячее", "Стейк из говядины", "Говяжья вырезка с гарниром", "1490.00", 22),
        ("Горячее", "Лосось с овощами", "Филе лосося и овощи", "1320.00", 18),
        ("Горячее", "Куриная грудка су-вид", "Нежная курица и сливочный соус", "760.00", 20),
        ("Паста и ризотто", "Паста карбонара", "Бекон, сливки и пармезан", "620.00", 15),
        ("Паста и ризотто", "Ризотто с грибами", "Арборио, грибы и пармезан", "690.00", 18),
        ("Паста и ризотто", "Паста с креветками", "Тальятелле, креветки и томаты", "780.00", 16),
        ("Гриль", "Бургер с говядиной", "Котлета, сыр и овощи", "680.00", 15),
        ("Гриль", "Курица гриль", "Маринованное филе на гриле", "620.00", 16),
        ("Гриль", "Овощи гриль", "Сезонные овощи", "410.00", 12),
        ("Десерты", "Шоколадный фондан", "Горячий шоколадный десерт", "430.00", 12),
        ("Десерты", "Панна-котта с клубникой", "Сливочный десерт", "390.00", 9),
        ("Десерты", "Сырники", "Творожные сырники со сметаной", "360.00", 12),
        ("Напитки", "Апельсиновый фреш", "Свежевыжатый сок", "330.00", 5),
        ("Напитки", "Ягодный морс", "Домашний морс", "190.00", 3),
        ("Напитки", "Лимонад базилик", "Освежающий лимонад", "260.00", 4),
        ("Кофе и чай", "Капучино", "Кофе с молоком", "210.00", 4),
        ("Кофе и чай", "Американо", "Черный кофе", "170.00", 3),
        ("Кофе и чай", "Чай зеленый", "Чайник зеленого чая", "240.00", 5),
        ("Детское меню", "Детская паста", "Паста со сливочным соусом", "310.00", 10),
        ("Детское меню", "Куриные наггетсы", "Курица в хрустящей панировке", "350.00", 12),
        ("Детское меню", "Картофельное пюре", "Нежное пюре", "190.00", 8),
    ]
    for category, name, description, price, minutes in dishes:
        cursor.execute(
            """
            INSERT IGNORE INTO dish (category_id, name, description, base_price, prep_time_minutes, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (id_by(cursor, "menu_category", "category_id", "name", category), name, description, Decimal(price), minutes),
        )

    modifier_groups = [
        ("Острота", "Уровень остроты блюда"),
        ("Гарнир", "Выбор гарнира"),
        ("Соус", "Дополнительный соус"),
        ("Молоко", "Молоко для кофе"),
        ("Сахар", "Сладость напитка"),
        ("Степень прожарки", "Прожарка мяса"),
        ("Исключить ингредиент", "Убрать нежелательный ингредиент"),
        ("Размер напитка", "Объем напитка"),
        ("Детская подача", "Упрощенная подача"),
        ("Температура напитка", "Горячий или холодный"),
    ]
    insert_many_ignore(cursor, "modifier_group", ["name", "description"], modifier_groups)
    options = [
        ("Острота", "Не остро", "0.00"),
        ("Острота", "Средне остро", "0.00"),
        ("Острота", "Очень остро", "50.00"),
        ("Гарнир", "Картофель", "120.00"),
        ("Гарнир", "Овощи гриль", "160.00"),
        ("Гарнир", "Рис", "110.00"),
        ("Соус", "Сливочный", "80.00"),
        ("Соус", "Перечный", "90.00"),
        ("Соус", "Томатный", "70.00"),
        ("Молоко", "Обычное", "0.00"),
        ("Молоко", "Безлактозное", "60.00"),
        ("Молоко", "Овсяное", "70.00"),
        ("Сахар", "Без сахара", "0.00"),
        ("Сахар", "Одна порция", "0.00"),
        ("Сахар", "Две порции", "0.00"),
        ("Степень прожарки", "Medium rare", "0.00"),
        ("Степень прожарки", "Medium", "0.00"),
        ("Степень прожарки", "Well done", "0.00"),
        ("Исключить ингредиент", "Без лука", "0.00"),
        ("Исключить ингредиент", "Без сыра", "0.00"),
        ("Исключить ингредиент", "Без зелени", "0.00"),
        ("Размер напитка", "300 мл", "0.00"),
        ("Размер напитка", "400 мл", "60.00"),
        ("Размер напитка", "500 мл", "100.00"),
        ("Детская подача", "Без специй", "0.00"),
        ("Детская подача", "Соус отдельно", "0.00"),
        ("Температура напитка", "Горячий", "0.00"),
        ("Температура напитка", "Со льдом", "0.00"),
    ]
    for group, name, price in options:
        cursor.execute(
            """
            INSERT IGNORE INTO modifier_option (modifier_group_id, name, extra_price, is_active)
            VALUES (%s, %s, %s, 1)
            """,
            (id_by(cursor, "modifier_group", "modifier_group_id", "name", group), name, Decimal(price)),
        )

    dish_names = [name for _, name, _, _, _ in dishes]
    group_names = [name for name, _ in modifier_groups]
    for index, dish_name in enumerate(dish_names):
        for group_name in [group_names[index % len(group_names)], group_names[(index + 2) % len(group_names)]]:
            cursor.execute(
                """
                INSERT IGNORE INTO dish_modifier_group (dish_id, modifier_group_id, min_select_count, max_select_count, sort_order)
                VALUES (%s, %s, 0, 1, %s)
                """,
                (
                    id_by(cursor, "dish", "dish_id", "name", dish_name),
                    id_by(cursor, "modifier_group", "modifier_group_id", "name", group_name),
                    index,
                ),
            )

    recipe_pairs = [
        ("Брускетта с томатами", ["Хлеб чиабатта", "Томаты", "Базилик", "Оливковое масло"]),
        ("Тар-тар из лосося", ["Лосось филе", "Оливковое масло", "Базилик"]),
        ("Том Ям", ["Креветки", "Томаты", "Сливки 33%", "Перец черный"]),
        ("Крем-суп из грибов", ["Грибы шампиньоны", "Сливки 33%", "Лук репчатый"]),
        ("Паста Альфредо", ["Паста тальятелле", "Сливки 33%", "Сыр пармезан"]),
        ("Бургер GastroSoft", ["Говядина вырезка", "Сыр моцарелла", "Томаты"]),
        ("Лимонад базилик-лайм", ["Базилик", "Сахар"]),
        ("Эспрессо", ["Кофе зерно"]),
        ("Креветки темпура", ["Креветки", "Мука", "Яйцо куриное"]),
        ("Цезарь с курицей", ["Куриное филе", "Сыр пармезан", "Яйцо куриное"]),
        ("Салат с тунцом", ["Тунец", "Огурцы", "Яйцо куриное"]),
        ("Руккола с креветками", ["Руккола", "Креветки", "Томаты"]),
        ("Крем-суп из тыквы", ["Тыква", "Сливки 33%", "Морковь"]),
        ("Куриный бульон", ["Куриное филе", "Морковь", "Лук репчатый"]),
        ("Грибной крем-суп", ["Грибы шампиньоны", "Сливки 33%", "Лук репчатый"]),
        ("Стейк из говядины", ["Говядина вырезка", "Картофель", "Перец черный"]),
        ("Лосось с овощами", ["Лосось филе", "Томаты", "Огурцы"]),
        ("Куриная грудка су-вид", ["Куриное филе", "Сливки 33%", "Соль морская"]),
        ("Паста карбонара", ["Паста тальятелле", "Бекон", "Сыр пармезан", "Сливки 33%"]),
        ("Ризотто с грибами", ["Рис арборио", "Грибы шампиньоны", "Сыр пармезан"]),
        ("Паста с креветками", ["Паста тальятелле", "Креветки", "Томаты"]),
        ("Бургер с говядиной", ["Говядина вырезка", "Сыр моцарелла", "Томаты"]),
        ("Курица гриль", ["Куриное филе", "Оливковое масло", "Перец черный"]),
        ("Овощи гриль", ["Томаты", "Огурцы", "Оливковое масло"]),
        ("Шоколадный фондан", ["Шоколад темный", "Мука", "Яйцо куриное", "Сахар"]),
        ("Панна-котта с клубникой", ["Сливки 33%", "Клубника", "Сахар"]),
        ("Сырники", ["Мука", "Яйцо куриное", "Сахар"]),
        ("Апельсиновый фреш", ["Апельсиновый сок"]),
        ("Ягодный морс", ["Морс ягодный"]),
        ("Лимонад базилик", ["Базилик", "Сахар"]),
        ("Капучино", ["Кофе зерно", "Молоко"]),
        ("Американо", ["Кофе зерно"]),
        ("Чай зеленый", ["Чай зеленый"]),
        ("Детская паста", ["Паста тальятелле", "Сливки 33%"]),
        ("Куриные наггетсы", ["Куриное филе", "Мука", "Яйцо куриное"]),
        ("Картофельное пюре", ["Картофель", "Молоко"]),
    ]
    for dish_name, ingredient_names in recipe_pairs:
        for offset, ingredient_name in enumerate(ingredient_names):
            cursor.execute(
                """
                INSERT IGNORE INTO recipe_item (dish_id, ingredient_id, quantity)
                VALUES (%s, %s, %s)
                """,
                (
                    id_by(cursor, "dish", "dish_id", "name", dish_name),
                    id_by(cursor, "ingredient", "ingredient_id", "name", ingredient_name),
                    Decimal("0.120") if offset == 0 else Decimal("0.040"),
                ),
            )

    user_id = id_by(cursor, "app_user", "user_id", "login", "admin")
    if user_id is None:
        user_id = id_by(cursor, "app_user", "user_id", "login", "director")
    operation_type_receipt = id_by(cursor, "stock_operation_type", "stock_operation_type_id", "code", "RECEIPT")
    operation_type_writeoff = id_by(cursor, "stock_operation_type", "stock_operation_type_id", "code", "WRITE_OFF")
    cursor.execute("SELECT ingredient_id, name, critical_level FROM ingredient ORDER BY ingredient_id")
    for index, ingredient in enumerate(cursor.fetchall(), start=1):
        ensure_inventory_operation(
            cursor,
            ingredient["ingredient_id"],
            operation_type_receipt,
            Decimal("20.000") + Decimal(index % 9),
            user_id,
            f"seed:receipt:{ingredient['name']}",
        )
        if index <= 18:
            ensure_inventory_operation(
                cursor,
                ingredient["ingredient_id"],
                operation_type_writeoff,
                Decimal("1.000") + Decimal(index % 3) / Decimal("10"),
                user_id,
                f"seed:writeoff:{ingredient['name']}",
            )


def seed_reservations(cursor) -> None:
    statuses = ["PENDING", "CONFIRMED", "SEATED", "COMPLETED", "CANCELLED", "NO_SHOW"]
    table_codes = [f"T-{index:02d}" for index in range(1, 16)]
    cursor.execute("SELECT phone FROM guest ORDER BY guest_id LIMIT 20")
    guest_phones = [row["phone"] for row in cursor.fetchall()]
    creator_id = id_by(cursor, "app_user", "user_id", "login", "hall2") or id_by(cursor, "app_user", "user_id", "login", "director")
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    for index, phone in enumerate(guest_phones, start=1):
        note = f"seed:reservation:{index:02d}"
        if exists_by_note(cursor, "reservation", note):
            continue
        reserved_from = base + timedelta(hours=index % 8, days=index // 5)
        reserved_to = reserved_from + timedelta(hours=2)
        cursor.execute(
            """
            INSERT INTO reservation (
                guest_id, table_id, reservation_status_id, reserved_from, reserved_to,
                guest_count, created_by_user_id, note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_by(cursor, "guest", "guest_id", "phone", phone),
                id_by(cursor, "restaurant_table", "table_id", "code", table_codes[(index - 1) % len(table_codes)]),
                id_by(cursor, "reservation_status", "reservation_status_id", "code", statuses[index % len(statuses)]),
                reserved_from,
                reserved_to,
                2 + (index % 6),
                creator_id,
                note,
            ),
        )


def seed_orders(cursor) -> None:
    dish_names = [
        "Брускетта с томатами",
        "Цезарь с курицей",
        "Стейк из говядины",
        "Паста карбонара",
        "Капучино",
        "Шоколадный фондан",
        "Лосось с овощами",
        "Ризотто с грибами",
        "Апельсиновый фреш",
        "Куриные наггетсы",
    ]
    status_codes = ["ACCEPTED", "PREPARING", "READY", "SERVED", "CLOSED"]
    payment_codes = ["CASH", "CARD", "ONLINE", "SBP", "QR", "MIXED"]
    table_codes = [f"T-{index:02d}" for index in range(1, 16)]
    creator_id = id_by(cursor, "app_user", "user_id", "login", "waiter2") or id_by(cursor, "app_user", "user_id", "login", "director")
    base = datetime.now().replace(minute=15, second=0, microsecond=0)
    item_status_ids = {
        "ACCEPTED": id_by(cursor, "order_item_status", "order_item_status_id", "code", "QUEUED"),
        "PREPARING": id_by(cursor, "order_item_status", "order_item_status_id", "code", "COOKING"),
        "READY": id_by(cursor, "order_item_status", "order_item_status_id", "code", "READY"),
        "SERVED": id_by(cursor, "order_item_status", "order_item_status_id", "code", "SERVED"),
        "CLOSED": id_by(cursor, "order_item_status", "order_item_status_id", "code", "SERVED"),
    }
    for index in range(1, 26):
        note = f"seed:order:{index:02d}"
        order_id = id_by(cursor, "customer_order", "order_id", "note", note)
        status_code = status_codes[index % len(status_codes)]
        created_at = base - timedelta(hours=index)
        closed_at = created_at + timedelta(hours=1, minutes=20) if status_code in {"SERVED", "CLOSED"} else None
        if order_id is None:
            cursor.execute(
                """
                INSERT INTO customer_order (
                    table_id, order_status_id, created_by_user_id, payment_method_id,
                    created_at, closed_at, note
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_by(cursor, "restaurant_table", "table_id", "code", table_codes[index % len(table_codes)]),
                    id_by(cursor, "order_status", "order_status_id", "code", status_code),
                    creator_id,
                    id_by(cursor, "payment_method", "payment_method_id", "code", payment_codes[index % len(payment_codes)]),
                    created_at,
                    closed_at,
                    note,
                ),
            )
            order_id = cursor.lastrowid
        for offset in range(2):
            dish_name = dish_names[(index + offset) % len(dish_names)]
            item_note = f"seed:item:{index:02d}:{offset}"
            if id_by(cursor, "order_item", "order_item_id", "note", item_note) is not None:
                continue
            cursor.execute("SELECT base_price FROM dish WHERE name = %s", (dish_name,))
            price = cursor.fetchone()["base_price"]
            cursor.execute(
                """
                INSERT INTO order_item (order_id, dish_id, order_item_status_id, quantity, unit_price, note)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    id_by(cursor, "dish", "dish_id", "name", dish_name),
                    item_status_ids[status_code],
                    1 + ((index + offset) % 2),
                    price,
                    item_note,
                ),
            )
            order_item_id = cursor.lastrowid
            if index <= 15:
                option_name = "Средне остро" if index % 2 else "Без лука"
                cursor.execute(
                    """
                    INSERT IGNORE INTO order_item_modifier (order_item_id, modifier_option_id, extra_charge)
                    VALUES (%s, %s, %s)
                    """,
                    (order_item_id, modifier_option_id_by_name(cursor, option_name), Decimal("0.00")),
                )


def seed_shifts(cursor) -> None:
    creator_id = id_by(cursor, "app_user", "user_id", "login", "admin") or id_by(cursor, "app_user", "user_id", "login", "director")
    shift_codes = ["MORNING", "DAY", "EVENING", "LUNCH_PEAK", "DINNER_PEAK", "PREP"]
    status_codes = ["PLANNED", "IN_PROGRESS", "COMPLETED"]
    base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    for index in range(1, 31):
        shift_code = shift_codes[index % len(shift_codes)]
        note = f"seed:shift:{index:02d}"
        shift_id = id_by(cursor, "work_shift", "shift_id", "note", note)
        planned_start = base_date + timedelta(days=(index - 1) // 3, hours=(index % 3) * 5)
        planned_end = planned_start + timedelta(hours=6)
        if shift_id is None:
            cursor.execute(
                """
                INSERT INTO work_shift (
                    shift_type_id, shift_status_id, planned_start, planned_end, created_by_user_id, note
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    id_by(cursor, "shift_type", "shift_type_id", "code", shift_code),
                    id_by(cursor, "shift_status", "shift_status_id", "code", status_codes[index % len(status_codes)]),
                    planned_start,
                    planned_end,
                    creator_id,
                    note,
                ),
            )
            shift_id = cursor.lastrowid
        cursor.execute(
            """
            SELECT employee_id, role_id
            FROM employee
            WHERE is_active = 1
            ORDER BY employee_id
            LIMIT 2 OFFSET %s
            """,
            (index % 10,),
        )
        employees = cursor.fetchall()
        if len(employees) < 2:
            cursor.execute("SELECT employee_id, role_id FROM employee WHERE is_active = 1 ORDER BY employee_id LIMIT 2")
            employees = cursor.fetchall()
        for employee in employees:
            cursor.execute(
                """
                INSERT IGNORE INTO shift_assignment (shift_id, employee_id, assignment_role_id, note)
                VALUES (%s, %s, %s, %s)
                """,
                (shift_id, employee["employee_id"], employee["role_id"], f"seed:assignment:{index:02d}"),
            )

    cursor.execute("SELECT assignment_id FROM shift_assignment WHERE note LIKE 'seed:assignment:%' ORDER BY assignment_id LIMIT 10")
    assignment_ids = [row["assignment_id"] for row in cursor.fetchall()]
    status_id = id_by(cursor, "swap_request_status", "swap_request_status_id", "code", "NEW")
    director_id = id_by(cursor, "app_user", "user_id", "login", "director")
    for index, assignment_id in enumerate(assignment_ids, start=1):
        reason = f"seed:swap:{index:02d}"
        if id_by(cursor, "shift_swap_request", "swap_request_id", "reason", reason) is not None:
            continue
        cursor.execute(
            """
            INSERT INTO shift_swap_request (
                assignment_id, requested_employee_id, swap_request_status_id, decided_by_user_id, reason
            )
            VALUES (%s, NULL, %s, %s, %s)
            """,
            (assignment_id, status_id, director_id, reason),
        )


def seed_forecasts(cursor) -> None:
    creator_id = id_by(cursor, "app_user", "user_id", "login", "director")
    role_codes = ["WAITER", "COOK", "HALL_MANAGER"]
    base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    for index in range(1, 13):
        note = f"seed:forecast:{index:02d}"
        forecast_id = id_by(cursor, "workload_forecast", "forecast_id", "note", note)
        start = base + timedelta(days=index // 3, hours=(index % 3) * 4)
        if forecast_id is None:
            cursor.execute(
                """
                INSERT INTO workload_forecast (
                    forecast_start, forecast_end, expected_guests, expected_orders,
                    hall_load_percent, kitchen_load_percent, created_by_user_id, note
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    start,
                    start + timedelta(hours=4),
                    25 + index * 4,
                    18 + index * 3,
                    Decimal(45 + index * 3),
                    Decimal(40 + index * 4),
                    creator_id,
                    note,
                ),
            )
            forecast_id = cursor.lastrowid
        for role_code in role_codes:
            cursor.execute(
                """
                INSERT IGNORE INTO staffing_requirement (forecast_id, role_id, required_employee_count)
                VALUES (%s, %s, %s)
                """,
                (
                    forecast_id,
                    id_by(cursor, "employee_role", "role_id", "code", role_code),
                    1 + (index % 3),
                ),
            )


def insert_many_ignore(cursor, table: str, columns: list[str], rows: list[tuple]) -> None:
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    cursor.executemany(
        f"INSERT IGNORE INTO {table} ({column_sql}) VALUES ({placeholders})",
        rows,
    )


def id_by(cursor, table: str, id_column: str, lookup_column: str, value):
    cursor.execute(
        f"SELECT {id_column} FROM {table} WHERE {lookup_column} = %s LIMIT 1",
        (value,),
    )
    row = cursor.fetchone()
    return row[id_column] if row else None


def employee_id_by_email(cursor, email: str):
    return id_by(cursor, "employee", "employee_id", "email", email)


def ensure_guest(cursor, full_name: str, phone: str, email: str, note: str) -> int:
    guest_id = id_by(cursor, "guest", "guest_id", "phone", phone)
    if guest_id is not None:
        return guest_id
    cursor.execute(
        """
        INSERT INTO guest (full_name, phone, email, note)
        VALUES (%s, %s, %s, %s)
        """,
        (full_name, phone, email, note),
    )
    return cursor.lastrowid


def modifier_option_id_by_name(cursor, name: str) -> int:
    cursor.execute("SELECT modifier_option_id FROM modifier_option WHERE name = %s LIMIT 1", (name,))
    return cursor.fetchone()["modifier_option_id"]


def exists_by_note(cursor, table: str, note: str) -> bool:
    return id_by(cursor, table, f"{table.split('_')[-1]}_id", "note", note) is not None


def ensure_inventory_operation(cursor, ingredient_id: int, operation_type_id: int, quantity: Decimal, user_id: int, note: str) -> None:
    cursor.execute("SELECT operation_id FROM inventory_operation WHERE note = %s LIMIT 1", (note,))
    if cursor.fetchone():
        return
    cursor.execute(
        """
        INSERT INTO inventory_operation (
            ingredient_id, stock_operation_type_id, quantity, performed_by_user_id, note
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (ingredient_id, operation_type_id, quantity, user_id, note),
    )


def print_counts(cursor) -> None:
    tables = [
        "employee",
        "app_user",
        "skill",
        "employee_skill",
        "employee_shift_preference",
        "restaurant_table",
        "guest",
        "reservation",
        "menu_category",
        "dish",
        "modifier_group",
        "modifier_option",
        "dish_modifier_group",
        "ingredient",
        "recipe_item",
        "inventory_operation",
        "customer_order",
        "order_item",
        "order_item_modifier",
        "work_shift",
        "shift_assignment",
        "shift_swap_request",
        "workload_forecast",
        "staffing_requirement",
    ]
    print("Seed complete. Row counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) AS count_value FROM {table}")
        print(f"{table}: {cursor.fetchone()['count_value']}")


if __name__ == "__main__":
    raise SystemExit(main())
