import pandas as pd
import sqlite3


# Файл Excel
excel_file = "books.xlsx"

# База
db_file = "instance/newflask.db"


# Читаємо тільки потрібні колонки
df = pd.read_excel(
    excel_file,
    usecols=["name_book", "author", "ean"]
)


# Додаємо відсутні колонки з дефолтом
df["buyer"] = ""
df["phone"] = ""
df["stat"] = "нема"
df["surname"] = ""
df["date"] = None
df["enddate"] = None
df["history"] = None


# Підключаємось
conn = sqlite3.connect(db_file)


# Записуємо в Book
df.to_sql(
    "book",
    conn,
    if_exists="append",
    index=False
)

conn.close()

print("✅ Імпорт завершено!")