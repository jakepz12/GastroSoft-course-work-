from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


def apply_button_variant(button: QPushButton, variant: str = "primary") -> None:
    button.setProperty("variant", variant)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.style().unpolish(button)
    button.style().polish(button)


class SectionCard(QFrame):
    def __init__(self, title: str = "", subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("sectionCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("sectionCardTitle")
            layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("sectionCardSubtitle")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        layout.addLayout(self.content_layout)


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, note: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        layout.addWidget(self.value_label)

        self.note_label = QLabel(note)
        self.note_label.setObjectName("metricNote")
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

    def set_value(self, value: str, note: str | None = None) -> None:
        self.value_label.setText(value)
        if note is not None:
            self.note_label.setText(note)


class StatusPill(QLabel):
    def __init__(self, text: str, tone: str = "info") -> None:
        super().__init__(text)
        self.setObjectName("statusPill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(30)
        self.set_state(text, tone)

    def set_state(self, text: str, tone: str = "info") -> None:
        self.setText(text)
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


def tint_table_item(item, tone: str) -> None:
    palette = {
        "success": ("#0F766E", "#CCFBF1"),
        "warning": ("#B45309", "#FEF3C7"),
        "danger": ("#991B1B", "#FEE2E2"),
        "info": ("#1F686E", "#D8F0F1"),
        "muted": ("#475569", "#E2E8F0"),
    }
    foreground, background = palette.get(tone, palette["muted"])
    item.setForeground(QColor(foreground))
    item.setBackground(QColor(background))
