import sqlite3
connection = sqlite3.connect('mydatabase.db')
cursor = connection.cursor()
# Нахождение минимального возраста
cursor.execute ('SELECT MIN(age) FROM Users')
min_age = cursor.fetchone() [0]
print ('Минимальный возраст среди пользователей: ', min_age)
cursor.execute('SELECT MAX (age) FROM Users')
max_age = cursor.fetchone() [0]
print ('Максимальный возраст среди пользователей: ', max_age)
connection.close()
