import openpyxl
import sqlite3

# Файл Excel
excel_file = "books.xlsx"

# База
db_file = "instance/newflask.db"

# Відкриваємо Excel
wb = openpyxl.load_workbook(excel_file)
sheet = wb.active

# Підключаємось до БД
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Пропускаємо перший рядок (заголовки)
rows = list(sheet.iter_rows(min_row=2, values_only=True))

count = 0
for row in rows:
    name_book = row[1]  # Колонка A
    author = row[0]     # Колонка B
    ean = row[2] if len(row) > 2 else ""  # Колонка C
    
    # Пропускаємо порожні рядки
    if not name_book or not author:
        continue
    
    cursor.execute('''
        INSERT INTO book (name_book, author, ean, buyer, phone, stat, surname, date, enddate, history)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name_book, author, ean or "", "", "", "доступна", "", None, None, ""))
    
    count += 1

conn.commit()
conn.close()

print(f"✅ Імпортовано {count} книг!")