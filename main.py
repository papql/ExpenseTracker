# Running the App
import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from app import ExpenseApp
from database import init_db


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "expenses.db")
    style_path = os.path.join(base_dir, "style.qss")

    if not init_db(db_path):
        QMessageBox.critical(None, "Error", "Unable to load the expense database.")
        sys.exit(1)

    if not os.path.exists(style_path):
        QMessageBox.critical(None, "Style Error", f"Missing stylesheet:\n{style_path}")
        sys.exit(1)

    with open(style_path, "r", encoding="utf-8") as style_file:
        app.setStyleSheet(style_file.read())

    window = ExpenseApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
