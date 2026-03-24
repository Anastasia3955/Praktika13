import sqlite3
# Создаем подключение к базе данных 
connection = sqlite3.connect('mydatabase.db')
connection.close()
