# Код функций кухонного модуля

Листинги подготовлены для приложения к пояснительной записке.

## 1. OrdersPage.apply_role_mode

```python
def apply_role_mode(self) -> None:
    role = self._current_role()
    can_create = can_create_orders(role)
    is_kitchen = can_process_kitchen(role)
    can_close = can_close_orders(role)

    self.menu_card.setVisible(can_create)
    self.order_card.setVisible(can_create)
    self.kitchen_card.setVisible(True)
    self.kitchen_controls.setVisible(is_kitchen)
    self.next_status_button.setVisible(is_kitchen)
    self.close_order_button.setVisible(can_close)

    if is_kitchen:
        self.kitchen_card.set_header("Кухонная очередь", "Повар и шеф-повар меняют статусы.")
        self.next_status_button.setText("Взять в работу")
    else:
        self.kitchen_card.set_header("Заказы", "Просмотр заказов и закрытие выданных.")
```

## 2. KitchenPage._build_order_card

```python
def _build_order_card(self, order: dict) -> QFrame:
    card = QFrame()
    card.setObjectName("kitchenOrderCard")
    is_rush = order.get("priority") == "rush"
    if is_rush:
        card.setProperty("rush", True)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(6)

    header = QHBoxLayout()
    header.setSpacing(10)

    order_no = QLabel(order.get("order_no", "GS-?"))
    order_no.setObjectName("kitchenOrderNo")
    header.addWidget(order_no)

    table_label = QLabel(f"Стол {order.get('table', '-')}")
    header.addWidget(table_label)

    if is_rush:
        rush_pill = StatusPill("СРОЧНО", "danger")
        header.addWidget(rush_pill)

    header.addStretch(1)

    timer_label = QLabel(self._calc_timer(order))
    timer_label.setObjectName("kitchenTimer")
    timer_label.setProperty("timer_color", self._timer_color(order))
    header.addWidget(timer_label)

    status = order.get("status", "")
    status_pill = StatusPill(status, self._status_tone(status))
    header.addWidget(status_pill)
    layout.addLayout(header)

    items = order.get("items", [])
    if isinstance(items, list) and items:
        for item in items:
            item_row = QHBoxLayout()
            item_row.setSpacing(8)

            dot = QLabel("●")
            dot.setObjectName("kitchenItemDot")
            dot.setProperty("dot_color", self._item_dot_color(item.get("status", "")))
            item_row.addWidget(dot)

            name_label = QLabel(f"{item.get('dish', '?')} x{item.get('quantity', 1)}")
            name_label.setObjectName("kitchenItemName")
            item_row.addWidget(name_label, 1)

            item_status_label = QLabel(item.get("status", ""))
            item_status_label.setObjectName("kitchenItemStatus")
            item_row.addWidget(item_status_label)

            if item.get("note"):
                note_label = QLabel(item["note"])
                note_label.setObjectName("kitchenItemNote")
                item_row.addWidget(note_label)

            layout.addLayout(item_row)
    return card
```

## 3. MySQLBackedStore.get_active_orders_for_kitchen

```python
def get_active_orders_for_kitchen(self) -> list[dict]:
    if not self.mysql_enabled:
        return self.kitchen_queue
    rows = self._fetch_all(
        """
        SELECT
            co.order_id,
            rt.code AS table_code,
            os.code AS status_code,
            co.created_at,
            co.started_at,
            co.priority,
            COALESCE(total.total_amount, 0) AS total_amount,
            CONCAT(cook_e.last_name, ' ', cook_e.first_name) AS cook_name
        FROM customer_order co
        LEFT JOIN restaurant_table rt ON rt.table_id = co.table_id
        JOIN order_status os ON os.order_status_id = co.order_status_id
        LEFT JOIN v_order_total total ON total.order_id = co.order_id
        LEFT JOIN employee cook_e ON cook_e.employee_id = co.assigned_cook_id
        WHERE os.code NOT IN ('CLOSED', 'CANCELLED')
        ORDER BY FIELD(co.priority, 'rush', 'normal'), co.created_at ASC
        """
    )
    result = []
    for row in rows:
        items = self.get_order_items(row["order_id"])
        result.append({
            "order_id": row["order_id"],
            "order_no": f"GS-{row['order_id']}",
            "table": row["table_code"] or "-",
            "created": row["created_at"].strftime("%H:%M") if row["created_at"] else "-",
            "started_at": row["started_at"],
            "status": _order_status_ru(row["status_code"]),
            "status_code": row["status_code"],
            "total": int(row["total_amount"] or 0),
            "priority": row["priority"],
            "cook_name": row["cook_name"] or "",
            "items": items,
        })
    return result
```

## 4. MySQLBackedStore.mark_item_ready

```python
def mark_item_ready(self, order_item_id: int) -> str:
    if not self.mysql_enabled:
        return "MySQL не подключен."
    try:
        ready_status_id = self._get_id(
            "order_item_status", "order_item_status_id", "code", "READY"
        )
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE order_item
                       SET order_item_status_id = %s, ready_at = COALESCE(ready_at, NOW())
                       WHERE order_item_id = %s""",
                    (ready_status_id, order_item_id),
                )
                cursor.execute(
                    "SELECT order_id FROM order_item WHERE order_item_id = %s",
                    (order_item_id,),
                )
                row = cursor.fetchone()
                if row:
                    self._update_order_status_from_items(connection, row[0])
            connection.commit()
        self.reload_from_mysql()
    except Error as exc:
        return f"Ошибка отметки готовности: {exc}"
    return "Позиция отмечена как готовая."
```

## 5. MySQLBackedStore.get_kitchen_stats

```python
def get_kitchen_stats(self) -> dict:
    if not self.mysql_enabled:
        return {"avg_prep_time": 0, "in_progress": 0, "completed_today": 0, "rush_active": 0}
    try:
        avg_row = self._fetch_one(
            """SELECT AVG(TIMESTAMPDIFF(MINUTE, started_at, ready_at)) AS avg_min
               FROM order_item
               WHERE started_at IS NOT NULL AND ready_at IS NOT NULL
                 AND DATE(ready_at) = CURRENT_DATE()"""
        )
        progress_row = self._fetch_one(
            """SELECT COUNT(*) AS cnt FROM customer_order co
               JOIN order_status os ON os.order_status_id = co.order_status_id
               WHERE os.code IN ('ACCEPTED', 'PREPARING')"""
        )
        completed_row = self._fetch_one(
            """SELECT COUNT(*) AS cnt FROM customer_order co
               JOIN order_status os ON os.order_status_id = co.order_status_id
               WHERE os.code IN ('READY', 'SERVED', 'CLOSED')
                 AND DATE(co.created_at) = CURRENT_DATE()"""
        )
        rush_row = self._fetch_one(
            """SELECT COUNT(*) AS cnt FROM customer_order
               WHERE priority = 'rush'
                 AND order_status_id IN (
                   SELECT order_status_id FROM order_status
                   WHERE code IN ('ACCEPTED', 'PREPARING'))"""
        )
        return {
            "avg_prep_time": int(avg_row["avg_min"] or 0) if avg_row else 0,
            "in_progress": int(progress_row["cnt"] or 0) if progress_row else 0,
            "completed_today": int(completed_row["cnt"] or 0) if completed_row else 0,
            "rush_active": int(rush_row["cnt"] or 0) if rush_row else 0,
        }
    except Error:
        return {"avg_prep_time": 0, "in_progress": 0, "completed_today": 0, "rush_active": 0}
```

## 6. ReportsPage._build_report

```python
def _build_report(self) -> str:
    stats = self.store.get_kitchen_stats() if hasattr(self.store, "get_kitchen_stats") else {}
    orders = self.store.get_active_orders_for_kitchen() if hasattr(self.store, "get_active_orders_for_kitchen") else []
    history = self.store.get_order_history(limit=50) if hasattr(self.store, "get_order_history") else []

    lines = [
        "ОТЧЁТ КУХНИ GASTROSoft",
        f"Дата: {datetime.now():%d.%m.%Y %H:%M}",
        "",
        "=== СТАТИСТИКА ===",
        f"Среднее время приготовления: {stats.get('avg_prep_time', 0)} мин",
        f"Заказов в работе: {stats.get('in_progress', 0)}",
        f"Выполнено за сегодня: {stats.get('completed_today', 0)}",
        f"Срочных заказов: {stats.get('rush_active', 0)}",
        "",
        "=== АКТИВНЫЕ ЗАКАЗЫ ===",
    ]

    if orders:
        for order in orders:
            priority = " [СРОЧНО]" if order.get("priority") == "rush" else ""
            cook = f" (повар: {order['cook_name']})" if order.get("cook_name") else ""
            lines.append(f"  {order['order_no']} — Стол {order['table']} — {order['status']}{priority}{cook}")
    else:
        lines.append("  Нет активных заказов")

    return "\n".join(lines)
```
