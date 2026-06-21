# План модуля кухни — GastroSoft

**Статус: РЕАЛИЗОВАНО**

## Цель

Разделить UI на специализированные роли: официант (заказы), кухня (приготовление), шеф-повар (управление). Добавить трекинг по позициям, таймеры, примечания, приоритеты, метрики.

---

## 1. Расширение MySQL схемы

**Файл:** `gastrosoft_mysql.sql`

### Новые колонки в `customer_order`:
- `assigned_cook_id` — назначенный повар
- `priority` ENUM('normal','rush') — приоритет заказа
- `started_at` — время начала приготовления

### Новые колонки в `order_item`:
- `assigned_cook_id` — повар на позицию
- `started_at` — начало приготовления позиции
- `ready_at` — время готовности позиции

### Новая таблица `kitchen_log`:
- Лог действий на кухне (создание, назначение, статусы)

---

## 2. Реализованные файлы

| Файл | Статус |
|------|--------|
| `gastrosoft_mysql.sql` | Расширена схема |
| `mysql_store.py` | +12 методов для кухни |
| `kitchen_page.py` | Новая страница |
| `styles/kitchen/style.css` | Стили кухни |
| `orders_page.py` | Упрощён для официанта |
| `role_access.py` | Обновлён доступ |
| `shell.py` | Подключены kitchen + reports |
| `dashboard_page.py` | Метрики кухни |
| `data.py` | Заглушки |
| `reports_page.py` | Страница отчётов |
| `styles/reports/style.css` | Стили отчётов |

---

## 3. Методы в mysql_store.py

- `get_active_orders_for_kitchen()` — активные заказы с позициями
- `get_order_items(order_id)` — позиции заказа
- `update_item_status(item_id, status)` — смена статуса позиции
- `assign_cook_to_order(order_id, cook_id)` — назначение повара
- `set_order_priority(order_id, priority)` — приоритет
- `start_order(order_id)` — начало приготовления
- `mark_item_ready(item_id)` — отметка готовности
- `get_kitchen_stats()` — статистика кухни
- `get_order_history(limit)` — история заказов
- `log_kitchen_action(order_id, action, note)` — лог
- `get_cooks()` — список поваров
- `get_active_orders_for_kitchen()` — все активные заказы
