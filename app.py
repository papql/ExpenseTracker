# App Design

import calendar
import math
from pathlib import Path

from PyQt6.QtCore import QDate, QEvent, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import (
    FALLBACK_CATEGORY_COLOR,
    add_category,
    add_expense,
    delete_category,
    delete_expense,
    fetch_categories,
    fetch_category_totals,
    fetch_expenses,
    fetch_month_totals,
    fetch_years,
    update_category_color,
    update_expense,
)

PALETTE = {
    "deep_teal": "#2E6C76",
    "mint": "#92C3BE",
    "ice": "#EFF6F9",
    "blush": "#FADED4",
    "coral": "#D7997D",
}


class ExpenseDelegate(QStyledItemDelegate):
    """Creates efficient cell editors for Category, Amount, and Date."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

    def createEditor(self, parent, option, index):
        column = index.column()

        if column == 1:  # Category
            editor = QComboBox(parent)
            for name, _is_default, color in fetch_categories():
                editor.addItem(self.app.color_icon(color), name)
            return editor

        if column == 2:  # Amount
            editor = QDoubleSpinBox(parent)
            editor.setPrefix("$ ")
            editor.setDecimals(2)
            editor.setRange(0, 999999999.99)
            editor.setSingleStep(1.00)
            return editor

        if column == 3:  # Date
            editor = QDateEdit(parent)
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
            return editor

        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        text = str(index.data() or "")
        column = index.column()

        if column == 1:
            idx = editor.findText(text)
            if idx >= 0:
                editor.setCurrentIndex(idx)
        elif column == 2:
            editor.setValue(self.app.parse_amount(text))
        elif column == 3:
            date = QDate.fromString(text, "yyyy-MM-dd")
            editor.setDate(date if date.isValid() else QDate.currentDate())
        else:
            editor.setText(text)

    def setModelData(self, editor, model, index):
        column = index.column()

        if column == 1:
            model.setData(index, editor.currentText())
        elif column == 2:
            model.setData(index, f"${editor.value():,.2f}")
        elif column == 3:
            model.setData(index, editor.date().toString("yyyy-MM-dd"))
        else:
            model.setData(index, editor.text())


class BarChartWidget(QWidget):
    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.values = values
        self.setMinimumSize(720, 420)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PALETTE["ice"]))

        left, top, right, bottom = 70, 35, 25, 65
        chart_w = max(1, self.width() - left - right)
        chart_h = max(1, self.height() - top - bottom)
        baseline = top + chart_h

        painter.setPen(QPen(QColor(PALETTE["deep_teal"]), 2))
        painter.drawLine(left, top, left, baseline)
        painter.drawLine(left, baseline, left + chart_w, baseline)

        max_value = max([value for _label, value in self.values] + [1.0])
        slot = chart_w / max(1, len(self.values))
        bar_w = slot * 0.58

        for i, (label, value) in enumerate(self.values):
            height = (value / max_value) * (chart_h * 0.82) if max_value else 0
            x = left + i * slot + (slot - bar_w) / 2
            y = baseline - height

            painter.setBrush(QColor(PALETTE["mint"]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_w, height), 5, 5)

            painter.setPen(QColor(PALETTE["deep_teal"]))
            painter.drawText(
                QRectF(left + i * slot, baseline + 8, slot, 24),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

            if value > 0:
                painter.drawText(
                    QRectF(x - 12, max(top, y - 24), bar_w + 24, 20),
                    Qt.AlignmentFlag.AlignCenter,
                    f"${value:,.0f}",
                )


class PieChartWidget(QWidget):
    def __init__(self, values, parent=None):
        super().__init__(parent)
        self.values = values
        self.setMinimumSize(720, 440)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PALETTE["ice"]))

        positive = [(name, total, color) for name, total, color in self.values if total > 0]
        total_sum = sum(total for _name, total, _color in positive)

        if total_sum <= 0:
            painter.setPen(QColor(PALETTE["deep_teal"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No spending for this year yet.")
            return

        size = min(self.height() - 90, self.width() * 0.48)
        pie_rect = QRectF(40, 45, size, size)
        start_angle = 90 * 16

        for name, total, color in positive:
            span = int((total / total_sum) * 360 * 16)
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor(PALETTE["ice"]), 2))
            painter.drawPie(pie_rect, start_angle, -span)
            start_angle -= span

        legend_x = pie_rect.right() + 45
        legend_y = 55
        painter.setPen(QColor(PALETTE["deep_teal"]))

        for i, (name, total, color) in enumerate(positive):
            y = legend_y + i * 34
            painter.fillRect(int(legend_x), int(y), 18, 18, QColor(color))
            painter.drawText(
                QRectF(legend_x + 28, y - 2, self.width() - legend_x - 40, 24),
                Qt.AlignmentFlag.AlignVCenter,
                f"{name}: ${total:,.2f}",
            )


class ChartDialog(QDialog):
    def __init__(self, title, chart_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(780, 520)

        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setObjectName("chartTitle")
        layout.addWidget(title_label)
        layout.addWidget(chart_widget, 1)


class ExpenseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.loading_table = False
        self.settings()
        self.init_ui()
        self.load_categories()
        self.load_table_data()
        self.refresh_year_selector()
        self.refresh_summaries()

    def settings(self):
        self.setObjectName("ExpenseApp")
        self.setWindowTitle("Expense Tracker")
        self.resize(1255, 795)
        self.setMinimumSize(1180, 740)

    def init_ui(self):
        # ---------- Input widgets ----------
        self.item = QLineEdit()
        self.item.setPlaceholderText("e.g. Five Guys")

        self.amount = QDoubleSpinBox()
        self.amount.setPrefix("$ ")
        self.amount.setDecimals(2)
        self.amount.setRange(0, 999999999.99)
        self.amount.setSingleStep(1.00)

        self.date_box = QDateEdit()
        self.date_box.setDate(QDate.currentDate())
        self.date_box.setDisplayFormat("yyyy-MM-dd")
        self.date_box.setCalendarPopup(True)

        self.note = QLineEdit()
        self.note.setPlaceholderText("Optional note")

        self.dropdown = QComboBox()

        self.btn_add_category = QPushButton("Add Category")
        self.btn_remove_category = QPushButton("Delete Category")
        self.btn_color_category = QPushButton("Category Color")
        self.btn_color_category.setObjectName("colorWheelButton")
        self.btn_color_category.setIcon(QIcon(str(Path(__file__).resolve().parent / "color_wheel.png")))
        self.btn_color_category.setIconSize(QSize(20, 20))
        self.btn_color_category.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_color_category.setToolTip("Choose a color for the selected category")

        self.btn_add = QPushButton("Add Expense")
        self.btn_add.setObjectName("primaryButton")
        self.btn_delete = QPushButton("Delete Expense")
        self.btn_delete.setObjectName("dangerButton")

        # ---------- Main expense table ----------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Item", "Category", "Amount", "Date", "Note"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.table.setItemDelegate(ExpenseDelegate(self, self.table))
        self.table.installEventFilter(self)

        # ---------- Monthly summary ----------
        self.year_selector = QComboBox()
        self.month_graph_button = QPushButton("")
        self.month_graph_button.setObjectName("monthIconButton")
        self.month_graph_button.setIcon(QIcon(str(Path(__file__).resolve().parent / "month_graph.png")))
        self.month_graph_button.setIconSize(QSize(28, 28))
        self.month_graph_button.setToolTip("Open monthly bar graph")

        self.month_table = QTableWidget(12, 2)
        self.month_table.setHorizontalHeaderLabels(["Month", "Total"])
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.month_table.verticalHeader().setVisible(False)
        self.month_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.month_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.month_table.verticalHeader().setDefaultSectionSize(28)
        self.month_table.setMinimumHeight(148)

        # ---------- Category summary ----------
        self.category_graph_button = QPushButton("◔")
        self.category_graph_button.setObjectName("categoryIconButton")
        self.category_graph_button.setToolTip("Open category pie chart")

        self.category_table = QTableWidget(0, 2)
        self.category_table.setHorizontalHeaderLabels(["Category", "Total"])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.category_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.category_table.verticalHeader().setDefaultSectionSize(28)
        self.category_table.setMinimumHeight(196)
        self.category_table.setIconSize(QSize(16, 16))

        # ---------- Signals ----------
        self.btn_add.clicked.connect(self.add_expense_from_inputs)
        self.btn_delete.clicked.connect(self.delete_selected_expense)
        self.btn_add_category.clicked.connect(self.add_custom_category)
        self.btn_remove_category.clicked.connect(self.remove_category)
        self.btn_color_category.clicked.connect(self.choose_category_color)
        self.table.itemChanged.connect(self.save_inline_edit)
        self.year_selector.currentTextChanged.connect(self.refresh_summaries)
        self.month_graph_button.clicked.connect(self.show_month_graph)
        self.category_graph_button.clicked.connect(self.show_category_graph)

        self.setup_layout()

    def setup_layout(self):
        master = QVBoxLayout(self)
        master.setContentsMargins(14, 10, 14, 14)
        master.setSpacing(12)

        # ---------- Header ----------
        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 12, 14, 12)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        title = QLabel("EXPENSE TRACKER")
        title.setObjectName("mainTitle")
        subtitle = QLabel("A simple view of where your money goes")
        subtitle.setObjectName("mainSubtitle")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)

        header_layout.addLayout(title_group)
        header_layout.addStretch()
        master.addWidget(header)

        # ---------- Entry / controls card ----------
        controls = QFrame()
        controls.setObjectName("controlsCard")
        controls.setFixedHeight(132)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(16, 8, 16, 8)
        controls_layout.setSpacing(24)

        entry_grid = QGridLayout()
        entry_grid.setHorizontalSpacing(14)
        entry_grid.setVerticalSpacing(9)

        item_label = QLabel("Item")
        amount_label = QLabel("Amount")
        date_label = QLabel("Date")
        note_label = QLabel("Note")
        category_label = QLabel("Category")
        for label in (item_label, amount_label, date_label, note_label, category_label):
            label.setObjectName("fieldLabel")

        entry_grid.addWidget(item_label, 0, 0)
        entry_grid.addWidget(self.item, 0, 1, 1, 3)
        entry_grid.addWidget(amount_label, 1, 0)
        entry_grid.addWidget(self.amount, 1, 1)
        entry_grid.addWidget(date_label, 1, 2)
        entry_grid.addWidget(self.date_box, 1, 3)
        entry_grid.addWidget(note_label, 2, 0)
        entry_grid.addWidget(self.note, 2, 1, 1, 3)
        entry_grid.setColumnStretch(1, 1)
        entry_grid.setColumnStretch(3, 1)

        category_panel_frame = QFrame()
        category_panel_frame.setObjectName("categoryControlPanel")
        category_panel = QVBoxLayout(category_panel_frame)
        category_panel.setContentsMargins(10, 6, 10, 6)
        category_panel.setSpacing(5)

        # Match the approved mockup: category selector and category buttons share
        # the first row, followed by colour, then expense actions.
        category_row = QHBoxLayout()
        category_row.setSpacing(6)
        category_row.addWidget(category_label)
        category_row.addWidget(self.dropdown, 3)
        category_row.addWidget(self.btn_add_category, 1)
        category_row.addWidget(self.btn_remove_category, 1)
        category_panel.addLayout(category_row)

        category_panel.addWidget(self.btn_color_category)

        expense_buttons = QHBoxLayout()
        expense_buttons.setSpacing(6)
        expense_buttons.addWidget(self.btn_add)
        expense_buttons.addWidget(self.btn_delete)
        category_panel.addLayout(expense_buttons)

        # Compact action controls so this panel has more breathing room.
        for button in (self.btn_add_category, self.btn_remove_category):
            button.setMaximumHeight(30)
            button.setMinimumHeight(28)
        self.btn_color_category.setMaximumHeight(30)
        self.btn_color_category.setMinimumHeight(28)
        self.btn_add.setMaximumHeight(32)
        self.btn_add.setMinimumHeight(30)
        self.btn_delete.setMaximumHeight(32)
        self.btn_delete.setMinimumHeight(30)

        controls_layout.addLayout(entry_grid, 3)
        controls_layout.addWidget(category_panel_frame, 2)
        master.addWidget(controls)

        # ---------- Main content ----------
        content = QHBoxLayout()
        content.setSpacing(14)

        # Main expenses card
        main_card = QFrame()
        main_card.setObjectName("tableCard")
        main_layout = QVBoxLayout(main_card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        expenses_header = QFrame()
        expenses_header.setObjectName("expensesHeader")
        expenses_header_layout = QHBoxLayout(expenses_header)
        expenses_header_layout.setContentsMargins(20, 13, 20, 13)
        main_label = QLabel("EXPENSES")
        main_label.setObjectName("sectionTitle")
        expenses_header_layout.addWidget(main_label)
        expenses_header_layout.addStretch()
        main_layout.addWidget(expenses_header)

        table_wrap = QFrame()
        table_wrap.setObjectName("tableBody")
        table_wrap_layout = QVBoxLayout(table_wrap)
        table_wrap_layout.setContentsMargins(14, 12, 14, 14)
        table_wrap_layout.addWidget(self.table, 1)
        main_layout.addWidget(table_wrap, 1)

        # Summary column
        right_column = QVBoxLayout()
        right_column.setSpacing(14)

        month_card = QFrame()
        month_card.setObjectName("summaryCard")
        month_card.setFixedHeight(220)
        month_layout = QVBoxLayout(month_card)
        month_layout.setContentsMargins(0, 0, 0, 0)
        month_layout.setSpacing(0)

        month_header_frame = QFrame()
        month_header_frame.setObjectName("monthHeader")
        month_header = QHBoxLayout(month_header_frame)
        month_header.setContentsMargins(16, 11, 12, 11)
        month_title = QLabel("MONTH")
        month_title.setObjectName("sectionTitle")
        month_header.addWidget(month_title)
        month_header.addStretch()
        # The selected year is still used internally, but the reference layout
        # keeps the Month header visually clean.
        self.year_selector.hide()
        month_header.addWidget(self.month_graph_button)
        month_layout.addWidget(month_header_frame)

        month_body = QFrame()
        month_body.setObjectName("summaryBody")
        month_body_layout = QVBoxLayout(month_body)
        month_body_layout.setContentsMargins(10, 10, 10, 12)
        month_body_layout.addWidget(self.month_table)
        month_layout.addWidget(month_body, 1)

        category_card = QFrame()
        category_card.setObjectName("summaryCard")
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(0)

        category_header_frame = QFrame()
        category_header_frame.setObjectName("categoryHeader")
        category_header = QHBoxLayout(category_header_frame)
        category_header.setContentsMargins(16, 11, 12, 11)
        category_title = QLabel("CATEGORY")
        category_title.setObjectName("sectionTitle")
        category_header.addWidget(category_title)
        category_header.addStretch()
        category_header.addWidget(self.category_graph_button)
        category_layout.addWidget(category_header_frame)

        category_body = QFrame()
        category_body.setObjectName("summaryBody")
        category_body_layout = QVBoxLayout(category_body)
        category_body_layout.setContentsMargins(10, 10, 10, 12)
        category_body_layout.addWidget(self.category_table)
        category_layout.addWidget(category_body, 1)

        right_column.addWidget(month_card)
        right_column.addWidget(category_card, 1)

        # Keep the Category card aligned with the bottom edge of Expenses.
        content.addWidget(main_card, 68)
        content.addLayout(right_column, 32)
        master.addLayout(content, 1)

    # ------------------------------------------------------------------
    # Category management
    # ------------------------------------------------------------------
    def load_categories(self, selected_category=None):
        previous = selected_category or self.dropdown.currentText()
        self.dropdown.clear()

        for name, _is_default, color in fetch_categories():
            self.dropdown.addItem(self.color_icon(color), name)

        if previous:
            index = self.dropdown.findText(previous)
            if index >= 0:
                self.dropdown.setCurrentIndex(index)

    def add_custom_category(self):
        category, ok = QInputDialog.getText(
            self,
            "Add Category",
            "Enter a new category name:",
        )
        if not ok:
            return

        category = category.strip()
        if not category:
            QMessageBox.warning(self, "Invalid Category", "Category name cannot be empty.")
            return

        existing = [name.lower() for name, _default, _color in fetch_categories()]
        if category.lower() in existing:
            QMessageBox.warning(self, "Category Exists", "That category already exists.")
            return

        color = QColorDialog.getColor(QColor(PALETTE["mint"]), self, "Choose Category Color")
        color_hex = color.name() if color.isValid() else PALETTE["mint"]

        if add_category(category, color_hex):
            self.load_categories(category)
            self.refresh_summaries()
        else:
            QMessageBox.critical(self, "Error", "Failed to add category.")

    def remove_category(self):
        category = self.dropdown.currentText()
        if not category:
            return

        if self.dropdown.count() <= 1:
            QMessageBox.information(
                self,
                "Keep One Category",
                "Add another category before deleting the last remaining category.",
            )
            return

        confirm = QMessageBox.question(
            self,
            "Delete Category",
            (
                f'Delete "{category}" from the category list?\n\n'
                "Existing expenses keep their historical category name."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if delete_category(category):
            self.load_categories()
            self.load_table_data()
            self.refresh_summaries()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete category.")

    def choose_category_color(self):
        category = self.dropdown.currentText()
        if not category:
            return

        current_color = self.category_color(category)
        color = QColorDialog.getColor(QColor(current_color), self, f"Color for {category}")
        if not color.isValid():
            return

        if update_category_color(category, color.name()):
            self.load_categories(category)
            self.load_table_data()
            self.refresh_summaries()
        else:
            QMessageBox.critical(self, "Error", "Failed to save the category color.")

    # ------------------------------------------------------------------
    # Main expense table
    # ------------------------------------------------------------------
    def load_table_data(self):
        self.loading_table = True
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for row_idx, expense in enumerate(fetch_expenses()):
            expense_id, item, category, amount, date, note = expense
            self.table.insertRow(row_idx)

            cells = [
                QTableWidgetItem("" if item is None else str(item)),
                QTableWidgetItem("" if category is None else str(category)),
                QTableWidgetItem(self.format_amount(amount)),
                QTableWidgetItem("" if date is None else str(date)),
                QTableWidgetItem("" if note is None else str(note)),
            ]

            cells[0].setData(Qt.ItemDataRole.UserRole, expense_id)
            self.apply_category_style(cells[1], cells[1].text())

            for column, cell in enumerate(cells):
                self.table.setItem(row_idx, column, cell)

        self.table.blockSignals(False)
        self.loading_table = False

    def add_expense_from_inputs(self):
        item = self.item.text().strip()
        category = self.dropdown.currentText().strip()
        amount = self.amount.value()
        date = self.date_box.date().toString("yyyy-MM-dd")
        note = self.note.text().strip()

        if not item:
            QMessageBox.warning(self, "Input Error", "Item cannot be empty.")
            return
        if not category:
            QMessageBox.warning(self, "Input Error", "Please add or choose a category.")
            return

        if add_expense(date, category, amount, item, note):
            self.clear_inputs()
            self.after_expense_change()
        else:
            QMessageBox.critical(self, "Error", "Failed to add expense.")

    def clear_inputs(self):
        self.item.clear()
        self.amount.setValue(0.00)
        self.date_box.setDate(QDate.currentDate())
        self.note.clear()
        if self.dropdown.count() > 0:
            self.dropdown.setCurrentIndex(0)

    def delete_selected_expense(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Error", "Please choose an expense to delete.")
            return

        id_cell = self.table.item(row, 0)
        if id_cell is None:
            return
        expense_id = id_cell.data(Qt.ItemDataRole.UserRole)

        confirm = QMessageBox.question(
            self,
            "Delete Expense",
            "Are you sure you want to delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if delete_expense(expense_id):
            self.after_expense_change()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete expense.")

    def save_inline_edit(self, changed_item):
        if self.loading_table:
            return

        row = changed_item.row()
        id_cell = self.table.item(row, 0)
        if id_cell is None:
            return

        expense_id = id_cell.data(Qt.ItemDataRole.UserRole)
        item = self.cell_text(row, 0).strip()
        category = self.cell_text(row, 1).strip()
        amount = self.parse_amount(self.cell_text(row, 2))
        date = self.cell_text(row, 3).strip()
        note = self.cell_text(row, 4).strip()

        if not item:
            QMessageBox.warning(self, "Invalid Item", "Item cannot be empty.")
            self.load_table_data()
            return

        if not category:
            QMessageBox.warning(self, "Invalid Category", "Category cannot be empty.")
            self.load_table_data()
            return

        parsed_date = QDate.fromString(date, "yyyy-MM-dd")
        if not parsed_date.isValid():
            QMessageBox.warning(self, "Invalid Date", "Use the date format YYYY-MM-DD.")
            self.load_table_data()
            return

        if not update_expense(expense_id, item, category, amount, date, note):
            QMessageBox.critical(self, "Error", "Failed to save the edited expense.")
            self.load_table_data()
            return

        self.after_expense_change()

    def after_expense_change(self):
        selected_year = self.year_selector.currentText()
        self.load_table_data()
        self.refresh_year_selector(preferred_year=selected_year)
        self.refresh_summaries()

    def eventFilter(self, source, event):
        if source is self.table and event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.delete_selected_expense()
                return True

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current = self.table.currentItem()
                if current is not None:
                    self.table.editItem(current)
                    return True

        return super().eventFilter(source, event)

    # ------------------------------------------------------------------
    # Summaries and graphs
    # ------------------------------------------------------------------
    def refresh_year_selector(self, preferred_year=None):
        current_year = QDate.currentDate().year()
        years = set(fetch_years())
        years.add(current_year)
        years = sorted(years, reverse=True)

        preferred = str(preferred_year or self.year_selector.currentText() or current_year)

        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        self.year_selector.addItems([str(year) for year in years])

        index = self.year_selector.findText(preferred)
        if index < 0:
            index = self.year_selector.findText(str(current_year))
        self.year_selector.setCurrentIndex(max(index, 0))
        self.year_selector.blockSignals(False)

    def selected_year(self):
        try:
            return int(self.year_selector.currentText())
        except (TypeError, ValueError):
            return QDate.currentDate().year()

    def refresh_summaries(self, *_args):
        if not hasattr(self, "month_table"):
            return

        year = self.selected_year()
        month_totals = fetch_month_totals(year)

        self.month_table.setRowCount(12)
        for month in range(1, 13):
            month_item = QTableWidgetItem(calendar.month_abbr[month])
            total_item = QTableWidgetItem(self.format_amount(month_totals.get(month, 0)))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.month_table.setItem(month - 1, 0, month_item)
            self.month_table.setItem(month - 1, 1, total_item)

        category_totals = fetch_category_totals(year)
        self.category_table.setRowCount(len(category_totals))

        for row, (name, total, color) in enumerate(category_totals):
            category_item = QTableWidgetItem(self.dot_icon(color), name)
            total_item = QTableWidgetItem(self.format_amount(total))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.category_table.setItem(row, 0, category_item)
            self.category_table.setItem(row, 1, total_item)

    def show_month_graph(self):
        year = self.selected_year()
        totals = fetch_month_totals(year)
        values = [(calendar.month_abbr[m], totals.get(m, 0.0)) for m in range(1, 13)]
        dialog = ChartDialog(f"Monthly Spending - {year}", BarChartWidget(values), self)
        dialog.exec()

    def show_category_graph(self):
        year = self.selected_year()
        values = fetch_category_totals(year)
        dialog = ChartDialog(f"Category Spending - {year}", PieChartWidget(values), self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def cell_text(self, row, column):
        item = self.table.item(row, column)
        return "" if item is None else item.text()

    def category_color(self, category):
        for name, _is_default, color in fetch_categories():
            if name == category:
                return color
        return FALLBACK_CATEGORY_COLOR

    def apply_category_style(self, item, category):
        self.apply_color_to_item(item, self.category_color(category))

    @staticmethod
    def apply_color_to_item(item, color_hex):
        color = QColor(color_hex)
        item.setBackground(color)
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        item.setForeground(QColor("#17343A") if luminance > 150 else QColor("#FFFFFF"))

    @staticmethod
    def color_icon(color_hex):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color_hex))
        return QIcon(pixmap)


    @staticmethod
    def dot_icon(color_hex):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color_hex))
        painter.drawEllipse(1, 1, 14, 14)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def parse_amount(text):
        cleaned = str(text).replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def format_amount(amount):
        try:
            return f"${float(amount):,.2f}"
        except (TypeError, ValueError):
            return "$0.00"

