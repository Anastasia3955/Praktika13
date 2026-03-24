import sqlite3
# Устанавливаем соединение с базой данных
connection = sqlite3.connect('mydatabase.db')
cursor = connection.cursor()
# Создаем представление для активных пользователей
cursor.execute('CREATE VIEW ActiveUsers AS SELECT * FROM Users WHERE is_active = 1')
# Выбираем активных пользователей
cursor.execute('SELECT * FROM ActiveUsers')
active_users = cursor.fetchall()
# Выводим результаты
for user in active_users:
    print (user)
# Закрываем соединение
connection.close()
