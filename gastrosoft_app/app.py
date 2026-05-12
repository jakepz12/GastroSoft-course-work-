import sys

from PySide6.QtWidgets import QApplication

from .shell import GastroSoftWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GastroSoft")

    window = GastroSoftWindow()
    window.show()
    return app.exec()
