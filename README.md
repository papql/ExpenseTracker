# 💰 Expense Tracker

A desktop expense tracking application built with Python, PyQt6, and SQLite.

Track everyday expenses, organize spending by category, and explore monthly and category-based summaries!

---

## ✨ Features

- **Expense Tracking:** Add expenses with an item, category, amount, date, and optional note.
- **Custom Categories:** Add and remove categories to personalize how expenses are organized.
- **Editable Expenses:** Update existing expense information directly within the expense table.
- **Delete Expenses:** Remove expenses that are no longer needed.
- **Monthly Summary:** Automatically calculates total spending for each month.
- **Category Summary:** Shows total spending across different expense categories.
- **Year Selection:** View monthly and category summaries for different years.
- **Data Visualizations:** Generate graphs to better understand monthly and category spending patterns.
- **Persistent Storage:** Uses SQLite to save expense information between sessions.

---

## 🛠️ Technologies Used

- **Python 3** - Core application logic
- **PyQt6** - Desktop graphical user interface
- **SQLite** - Local expense database and data storage
- **SQL** - Creating, retrieving, updating, and deleting expense data
- **Matplotlib** - Spending visualizations
- **QSS** - Custom styling for the PyQt6 interface

---

## 🚀 Getting Started

### Prerequisites

Make sure you have **Python 3** installed on your computer.

Install the required Python libraries:

```bash
pip install PyQt6 matplotlib
```

### 1. Clone the repository

```bash
git clone https://github.com/papql/ExpenseTracker.git
```

### 2. Navigate to the project folder

```bash
cd ExpenseTracker
```

### 3. Run the application

```bash
python main.py
```

> **Note:** The application uses a local SQLite database (`expenses.db`). The database is not included in this repository and is created locally when the application is used.

---

## 📁 File Structure

```text
ExpenseTracker/
├── assets                # Photo Icons 
├── .gitignore            # Files excluded from Git
├── README.md             # Project documentation
├── app.py                # Main application interface and functionality
├── database.py           # SQLite database operations
├── main.py               # Starts the application
└── style.qss             # PyQt6 interface styling
```

> `expenses.db` is excluded through `.gitignore` because it contains locally stored expense data.

---

## 📊 Expense Summaries

The application provides two ways to summarize spending:

**Monthly Summary** displays total expenses for each month of the selected year, making it easier to see how spending changes over time.

**Category Summary** groups expenses by category, helping identify where money is being spent.

Both summaries update using information stored in the SQLite database.

---

## 📈 Data Visualizations

Expense Tracker includes visualizations for exploring spending data.

- **Monthly Graph:** Visualizes spending across months.
- **Category Graph:** Visualizes how spending is distributed across expense categories.

These graphs are generated from the expense data stored in the application.

---

## 💡 About the Project

I am a huge foodie! Some foods I can never resist are pudding, bingsu, sushi, and fried chicken, and I love trying out new restaurants. 🍮🍧🍣🍗

Unfortunately, my love for food also meant that I sometimes found myself spending more than I had planned. Instead of constantly wondering where my money went, I decided to build something that could help.

I created **Expense Tracker** as a personal project to organize my expenses, understand my spending habits, and stay within my budget. At the same time, I wanted to challenge myself by learning more about **Python, SQL, databases, and data analysis**.

Now I can figure out how much I spent on bingsu before convincing myself I need another one. 🍧

---

## 🐞 Issues & Feedback

If you find a bug or have an idea for a feature, feel free to open an issue!

---

## 📄 License

This project is open source.

Feel free to use, modify, and learn from the code.

---

**Happy tracking! 💰**
