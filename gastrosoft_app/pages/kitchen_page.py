from datetime import datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..role_access import can_manage_kitchen, can_cancel_orders, is_chef_role
from ..style_utils import load_style
from ..widgets import MetricCard, StatusPill, apply_button_variant


KITCHEN_FILTERS = ["Все активные", "Принят", "Готовится", "Готов"]


class KitchenPage(QWidget):
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.setObjectName("kitchenPage")
        self.setStyleSheet(load_style("styles", "kitchen", "style.css"))
        self.summary_cards: dict[str, MetricCard] = {}
        self._prev_order_count = 0
        self._flash_active = False

        self.timer_refresh = QTimer(self)
        self.timer_refresh.timeout.connect(self._auto_refresh)
        self.timer_refresh.start(30000)

        self.timer_notify = QTimer(self)
        self.timer_notify.timeout.connect(self._check_new_orders)
        self.timer_notify.start(10000)

        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self.title_label = QLabel("Кухонная очередь")
        self.title_label.setObjectName("kitchenTitle")
        top_bar.addWidget(self.title_label)
        top_bar.addStretch(1)

        for key, title_text, note in [
            ("accepted", "Принято", "Ожидают начала"),
            ("preparing", "Готовятся", "В работе"),
            ("ready", "Готово", "Выдать гостю"),
        ]:
            card = MetricCard(title_text, "0", note)
            self.summary_cards[key] = card
            top_bar.addWidget(card)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(KITCHEN_FILTERS)
        self.filter_combo.currentTextChanged.connect(lambda _: self._populate_orders())
        top_bar.addWidget(self.filter_combo)

        refresh_btn = QPushButton("Обновить")
        apply_button_variant(refresh_btn, "secondary")
        refresh_btn.clicked.connect(self.refresh_page)
        top_bar.addWidget(refresh_btn)

        root_layout.addLayout(top_bar)

        self.stats_bar = QHBoxLayout()
        self.stats_bar.setSpacing(14)

        self.avg_time_label = QLabel("Среднее время: -- мин")
        self.avg_time_label.setObjectName("kitchenStatLabel")
        self.stats_bar.addWidget(self.avg_time_label)

        self.rush_label = QLabel("")
        self.rush_label.setObjectName("kitchenRushLabel")
        self.rush_label.setVisible(False)
        self.stats_bar.addWidget(self.rush_label)
        self.stats_bar.addStretch(1)

        self.cook_label = QLabel("Повар:")
        self.cook_combo = QComboBox()
        self.cook_combo.setMinimumWidth(200)
        self.stats_bar.addWidget(self.cook_label)
        self.stats_bar.addWidget(self.cook_combo)
        self.cook_label.setVisible(False)
        self.cook_combo.setVisible(False)

        root_layout.addLayout(self.stats_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.viewport().setStyleSheet("background-color: #F8FAFC;")
        self.orders_container = QWidget()
        self.orders_container.setStyleSheet("background-color: transparent;")
        self.orders_layout = QVBoxLayout(self.orders_container)
        self.orders_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout.setSpacing(10)
        self.orders_layout.addStretch(1)
        scroll.setWidget(self.orders_container)
        root_layout.addWidget(scroll, 1)

        self.empty_label = QLabel("Нет активных заказов на кухне.\nЗаказы появятся, когда официант передаст их на кухню.")
        self.empty_label.setObjectName("kitchenEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def refresh_page(self) -> None:
        if hasattr(self.store, "reload_from_mysql") and getattr(self.store, "mysql_enabled", False):
            self.store.reload_from_mysql()
        self._setup_role()
        self._load_cooks()
        self._populate_orders()
        self._refresh_stats()
        self._prev_order_count = len(self.store.kitchen_queue)

    def _setup_role(self) -> None:
        role = self._current_role()
        is_ch = is_chef_role(role)
        self.cook_label.setVisible(is_ch)
        self.cook_combo.setVisible(is_ch)

        if role == "Повар":
            items = ["Все активные", "Мои заказы"]
            current = self.filter_combo.currentText()
            self.filter_combo.blockSignals(True)
            self.filter_combo.clear()
            self.filter_combo.addItems(items)
            if current in items:
                self.filter_combo.setCurrentText(current)
            self.filter_combo.blockSignals(False)
        else:
            current = self.filter_combo.currentText()
            self.filter_combo.blockSignals(True)
            self.filter_combo.clear()
            self.filter_combo.addItems(KITCHEN_FILTERS)
            if current in KITCHEN_FILTERS:
                self.filter_combo.setCurrentText(current)
            self.filter_combo.blockSignals(False)

    def _load_cooks(self) -> None:
        if not is_chef_role(self._current_role()):
            return
        cooks = self.store.get_cooks() if hasattr(self.store, "get_cooks") else []
        prev = self.cook_combo.currentData()
        self.cook_combo.clear()
        for cook in cooks:
            self.cook_combo.addItem(cook["name"], cook["id"])
        if prev is not None:
            idx = self.cook_combo.findData(prev)
            if idx >= 0:
                self.cook_combo.setCurrentIndex(idx)

    def _auto_refresh(self) -> None:
        if hasattr(self.store, "reload_from_mysql") and getattr(self.store, "mysql_enabled", False):
            self.store.reload_from_mysql()
        self._populate_orders()
        self._refresh_stats()

    def _check_new_orders(self) -> None:
        current_count = len(self.store.kitchen_queue)
        if current_count > self._prev_order_count and self._prev_order_count > 0:
            self._flash_new_order()
        self._prev_order_count = current_count

    def _flash_new_order(self) -> None:
        self.title_label.setText("Кухонная очередь — НОВЫЙ ЗАКАЗ!")
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: 700; color: #DC2626;")
        QTimer.singleShot(3000, self._reset_title)

    def _reset_title(self) -> None:
        self.title_label.setText("Кухонная очередь")
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: 700; color: #1E293B;")

    def _populate_orders(self) -> None:
        self.empty_label.setParent(None)

        for i in range(self.orders_layout.count() - 1, -1, -1):
            item = self.orders_layout.itemAt(i)
            w = item.widget() if item else None
            if w:
                w.setParent(None)
                w.deleteLater()

        orders = self.store.get_active_orders_for_kitchen() if hasattr(self.store, "get_active_orders_for_kitchen") else self.store.kitchen_queue

        selected_status = self.filter_combo.currentText()
        role = self._current_role()
        user = self.store.current_user or {}

        filtered = []
        for order in orders:
            status = order.get("status", "")
            if selected_status != "Все активные" and selected_status != "Мои заказы" and status != selected_status:
                continue
            if selected_status == "Мои заказы":
                if order.get("cook_name") != user.get("full_name", ""):
                    continue
            filtered.append(order)

        if not filtered:
            self.orders_layout.addWidget(self.empty_label)
            self.empty_label.setVisible(True)
        else:
            self.empty_label.setVisible(False)

        counts = {"Принят": 0, "Готовится": 0, "Готов": 0}
        for order in orders:
            s = order.get("status", "")
            if s in counts:
                counts[s] += 1

        self.summary_cards["accepted"].set_value(str(counts["Принят"]), "Ожидают начала")
        self.summary_cards["preparing"].set_value(str(counts["Готовится"]), "В работе")
        self.summary_cards["ready"].set_value(str(counts["Готов"]), "Выдать гостю")

        for order in filtered:
            card = self._build_order_card(order)
            self.orders_layout.addWidget(card)

        self.orders_layout.addStretch(1)

    def _build_order_card(self, order: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("kitchenOrderCard")
        is_rush = order.get("priority") == "rush"
        if is_rush:
            card.setProperty("rush", True)

        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QFrame()
        inner.setObjectName("kitchenCardInner")
        if is_rush:
            inner.setProperty("rush", True)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(10)

        order_no = QLabel(order.get("order_no", "GS-?"))
        order_no.setObjectName("kitchenOrderNo")
        header.addWidget(order_no)

        table_label = QLabel(f"Стол {order.get('table', '-')}")
        table_label.setObjectName("kitchenTableLabel")
        header.addWidget(table_label)

        if is_rush:
            rush_pill = StatusPill("СРОЧНО", "danger")
            rush_pill.setFixedHeight(22)
            header.addWidget(rush_pill)

        header.addStretch(1)

        timer_text = self._calc_timer(order)
        timer_label = QLabel(timer_text)
        timer_label.setObjectName("kitchenTimer")
        timer_label.setProperty("timer_color", self._timer_color(order))
        header.addWidget(timer_label)

        status = order.get("status", "")
        status_pill = StatusPill(status, self._status_tone(status))
        header.addWidget(status_pill)

        layout.addLayout(header)

        if order.get("cook_name"):
            cook_label = QLabel(f"Повар: {order['cook_name']}")
            cook_label.setObjectName("kitchenCookLabel")
            layout.addWidget(cook_label)

        items = order.get("items", [])
        if isinstance(items, list) and items:
            for item in items:
                item_row = QHBoxLayout()
                item_row.setSpacing(8)

                item_status = item.get("status", "")
                dot = QLabel("●")
                dot.setObjectName("kitchenItemDot")
                dot.setProperty("dot_color", self._item_dot_color(item_status))
                dot.setFixedWidth(16)
                item_row.addWidget(dot)

                name_text = f"{item.get('dish', '?')} x{item.get('quantity', 1)}"
                name_label = QLabel(name_text)
                name_label.setObjectName("kitchenItemName")
                if item_status in ("READY", "SERVED"):
                    name_label.setProperty("done", True)
                item_row.addWidget(name_label, 1)

                item_status_label = QLabel(item_status)
                item_status_label.setObjectName("kitchenItemStatus")
                item_row.addWidget(item_status_label)

                if item.get("note"):
                    note_label = QLabel(item["note"])
                    note_label.setObjectName("kitchenItemNote")
                    item_row.addWidget(note_label)

                layout.addLayout(item_row)
        elif isinstance(items, str) and items:
            items_label = QLabel(items)
            items_label.setObjectName("kitchenItemsText")
            layout.addWidget(items_label)

        total = order.get("total", 0)
        total_label = QLabel(f"Итого: {total:,} \u20bd".replace(",", " "))
        total_label.setObjectName("kitchenTotalLabel")
        layout.addWidget(total_label)

        actions_frame = QFrame()
        actions_frame.setObjectName("kitchenActionsFrame")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(12, 8, 12, 8)
        actions_layout.setSpacing(8)

        order_id = order.get("order_id")

        if is_chef_role(self._current_role()):
            assign_btn = QPushButton("Назначить повара")
            apply_button_variant(assign_btn, "secondary")
            assign_btn.clicked.connect(lambda _, oid=order_id: self._assign_cook(oid))
            actions_layout.addWidget(assign_btn)

            if not is_rush:
                rush_btn = QPushButton("Срочно")
                apply_button_variant(rush_btn, "danger")
                rush_btn.clicked.connect(lambda _, oid=order_id: self._set_rush(oid))
                actions_layout.addWidget(rush_btn)
            else:
                unrush_btn = QPushButton("Обычный")
                apply_button_variant(unrush_btn, "secondary")
                unrush_btn.clicked.connect(lambda _, oid=order_id: self._set_normal(oid))
                actions_layout.addWidget(unrush_btn)

        if can_manage_kitchen(self._current_role()):
            status_code = order.get("status_code", "")
            if status_code in ("ACCEPTED", "NEW"):
                start_btn = QPushButton("Взять в работу")
                apply_button_variant(start_btn, "warning")
                start_btn.clicked.connect(lambda _, oid=order_id: self._start_order(oid))
                actions_layout.addWidget(start_btn)
            elif status_code == "PREPARING" and isinstance(items, list):
                for item in items:
                    if item.get("status_code") not in ("READY", "SERVED", "CANCELLED"):
                        ready_btn = QPushButton(f"Готово: {item.get('dish', '?')}")
                        apply_button_variant(ready_btn, "success")
                        ready_btn.clicked.connect(lambda _, iid=item.get("item_id"): self._mark_item_ready(iid))
                        actions_layout.addWidget(ready_btn)
                        break

        if can_cancel_orders(self._current_role()):
            cancel_btn = QPushButton("Отменить")
            apply_button_variant(cancel_btn, "danger")
            cancel_btn.clicked.connect(lambda _, oid=order_id: self._cancel_order(oid))
            actions_layout.addWidget(cancel_btn)

        actions_layout.addStretch(1)
        layout.addWidget(actions_frame)

        outer.addWidget(inner)
        return card

    def _calc_timer(self, order: dict) -> str:
        started = order.get("started_at")
        created = order.get("created", "")
        now = datetime.now()

        if started and isinstance(started, datetime):
            delta = now - started
        elif created and ":" in created:
            try:
                parts = created.split(":")
                h, m = int(parts[0]), int(parts[1])
                order_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if order_time > now:
                    order_time = order_time.replace(day=order_time.day - 1)
                delta = now - order_time
            except (ValueError, IndexError):
                return created
        else:
            return created or "--"

        minutes = int(delta.total_seconds() // 60)
        if minutes < 60:
            return f"{minutes} мин"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}ч {mins}м"

    def _timer_color(self, order: dict) -> str:
        started = order.get("started_at")
        now = datetime.now()

        if started and isinstance(started, datetime):
            minutes = int((now - started).total_seconds() // 60)
        else:
            return "normal"

        if minutes < 10:
            return "fast"
        elif minutes < 20:
            return "medium"
        return "slow"

    def _status_tone(self, status: str) -> str:
        return {
            "Принят": "warning",
            "Готовится": "info",
            "Готов": "success",
            "Выдан": "muted",
        }.get(status, "info")

    def _item_dot_color(self, status: str) -> str:
        return {
            "В очереди": "gray",
            "Готовится": "blue",
            "Готово": "green",
            "Подано": "gray",
        }.get(status, "gray")

    def _refresh_stats(self) -> None:
        if hasattr(self.store, "get_kitchen_stats"):
            stats = self.store.get_kitchen_stats()
            avg = stats.get("avg_prep_time", 0)
            rush = stats.get("rush_active", 0)
            self.avg_time_label.setText(f"Среднее время: {avg} мин")
            if rush > 0:
                self.rush_label.setText(f"\u26a0 Срочных: {rush}")
                self.rush_label.setVisible(True)
            else:
                self.rush_label.setVisible(False)

    def _assign_cook(self, order_id: int) -> None:
        cook_id = self.cook_combo.currentData()
        if cook_id is None:
            self.status_message.emit("Выбери повара из списка.")
            return
        message = self.store.assign_cook_to_order(order_id, cook_id)
        self.store.log_kitchen_action(order_id, "COOK_ASSIGNED")
        self.refresh_page()
        self.status_message.emit(message)

    def _set_rush(self, order_id: int) -> None:
        message = self.store.set_order_priority(order_id, "rush")
        self.store.log_kitchen_action(order_id, "PRIORITY_SET", "rush")
        self.refresh_page()
        self.status_message.emit(message)

    def _set_normal(self, order_id: int) -> None:
        message = self.store.set_order_priority(order_id, "normal")
        self.store.log_kitchen_action(order_id, "PRIORITY_SET", "normal")
        self.refresh_page()
        self.status_message.emit(message)

    def _start_order(self, order_id: int) -> None:
        message = self.store.start_order(order_id)
        self.store.log_kitchen_action(order_id, "STARTED")
        self.refresh_page()
        self.status_message.emit(message)

    def _mark_item_ready(self, item_id: int) -> None:
        message = self.store.mark_item_ready(item_id)
        self.refresh_page()
        self.status_message.emit(message)

    def _cancel_order(self, order_id: int) -> None:
        message = self.store.cancel_order(order_id)
        self.refresh_page()
        self.status_message.emit(message)

    def _current_role(self) -> str | None:
        user = self.store.current_user or {}
        return user.get("role")
