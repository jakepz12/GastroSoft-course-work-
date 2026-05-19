# Код функций кухонного модуля

Листинги подготовлены для приложения к пояснительной записке. Код приведён без окружающих классов, чтобы его было удобно переносить на скриншоты.

## 1. OrdersPage.apply_role_mode

Файл: `gastrosoft_app/pages/orders_page.py`

```python
def apply_role_mode(self) -> None:
    role = self._current_role()
    can_create = can_create_orders(role)
    is_kitchen = can_process_kitchen(role)
    can_close = can_close_orders(role)
    show_order_list = is_kitchen or can_close

    self.menu_card.setVisible(can_create)
    self.order_card.setVisible(can_create)
    self.kitchen_card.setVisible(show_order_list)
    self.kitchen_controls.setVisible(is_kitchen)
    self.next_status_button.setVisible(is_kitchen)
    self.close_order_button.setVisible(can_close)

    if is_kitchen:
        self.kitchen_card.set_header("Кухонная очередь", "Повар и шеф-повар меняют только статусы приготовления.")
        self.next_status_button.setText("Взять в работу")
    elif can_close:
        self.kitchen_card.set_header("Заказы к оплате", "Кассир закрывает готовые и выданные заказы.")
    else:
        self.kitchen_card.set_header("Очередь заказов", "Просмотр заказов текущей смены.")
```

## 2. OrdersPage._filtered_queue_indices

Файл: `gastrosoft_app/pages/orders_page.py`

```python
def _filtered_queue_indices(self) -> list[int]:
    selected_status = self.kitchen_filter.currentText()
    indices = []
    role = self._current_role()
    for index, item in enumerate(self.store.kitchen_queue):
        status = item["status"]
        if can_process_kitchen(role) and status not in KITCHEN_ACTIVE_STATUSES:
            continue
        if can_process_kitchen(role) and selected_status != "Все активные" and status != selected_status:
            continue
        if role == "Кассир" and status not in CASHIER_VISIBLE_STATUSES:
            continue
        indices.append(index)
    return indices
```

## 3. OrdersPage.populate_kitchen

Файл: `gastrosoft_app/pages/orders_page.py`

```python
def populate_kitchen(self) -> None:
    role = self._current_role()
    is_kitchen = can_process_kitchen(role)
    headers = (
        ["Номер", "Стол", "Время", "Состав заказа", "Статус"]
        if is_kitchen
        else ["Номер", "Стол", "Время", "Состав", "Статус"]
    )
    self.kitchen_table.setColumnCount(len(headers))
    self.kitchen_table.setHorizontalHeaderLabels(headers)
    self.kitchen_table.verticalHeader().setDefaultSectionSize(58 if is_kitchen else 34)

    self.visible_queue_indices = self._filtered_queue_indices()
    self.kitchen_table.setRowCount(len(self.visible_queue_indices))
    for row_index, queue_index in enumerate(self.visible_queue_indices):
        queue_item = self.store.kitchen_queue[queue_index]
        values = (
            [
                queue_item["order_no"],
                queue_item["table"],
                queue_item.get("created", "-"),
                queue_item["items"],
                queue_item["status"],
            ]
            if is_kitchen
            else [
                queue_item["order_no"],
                queue_item["table"],
                queue_item.get("created", "-"),
                queue_item["items"],
                queue_item["status"],
            ]
        )
        for column_index, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setToolTip(str(value))
            if column_index == len(headers) - 1:
                tone = "warning"
                if value == "Готов":
                    tone = "success"
                elif value == "Выдан":
                    tone = "muted"
                elif value == "Готовится":
                    tone = "info"
                tint_table_item(item, tone)
            self.kitchen_table.setItem(row_index, column_index, item)
    if self.visible_queue_indices:
        self.kitchen_table.selectRow(0)

    self.update_kitchen_summary()
    self.update_kitchen_actions()
```

## 4. OrdersPage.update_kitchen_summary

Файл: `gastrosoft_app/pages/orders_page.py`

```python
def update_kitchen_summary(self) -> None:
    counts = {
        status: len([item for item in self.store.kitchen_queue if item["status"] == status])
        for status in KITCHEN_ACTIVE_STATUSES
    }
    self.summary_pills["accepted"].set_state(f"Принято: {counts['Принят']}", "warning")
    self.summary_pills["preparing"].set_state(f"В работе: {counts['Готовится']}", "info")
    self.summary_pills["ready"].set_state(f"Готово: {counts['Готов']}", "success")
```

## 5. OrdersPage.update_kitchen_actions

Файл: `gastrosoft_app/pages/orders_page.py`

```python
def update_kitchen_actions(self) -> None:
    role = self._current_role()
    if not can_process_kitchen(role):
        self.next_status_button.setEnabled(False)
        self.close_order_button.setEnabled(self._selected_queue_index() >= 0 and can_close_orders(role))
        return

    queue_index = self._selected_queue_index()
    if queue_index < 0:
        self.next_status_button.setText("Выбери заказ")
        self.next_status_button.setEnabled(False)
        return

    status = self.store.kitchen_queue[queue_index]["status"]
    next_actions = {
        "Принят": ("Взять в работу", True),
        "Готовится": ("Отметить готовым", True),
        "Готов": ("Заказ готов", False),
        "Выдан": ("Уже выдан", False),
    }
    text, enabled = next_actions.get(status, ("Следующий этап", True))
    self.next_status_button.setText(text)
    self.next_status_button.setEnabled(enabled)
```

## 6. MySQLBackedStore.advance_kitchen_order

Файл: `gastrosoft_app/mysql_store.py`

```python
def advance_kitchen_order(self, index: int) -> str:
    if not self.mysql_enabled or index < 0 or index >= len(self.kitchen_queue):
        return "MySQL не подключен или заказ не выбран."

    order = self.kitchen_queue[index]
    current_code = ORDER_STATUS_TO_CODE.get(order["status"], "ACCEPTED")
    if current_code == "READY":
        return "Заказ уже отмечен как готовый."
    if current_code in {"SERVED", "CLOSED"}:
        return "Заказ уже выдан или закрыт."

    next_code = "READY" if current_code == "PREPARING" else "PREPARING"
    return self._set_order_status(order, next_code)
```
