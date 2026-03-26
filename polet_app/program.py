from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys, shutil, os #модули для перемещения и удаления картинок
from PIL import Image
import sqlite3
from login import Ui_Dialog as login_interface
from main import Ui_MainWindow as main_interface
from zakaz import Ui_Dialog as zakaz_interface
from tovar import Ui_Dialog as tovar_interface

role = 'Гость' #роль по умолчанию
fio = ''
login = ''

class mainWindow(QMainWindow): #главное окно
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = main_interface()
        self.ui.setupUi(self)

        self.ui.action.triggered.connect(self.logout)
        self.ui.pushButton.clicked.connect(self.add_tovar)
        self.ui.pushButton_2.clicked.connect(self.add_zakaz)
        self.ui.pushButton_3.clicked.connect(self.del_tovar)
        self.ui.pushButton_4.clicked.connect(self.del_zakaz)
        
        self.ui.radioButton.toggled.connect(self.search_tovar)
        self.ui.radioButton_2.toggled.connect(self.search_tovar)
        self.ui.radioButton_3.toggled.connect(self.search_tovar)
        self.ui.lineEdit.textChanged.connect(self.search_tovar)
        self.ui.comboBox.currentTextChanged.connect(self.search_tovar)

    def read_zakaz(self): #заполнение таблицы заказов
        try:
            cursor.execute('select * from "order"')
            data = cursor.fetchall()
            self.ui.tableWidget_2.setRowCount(len(data))
            for row in range(len(data)):
                for col in range(len(data[row])):
                    item = QTableWidgetItem()
                    item.setText(str(data[row][col]))
                    item.id_zakaz = data[row][7] #создаю атрибут у элемента - номер заказа
                    self.ui.tableWidget_2.setItem(row, col, item)
            self.zakaz_data = data
        except Exception as e: print(e)
        
    def search_tovar(self): #поиск товаров
        try:
            text = self.ui.lineEdit.text()
            filtr = self.ui.comboBox.currentText()
            #поиск просходит по всем текстовым полям
            sql = 'SELECT * FROM tovar WHERE (articul LIKE "%' + text + '%" OR name LIKE "%' + text
            sql += '%" OR postav LIKE "%' + text + '%" OR category LIKE "%' + text + '%" ' + 'OR description LIKE "%' + text + '%")'
            #проверяем также наличие фильтров по поставщикам
            if filtr != 'Все поставщики' and filtr != '':
                sql += ' AND postav = "' + filtr + '"'
            #проверяем наличие сортировки
            if self.ui.radioButton_3.isChecked():
                sql += ' ORDER BY kolvo ASC'
            elif self.ui.radioButton.isChecked():
                sql += ' ORDER BY kolvo DESC'
            cursor.execute(sql)

            data = cursor.fetchall()
            #вывод отобранных товаров
            self.ui.tableWidget.setRowCount(len(data))
            self.ui.tableWidget.setIconSize(QSize(200, 200))
            for row in range(len(data)):
                #фото
                item1 = QTableWidgetItem()
                if data[row][-1] != '':
                    item1.setIcon(QIcon("import/" + data[row][-1]))
                else:
                    item1.setIcon(QIcon("import/picture.png"))
                item1.articul = data[row][0] #создаю атрибут у первой ячейки с артикулом
                #данные товара
                item2 = QTableWidgetItem()
                text = ''
                text += data[row][6] + ' | '        #категория
                text += data[row][1] + '<br>'         #наименование
                text += 'Описание товара: ' + data[row][-2] + '<br>'
                text += 'Производитель: ' + data[row][5] + '<br>'
                text += 'Поставщик: ' + data[row][4] + '<br>'
                if data[row][-4] != 0:
                    text += 'Цена: <span style="color: red; text-decoration: line-through;">' + str(data[row][3]) #старая цена
                    text += '</span><span style="color: black; font-weight: bold;">   ' + str(data[row][3] * (100 - data[row][-4])/100) #новая цена
                    text += '</span><br>'
                else:
                    text += 'Цена: ' + str(data[row][3]) + '<br>'
                text += 'Единица измерения: ' + data[row][2] + '<br>'
                text += 'Количество на складе: ' + str(data[row][-3])
                lbl = QLabel()
                lbl.setTextFormat(Qt.RichText)
                lbl.setText(text)
                self.ui.tableWidget.setCellWidget(row, 1, lbl)
                #скидка
                item3 = QTableWidgetItem()
                item3.setText(str(data[row][-4]) + '%')
                if data[row][-4] > 15: #если скидка больше 15%
                    item1.setBackground(QColor('#2E8B57'))
                    item2.setBackground(QColor('#2E8B57'))
                    item3.setBackground(QColor('#2E8B57'))
                if data[row][-3] == 0: #если товара нет на складе
                    item1.setBackground(QColor(Qt.cyan))
                    item2.setBackground(QColor(Qt.cyan))
                    item3.setBackground(QColor(Qt.cyan))
                self.ui.tableWidget.setItem(row, 0, item1)
                self.ui.tableWidget.setItem(row, 1, item2)
                self.ui.tableWidget.setItem(row, 2, item3)
            self.tovar_data = data #все данные о товарах
            self.ui.tableWidget.resizeRowsToContents()
            #заполняю выпадающий список поставщиков только теми, которые представлены в товарах
            self.ui.comboBox.currentTextChanged.disconnect(self.search_tovar)
            cursor.execute('SELECT DISTINCT postav FROM tovar')
            postav = cursor.fetchall()
            postav = [i[0] for i in postav]
            self.ui.comboBox.clear()
            self.ui.comboBox.addItem('Все поставщики')
            self.ui.comboBox.addItems(postav)
            self.ui.comboBox.setCurrentText(filtr)
            self.ui.comboBox.currentTextChanged.connect(self.search_tovar)
        except Exception as e: print(e)
        
    def set_roles(self, role, fio, login): #функция назначения ролей, происходит после авторизации
        if role == 'Авторизированный клиент':
            self.ui.label_2.setText(fio)
            self.ui.comboBox.setEnabled(False)
            self.ui.lineEdit.setEnabled(False)
            self.ui.pushButton.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.groupBox_2.hide()
            self.ui.radioButton.setEnabled(False)
            self.ui.radioButton_2.setEnabled(False)
            self.ui.radioButton_3.setEnabled(False)
        elif role == 'Менеджер':
            self.ui.label_2.setText(fio)
            self.ui.comboBox.setEnabled(True)
            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.groupBox_2.show()
            self.ui.pushButton_2.setEnabled(False)
            self.ui.pushButton_4.setEnabled(False)
            self.ui.radioButton.setEnabled(True)
            self.ui.radioButton_2.setEnabled(True)
            self.ui.radioButton_3.setEnabled(True)
            self.read_zakaz()
        elif role == 'Администратор':
            self.ui.label_2.setText(fio)
            self.ui.comboBox.setEnabled(True)
            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)
            self.ui.pushButton_3.setEnabled(True)
            self.ui.groupBox_2.show()
            self.ui.pushButton_2.setEnabled(True)
            self.ui.pushButton_4.setEnabled(True)
            self.ui.radioButton.setEnabled(True)
            self.ui.radioButton_2.setEnabled(True)
            self.ui.radioButton_3.setEnabled(True)
            self.read_zakaz()
            
            self.ui.tableWidget.itemDoubleClicked.connect(self.edit_tovar)
            self.ui.tableWidget_2.itemDoubleClicked.connect(self.edit_zakaz)
        else: #Гость
            self.ui.label_2.setText(role)
            self.ui.comboBox.setEnabled(False)
            self.ui.lineEdit.setEnabled(False)
            self.ui.pushButton.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.groupBox_2.hide()
            self.ui.radioButton.setEnabled(False)
            self.ui.radioButton_2.setEnabled(False)
            self.ui.radioButton_3.setEnabled(False)
        self.search_tovar()

    def logout(self): #функция выхода открываем заново окно авторизации
        self.hide()
        try:
            self.ui.tableWidget.itemDoubleClicked.disconnect(self.edit_tovar)
            self.ui.tableWidget_2.itemDoubleClicked.disconnect(self.edit_zakaz)
        except: pass
        login_win.ui.lineEdit.setText('')
        login_win.ui.lineEdit_2.setText('')
        login_win.show()

    def add_tovar(self): #добавление товара, открываем новое окно
        self.tovar_win = tovarWindow()
        self.tovar_win.ui.buttonBox.accepted.connect(self.tovar_win.add)
        self.tovar_win.exec_()

    def add_zakaz(self): #добавление заказа, открываем новое окно
        self.zakaz_win = zakazWindow()
        self.zakaz_win.ui.buttonBox.accepted.connect(self.zakaz_win.add)
        self.zakaz_win.exec_()

    def del_tovar(self): #удаление товара
        r = self.ui.tableWidget.currentRow() #выбранная строка с товаром
        if r == -1:
            QMessageBox.critical(self, 'Ошибка', 'Выберите товар для удаления.', QMessageBox.Ok)
            return
        art = self.ui.tableWidget.item(r, 0).articul
        cursor.execute('SELECT COUNT(*) FROM "order" WHERE articul=?', [art])
        d = int(cursor.fetchone()[0])
        if d == 0: #если данного товара нет в заказах, то удаляем
            try:
                cursor.execute('DELETE FROM tovar WHERE articul=?', [art])
                conn.commit()
                self.search_tovar() #обновляем таблицу с товарами
                QMessageBox.information(self, 'Информация', 'Товар успешно удален.', QMessageBox.Ok)
            except:
                QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранный товар.', QMessageBox.Ok)
        else:
            QMessageBox.critical(self, 'Ошибка', 'Выбранный товар уже есть в заказе.', QMessageBox.Ok)
            
    def del_zakaz(self): #удаление заказа
        r = self.ui.tableWidget_2.currentRow() #строка с выранным заказом
        if r == -1:
            QMessageBox.critical(self, 'Ошибка', 'Выберите заказ для удаления.', QMessageBox.Ok)
            return
        id_zakaz = self.ui.tableWidget_2.item(r, 0).id_zakaz
        try:
            cursor.execute('DELETE FROM "order" WHERE id=?', [id_zakaz])
            conn.commit()
            self.read_zakaz()
            QMessageBox.information(self, 'Информация', 'Заказ успешно удален.', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранный заказ.', QMessageBox.Ok)
            print(e)

    def edit_tovar(self, item): #изменение даннх товара
        try:
            art = self.ui.tableWidget.item(item.row(), 0).articul
            cursor.execute('SELECT * FROM tovar WHERE articul=?', [art])
            #создаем новое окно (такое же как при добавлении), но заполняем текущими данными товара
            data = cursor.fetchone()
            self.tovar_win = tovarWindow()
            self.tovar_win.ui.lineEdit.setText(data[0])
            self.tovar_win.ui.lineEdit_2.setText(data[1])
            self.tovar_win.ui.lineEdit_3.setText(data[2])
            self.tovar_win.ui.doubleSpinBox.setValue(data[3])
            self.tovar_win.ui.lineEdit_5.setText(data[4])
            self.tovar_win.ui.comboBox_2.setCurrentText(data[5])
            self.tovar_win.ui.comboBox.setCurrentText(data[6])
            self.tovar_win.ui.spinBox_2.setValue(int(data[7]))
            self.tovar_win.ui.spinBox.setValue(int(data[8]))
            self.tovar_win.ui.lineEdit_10.setText(data[9])
            self.tovar_win.ui.lineEdit_11.setText(data[10])
            #также при нажатии кнопки будет другая функция, отвечающая за изменение
            self.tovar_win.ui.buttonBox.accepted.connect(lambda: self.tovar_win.upd(art))
            self.tovar_win.exec_()
        except Exception as e: print(e)

    def edit_zakaz(self, item): #изменение данных заказа
        try:
            self.zakaz_win = zakazWindow()
            id_zakaz = self.ui.tableWidget_2.item(item.row(), 0).id_zakaz
            cursor.execute('SELECT * FROM "order" WHERE id=?', [id_zakaz])
            #также создаем окно, такое же как при добавлении заказа, но заполняем текущими данными
            data = cursor.fetchone()
            self.zakaz_win.ui.lineEdit.setText(str(data[0]))
            self.zakaz_win.ui.dateEdit.setDate(QDate.fromString(str(data[1]), 'dd.MM.yyyy'))
            self.zakaz_win.ui.dateEdit_2.setDate(QDate.fromString(str(data[2]), 'dd.MM.yyyy'))
            self.zakaz_win.ui.lineEdit_4.setText(str(data[3]))
            self.zakaz_win.ui.lineEdit_5.setText(str(data[4]))
            self.zakaz_win.ui.spinBox_2.setValue(int(data[5]))
            self.zakaz_win.ui.lineEdit_7.setText(str(data[6]))
            self.zakaz_win.ui.lineEdit_8.setText(str(data[7]))
            self.zakaz_win.ui.spinBox.setValue(int(data[8]))
            #кнопка здесь отвечает за редактирование
            self.zakaz_win.ui.buttonBox.accepted.connect(self.zakaz_win.upd)
            self.zakaz_win.exec_()
        except Exception as e: print(e)
        
class loginWindow(QDialog): #окно логирования
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.ui = login_interface()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.connect(self.log)
        self.ui.buttonBox.rejected.connect(self.log_gost)
        
    def log(self): #функция входа
        global role, fio, login
        login = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        for i in users:
            if i[0] == login and i[-1] == password: #нашли логин и пароль введенные пользователем
                QMessageBox.information(self, 'Информация', 'Вы зашли как ' + i[1], QMessageBox.Ok)
                role = i[2]
                fio = i[1]
                login = i[0]
                main_win.set_roles(role, fio, login)
                main_win.show()
                return
        QMessageBox.information(self, 'Информация', 'Логин или пароль не найден. Вы зашли как Гость.', QMessageBox.Ok)
        role = 'Гость'
        fio = ''
        login = ''
        main_win.set_roles(role, fio, login)
        main_win.show()

    def log_gost(self): #если пользователь ажал кнопку Отмена, то заходит как Гость
        QMessageBox.information(self, 'Информация', 'Вы зашли как Гость.', QMessageBox.Ok)
        role = 'Гость'
        fio = ''
        login = ''
        main_win.set_roles()
        main_win.show()

class zakazWindow(QDialog): #окно добавления/редактирования заказа
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.ui = zakaz_interface()
        self.ui.setupUi(self)

    def add(self): #функция для добавления заказа
        art = self.ui.lineEdit.text()
        date = self.ui.dateEdit.date().toString('dd.MM.yyyy')
        date_2 = self.ui.dateEdit_2.date().toString('dd.MM.yyyy')
        pvz = self.ui.lineEdit_4.text()
        pokup = self.ui.lineEdit_5.text()
        code = str(self.ui.spinBox_2.value())
        status = self.ui.lineEdit_7.text()
        kolvo = str(self.ui.spinBox.value())
        sp = [art, date, date_2, pvz, pokup, code, status, kolvo]
        if any(i == '' for i in sp): #если хоть одно поле пустое
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        try:
            cursor.execute('INSERT INTO "order" (articul, "data", data_dostavki, pvz, "user", code, status, kolvo)' +
                           'VALUES(?,?,?,?,?,?,?,?)', sp)
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить заказ. Проверьте правильность данных.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Заказ успешно добавлен.', QMessageBox.Ok)
        self.close()
        main_win.read_zakaz() #обновляем список заказов на главном окне

    def upd(self): #функция обновления данных заказа
        art = self.ui.lineEdit.text()
        date = self.ui.dateEdit.date().toString('dd.MM.yyyy')
        date_2 = self.ui.dateEdit_2.date().toString('dd.MM.yyyy')
        pvz = self.ui.lineEdit_4.text()
        pokup = self.ui.lineEdit_5.text()
        code = self.ui.spinBox_2.value()
        status = self.ui.lineEdit_7.text()
        id_zakaz = self.ui.lineEdit_8.text()
        kolvo = self.ui.spinBox.value()
        sp = [art, date, date_2, pvz, pokup, code, status, kolvo, id_zakaz]
        if any(i == '' for i in sp): #если хоть одно поле пустое
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        try:
            cursor.execute('UPDATE "order" SET articul=?, data=?, data_dostavki=?, pvz=?, user=?, code=?, ' +
                           'status=?, kolvo=? WHERE id=?', sp)
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', 'Не удалось редактировать заказ. Проверьте правильность данных.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Информация о заказе успешно изменена.', QMessageBox.Ok)
        self.close()
        main_win.read_zakaz() #обновляем список заказов на главном окне

class tovarWindow(QDialog): #окно добавления редактирования товара
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.ui = tovar_interface()
        self.ui.setupUi(self)
        
        self.ui.pushButton.clicked.connect(self.select_photo)

    def select_photo(self): #выбор фотографии
        try:
            filename = QFileDialog.getOpenFileName(self, 'Выберите фото', '', 'Photo (*.jpg *.png *.jpeg)')[0]
            if filename:
                print(filename)
                im = Image.open(filename)
                w, h = im.size
                print(w, h)
                if w <= 300 and h <= 200: #если размер фотографии не больше 300 на 200 пикселей
                    self.ui.lineEdit_11.setText(filename)
                else:
                    QMessageBox.critical(self, 'Ошибка', 'Размер изображения превышает 300Х200 пикселей.', QMessageBox.Ok)
        except Exception as e: print(e)
    
    def add(self): #функция добавления товара
        art = self.ui.lineEdit.text()
        name = self.ui.lineEdit_2.text()
        ed_izm = self.ui.lineEdit_3.text()
        cena = self.ui.doubleSpinBox.value()
        postav = self.ui.lineEdit_5.text()
        proizv = self.ui.comboBox_2.currentText()
        category = self.ui.comboBox.currentText()
        skidka = self.ui.spinBox_2.value()
        kolvo = self.ui.spinBox.value()
        opisanie = self.ui.lineEdit_10.text()
        photo = self.ui.lineEdit_11.text()
        sp = [art, name, ed_izm, cena, postav, proizv, category, skidka, kolvo, opisanie, photo]
        if any(i == '' for i in sp):  #если хоть одно поле пустое
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        try:
            shutil.copy(photo, os.curdir + '/import') #копируем в папку с фотографиями
        except shutil.SameFileError: #если копирую этот же самый файл (фото, которое выбрал пользователь и старое фото - один и тот же файл)
            pass
        try:
            cursor.execute('INSERT INTO tovar VALUES(?,?,?,?,?,?,?,?,?,?,?)', sp)
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить товар. Проверьте правильность данных.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Товар успешно добавлен.', QMessageBox.Ok)
        self.close()
        main_win.search_tovar() #обновляем список товаров на главном окне
        
    def upd(self, old_art): #функция обновления товара
        art = self.ui.lineEdit.text()
        name = self.ui.lineEdit_2.text()
        ed_izm = self.ui.lineEdit_3.text()
        cena = self.ui.doubleSpinBox.value()
        postav = self.ui.lineEdit_5.text()
        proizv = self.ui.comboBox_2.currentText()
        category = self.ui.comboBox.currentText()
        skidka = self.ui.spinBox_2.value()
        kolvo = self.ui.spinBox.value()
        opisanie = self.ui.lineEdit_10.text()
        photo = self.ui.lineEdit_11.text()
        photo_name = photo.split('/')[-1] #берем только название файла
        sp = [art, name, ed_izm, cena, postav, proizv, category, skidka, kolvo, opisanie, photo_name, old_art]
        if any(i == '' for i in sp): #если хоть одно поле пустое
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        
        cursor.execute('SELECT photo FROM tovar WHERE articul=?', [old_art])
        d = cursor.fetchone()[0]
        print(photo)
        print(os.curdir + '/import/' + d)
        if photo != os.curdir + '/import/' + d: #если фотка изменилась
            try:
                shutil.copy(photo, os.curdir + '/import') #копируем в папку с фотографиями
                os.remove(os.curdir + '/import/' + d) #удаляем старую фотку
            except shutil.SameFileError: #если копирую этот же самый файл (фото, которое выбрал пользователь и старое фото - один и тот же файл)
                pass
        try:
            cursor.execute('UPDATE tovar SET articul=?, name=?, edIzm=?, price=?, postav=?, proizv=?, ' +
                           'category=?, sale=?, kolvo=?, description=?, photo=? WHERE articul=?', sp)
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось редактировать товар. Проверьте правильность данных.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Информация о товаре успешно изменена.', QMessageBox.Ok)
        self.close()
        main_win.search_tovar() #обновляем список товаров на главном окне
        
conn = sqlite3.connect('shoes.db')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys")

users = cursor.execute('SELECT * FROM user').fetchall()

app = QApplication(sys.argv)

app.setStyle(QStyleFactory.create("Fusion"))
pal = app.palette()
#создаем палитру и назначаем цвета на свои места
pal.setColor(QPalette.Window, QColor('#FFFFFF'))
pal.setColor(QPalette.Button, QColor('#7FFF00'))
pal.setColor(QPalette.Base, QColor('#00FA9A'))

app.setPalette(pal)
#создаем нужный шрифт
font = QFont('Times New Roman', 12)
app.setFont(font)

main_win = mainWindow()
login_win = loginWindow()
login_win.show()

sys.exit(app.exec_())
cursor.close()
conn.close()
