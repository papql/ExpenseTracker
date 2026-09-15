# SQL Only
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

DEFAULT_CATEGORIES = [
    "Food",
    "Rent",
    "Bills",
    "Entertainment",
    "Groceries",
    "Other",
]

DEFAULT_CATEGORY_COLORS = {
    "Food": "#D98C8C",          
    "Rent": "#D9A06F",         
    "Bills": "#D5C66F",        
    "Entertainment": "#8FB99A", 
    "Groceries": "#86A9C4",   
    "Other": "#A996C2",        
}

FALLBACK_CATEGORY_COLOR = "#B8A7C9"


def init_db(db_name):
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(db_name)

    if not database.open():
        return False

    query = QSqlQuery()

    # Main expense table. 
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            item TEXT,
            note TEXT
        )
        """
    ):
        return False

    if not _migrate_expense_columns():
        return False

    # Category settings 
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS categories (
        name TEXT PRIMARY KEY,
            is_default INTEGER NOT NULL DEFAULT 0,
            color TEXT
        )
        """
    ):
        return False

    if not _migrate_category_columns():
        return False

    # Only add the default categories once, so deleted categories don't come back when the app restarts.
    if not query.exec(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    ):
        return False

    seeded_query = QSqlQuery()
    seeded_query.prepare("SELECT value FROM app_settings WHERE key = 'defaults_seeded'")
    if not seeded_query.exec():
        return False

    already_seeded = seeded_query.next()
    if not already_seeded:
        for category in DEFAULT_CATEGORIES:
            insert_query = QSqlQuery()
            insert_query.prepare(
                """
                INSERT OR IGNORE INTO categories (name, is_default, color)
                VALUES (?, 1, ?)
                """
            )
            insert_query.addBindValue(category)
            insert_query.addBindValue(DEFAULT_CATEGORY_COLORS.get(category, FALLBACK_CATEGORY_COLOR))
            if not insert_query.exec():
                return False

        setting_query = QSqlQuery()
        if not setting_query.exec(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('defaults_seeded', '1')"
        ):
            return False

    previous_default_colors = {
        "Food": "#D7997D",
        "Rent": "#2E6C76",
        "Bills": "#92C3BE",
        "Entertainment": "#FADED4",
        "Groceries": "#8DB6B7",
        "Other": "#EFF6F9",
    }
    for category, old_color in previous_default_colors.items():
        color_query = QSqlQuery()
        color_query.prepare(
            "UPDATE categories SET color = ? WHERE name = ? AND color = ?"
        )
        color_query.addBindValue(DEFAULT_CATEGORY_COLORS[category])
        color_query.addBindValue(category)
        color_query.addBindValue(old_color)
        if not color_query.exec():
            return False

 # Add colors to older categories that don't have one yet.
    for category in DEFAULT_CATEGORIES:
        color_query = QSqlQuery()
        color_query.prepare(
            "UPDATE categories SET color = ? WHERE name = ? AND (color IS NULL OR color = '')"
             )
        color_query.addBindValue(DEFAULT_CATEGORY_COLORS.get(category, FALLBACK_CATEGORY_COLOR))
        color_query.addBindValue(category)
        if not color_query.exec():
            return False

    fallback_query = QSqlQuery()
    fallback_query.prepare(
        "UPDATE categories SET color = ? WHERE color IS NULL OR color = ''"
    )
    fallback_query.addBindValue(FALLBACK_CATEGORY_COLOR)
    if not fallback_query.exec():
        return False

    return True


def _expense_columns():
    query = QSqlQuery("PRAGMA table_info(expenses)")
    columns = set()
    while query.next():
        columns.add(str(query.value(1)))
    return columns


def _category_columns():
    query = QSqlQuery("PRAGMA table_info(categories)")
    columns = set()
    while query.next():
        columns.add(str(query.value(1)))
    return columns


def _migrate_expense_columns():
    columns = _expense_columns()

    if "description" in columns and "item" not in columns:
        query = QSqlQuery()
        if not query.exec("ALTER TABLE expenses RENAME COLUMN description TO item"):
            return False
        columns = _expense_columns()

    if "item" not in columns:
        query = QSqlQuery()
        if not query.exec("ALTER TABLE expenses ADD COLUMN item TEXT"):
            return False

    if "note" not in columns:
        query = QSqlQuery()
        if not query.exec("ALTER TABLE expenses ADD COLUMN note TEXT"):
            return False

    return True


def _migrate_category_columns():
    columns = _category_columns()

    if "color" not in columns:
        query = QSqlQuery()
        if not query.exec("ALTER TABLE categories ADD COLUMN color TEXT"):
            return False

    return True


def fetch_expenses():
    query = QSqlQuery(
        """
        SELECT id, item, category, amount, date, note
        FROM expenses
        ORDER BY date DESC, id DESC
        """
    )

    expenses = []
    while query.next():
        expenses.append([query.value(i) for i in range(6)])
    return expenses

def add_expense(date, category, amount, item, note=""):
    query = QSqlQuery()
    query.prepare(
        """
        INSERT INTO expenses (date, category, amount, item, note)
        VALUES (?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(date)
    query.addBindValue(category)
    query.addBindValue(amount)
    query.addBindValue(item)
    query.addBindValue(note)
    return query.exec()


def update_expense(expense_id, item, category, amount, date, note):
    query = QSqlQuery()
    query.prepare(
        """
        UPDATE expenses
        SET item = ?, category = ?, amount = ?, date = ?, note = ?
        WHERE id = ?
        """
    )
    query.addBindValue(item)
    query.addBindValue(category)
    query.addBindValue(amount)
    query.addBindValue(date)
    query.addBindValue(note)
    query.addBindValue(expense_id)
    return query.exec()


def delete_expense(expense_id):
    query = QSqlQuery()
    query.prepare("DELETE FROM expenses WHERE id = ?")
    query.addBindValue(expense_id)
    return query.exec()


def fetch_categories():
    query = QSqlQuery(
        """
        SELECT name, is_default, color
        FROM categories
        ORDER BY is_default DESC, name COLLATE NOCASE
        """
    )

    categories = []
    while query.next():
        categories.append(
            (str(query.value(0)),
                bool(query.value(1)),
                str(query.value(2) or FALLBACK_CATEGORY_COLOR),
            )
        )
    return categories


def add_category(name, color=FALLBACK_CATEGORY_COLOR):
    query = QSqlQuery()
    query.prepare(
        "INSERT INTO categories (name, is_default, color) VALUES (?, 0, ?)"
    )
    query.addBindValue(name)
    query.addBindValue(color)
    return query.exec()


def delete_category(name):
    query = QSqlQuery()
    query.prepare("DELETE FROM categories WHERE name = ?")
    query.addBindValue(name)

    if not query.exec():
        return False
    return query.numRowsAffected() > 0


def update_category_color(name, color):
    query = QSqlQuery()
    query.prepare("UPDATE categories SET color = ? WHERE name = ?")
    query.addBindValue(color)
    query.addBindValue(name)

    if not query.exec():
        return False
    return query.numRowsAffected() > 0


def fetch_years():
    query = QSqlQuery(
        """
        SELECT DISTINCT CAST(substr(date, 1, 4) AS INTEGER) AS year
        FROM expenses
        WHERE date IS NOT NULL AND length(date) >= 4
        ORDER BY year DESC
        """
    )

    years = []
    while query.next():
        try:
            years.append(int(query.value(0)))
        except (TypeError, ValueError):
            pass

    return years


def fetch_month_totals(year):
    totals = {month: 0.0 for month in range(1, 13)}

    query = QSqlQuery()
    query.prepare(
        """
        SELECT CAST(substr(date, 6, 2) AS INTEGER) AS month,
               COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(date, 1, 4) = ?
        GROUP BY month
        ORDER BY month
        """
    )
    query.addBindValue(str(year))

    if query.exec():
        while query.next():
            try:
                month = int(query.value(0))
                total = float(query.value(1) or 0)
            except (TypeError, ValueError):
                continue
            if 1 <= month <= 12:
                totals[month] = total

    return totals


def fetch_category_totals(year):
    # Show all current categories, including ones with $0 spent.
    categories = {
        name: {"total": 0.0, "color": color}
        for name, _is_default, color in fetch_categories()
    }

    query = QSqlQuery()
    query.prepare( """
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(date, 1, 4) = ?
        GROUP BY category
        ORDER BY category COLLATE NOCASE
        """
    )
    query.addBindValue(str(year))

    if query.exec():
        while query.next():
            name = str(query.value(0) or "Uncategorized")
            try:
                total = float(query.value(1) or 0)
            except (TypeError, ValueError):
                total = 0.0

            # Keep old expenses even if their category has been deleted.
            if name not in categories:
                categories[name] = {
                    "total": 0.0,
                    "color": FALLBACK_CATEGORY_COLOR,
                }
            categories[name]["total"] = total

    return [
        (name, values["total"], values["color"])
        for name, values in sorted(categories.items(), key=lambda pair: pair[0].lower())
    ]