from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..style_utils import load_style
from ..widgets import MetricCard, SectionCard, StatusPill, apply_button_variant


class DashboardPage(QWidget):
    navigate_requested = Signal(str)
    status_message = Signal(str)

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.setObjectName("dashboardPage")
        self.setStyleSheet(load_style("styles", "dashboard", "style.css"))
        self.metric_cards: dict[str, MetricCard] = {}
        self._build_ui()
        self.refresh_page()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(16)
        metrics_layout.setVerticalSpacing(16)
        for index, (key, title, note) in enumerate(
            [
                ("revenue", "Выручка за день", "По закрытым операциям текущей смены"),
                ("orders", "Заказов оформлено", "Включая зал и take-away"),
                ("reservations", "Активные брони", "С учетом подтвержденных и ожидаемых"),
                ("low_stock", "Проблемные остатки", "Позиции ниже минимального порога"),
            ]
        ):
            card = MetricCard(title, "0", note)
            self.metric_cards[key] = card
            metrics_layout.addWidget(card, index // 2, index % 2)
        root_layout.addLayout(metrics_layout)

        kitchen_metrics = QHBoxLayout()
        kitchen_metrics.setSpacing(16)
        for key, title, note in [
            ("kitchen_avg", "Среднее время", "Приготовления блюда за сегодня"),
            ("kitchen_active", "На кухне", "Заказов в работе сейчас"),
        ]:
            card = MetricCard(title, "0", note)
            self.metric_cards[key] = card
            kitchen_metrics.addWidget(card)
        kitchen_metrics.addStretch(1)
        root_layout.addLayout(kitchen_metrics)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(18)

        sales_card = SectionCard("Продажи по часам", "Макет оперативного графика на день.")
        self.sales_chart_view = QChartView()
        self.sales_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        sales_card.content_layout.addWidget(self.sales_chart_view)
        charts_layout.addWidget(sales_card, 7)

        popular_card = SectionCard("Популярные позиции", "Топ блюд и напитков текущей смены.")
        self.popular_chart_view = QChartView()
        self.popular_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        popular_card.content_layout.addWidget(self.popular_chart_view)
        charts_layout.addWidget(popular_card, 5)

        root_layout.addLayout(charts_layout, 1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        actions_card = SectionCard("Быстрые действия", "Кнопки переводят на отдельные прототипы страниц.")
        action_grid = QGridLayout()
        action_grid.setHorizontalSpacing(12)
        action_grid.setVerticalSpacing(12)
        for index, (title, page_key, variant) in enumerate(
            [
                ("Открыть смены", "staff", "primary"),
                ("Открыть брони", "reservations", "secondary"),
                ("Открыть заказы", "orders", "warning"),
                ("Открыть кухню", "kitchen", "danger"),
                ("Открыть склад", "inventory", "ghost"),
            ]
        ):
            button = QPushButton(title)
            apply_button_variant(button, variant)
            button.clicked.connect(lambda checked=False, key=page_key: self.navigate_requested.emit(key))
            action_grid.addWidget(button, index // 3, index % 3)
        actions_card.content_layout.addLayout(action_grid)

        refresh_button = QPushButton("Обновить показатели")
        apply_button_variant(refresh_button, "primary")
        refresh_button.clicked.connect(self.refresh_dashboard)
        actions_card.content_layout.addWidget(refresh_button)

        bottom_layout.addWidget(actions_card, 5)

        alerts_card = SectionCard("Предупреждения и статусы", "Блок низких остатков и организационных рисков.")
        self.alerts_list = QListWidget()
        alerts_card.content_layout.addWidget(self.alerts_list)

        self.draft_status = StatusPill("Черновик заказа: 0 ₽", "info")
        alerts_card.content_layout.addWidget(self.draft_status)
        bottom_layout.addWidget(alerts_card, 5)

        root_layout.addLayout(bottom_layout)

    def refresh_dashboard(self) -> None:
        self.store.refresh_dashboard()
        self.refresh_page()
        self.status_message.emit("Данные главной панели обновлены.")

    def refresh_page(self) -> None:
        metrics = self.store.metrics()
        self.metric_cards["revenue"].set_value(metrics["revenue"], "Сводка по оплатам и закрытым чекам")
        self.metric_cards["orders"].set_value(metrics["orders"], "Заказы по всем активным зонам")
        self.metric_cards["reservations"].set_value(metrics["reservations"], "Ожидаемые и подтвержденные гости")
        self.metric_cards["low_stock"].set_value(metrics["low_stock"], "Требуют внимания менеджера или кухни")

        if hasattr(self.store, "get_kitchen_stats"):
            k_stats = self.store.get_kitchen_stats()
            avg_time = k_stats.get("avg_prep_time", 0)
            in_progress = k_stats.get("in_progress", 0)
            self.metric_cards["kitchen_avg"].set_value(f"{avg_time} мин", "Среднее время приготовления")
            self.metric_cards["kitchen_active"].set_value(str(in_progress), "Заказов в работе на кухне")
        else:
            self.metric_cards["kitchen_avg"].set_value("--", "Нет данных о кухне")
            self.metric_cards["kitchen_active"].set_value("--", "Нет данных о кухне")

        self.draft_status.set_state(f"Черновик заказа: {metrics['draft_total']}", "info")

        self.alerts_list.clear()
        self.alerts_list.addItems(self.store.alerts)

        self.sales_chart_view.setChart(self._build_sales_chart())
        self.popular_chart_view.setChart(self._build_popular_chart())

    def _build_sales_chart(self) -> QChart:
        chart = QChart()
        chart.setTitle("Дневная выручка по интервалам")
        series = QLineSeries()
        series.setPen(QPen(QColor("#1F686E"), 3))
        series.setPointsVisible(True)
        for index, value in enumerate(self.store.sales_by_hour, start=1):
            series.append(index, value)
        chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setRange(1, len(self.store.sales_by_hour))
        axis_x.setTickCount(len(self.store.sales_by_hour))
        axis_x.setLabelFormat("%d")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(self.store.sales_by_hour) + 10)
        axis_y.setTickCount(6)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        return chart

    def _build_popular_chart(self) -> QChart:
        chart = QChart()
        chart.setTitle("Популярность меню")
        bar_set = QBarSet("Количество")
        bar_set.setColor(QColor("#1F686E"))
        categories = list(self.store.top_dishes.keys())
        for value in self.store.top_dishes.values():
            bar_set.append(value)

        series = QBarSeries()
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(self.store.top_dishes.values()) + 10)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        chart.legend().hide()
        chart.setBackgroundVisible(False)
        return chart
