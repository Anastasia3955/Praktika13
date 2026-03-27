from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 455)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("import/Icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)

        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")

        self.lineEdit_5 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.gridLayout.addWidget(self.lineEdit_5, 4, 1, 1, 2)

        self.spinBox_2 = QtWidgets.QSpinBox(Dialog)
        self.spinBox_2.setObjectName("spinBox_2")
        self.gridLayout.addWidget(self.spinBox_2, 7, 1, 1, 2)

        self.label_10 = QtWidgets.QLabel(Dialog)
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 9, 0, 1, 1)

        self.comboBox = QtWidgets.QComboBox(Dialog)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 6, 1, 1, 2)

        self.label_6 = QtWidgets.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)

        self.label_8 = QtWidgets.QLabel(Dialog)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 7, 0, 1, 1)

        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.doubleSpinBox.setMaximum(999999.99)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.gridLayout.addWidget(self.doubleSpinBox, 3, 1, 1, 2)

        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.lineEdit_2 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridLayout.addWidget(self.lineEdit_2, 1, 1, 1, 2)

        self.lineEdit_3 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.gridLayout.addWidget(self.lineEdit_3, 2, 1, 1, 2)

        self.label_9 = QtWidgets.QLabel(Dialog)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 8, 0, 1, 1)

        self.lineEdit_11 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_11.setReadOnly(True)
        self.lineEdit_11.setObjectName("lineEdit_11")
        self.gridLayout.addWidget(self.lineEdit_11, 10, 1, 1, 1)

        self.spinBox = QtWidgets.QSpinBox(Dialog)
        self.spinBox.setObjectName("spinBox")
        self.gridLayout.addWidget(self.spinBox, 8, 1, 1, 2)

        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)

        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 2)

        self.lineEdit_10 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_10.setObjectName("lineEdit_10")
        self.gridLayout.addWidget(self.lineEdit_10, 9, 1, 1, 2)

        self.label_11 = QtWidgets.QLabel(Dialog)
        self.label_11.setObjectName("label_11")
        self.gridLayout.addWidget(self.label_11, 10, 0, 1, 1)

        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 10, 2, 1, 1)

        self.label_7 = QtWidgets.QLabel(Dialog)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 6, 0, 1, 1)

        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)

        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 11, 1, 1, 1)

        self.comboBox_2 = QtWidgets.QComboBox(Dialog)
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.gridLayout.addWidget(self.comboBox_2, 5, 1, 1, 2)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Добавление/редактирование билета"))
        self.label.setText(_translate("Dialog", "Код билета:"))
        self.label_2.setText(_translate("Dialog", "Маршрут:"))
        self.label_3.setText(_translate("Dialog", "Конечный пункт:"))
        self.label_4.setText(_translate("Dialog", "Цена:"))
        self.label_5.setText(_translate("Dialog", "Тип самолета:"))
        self.label_6.setText(_translate("Dialog", "Тип самолета (список):"))
        self.label_7.setText(_translate("Dialog", "Конечный пункт (список):"))
        self.label_8.setText(_translate("Dialog", "Продолжительность полета (ч):"))
        self.label_9.setText(_translate("Dialog", "Количество продаж:"))
        self.label_10.setText(_translate("Dialog", "Дата вылета:"))
        self.label_11.setText(_translate("Dialog", "Изображение:"))
        self.pushButton.setText(_translate("Dialog", "Выбрать"))

        self.comboBox.setItemText(0, _translate("Dialog", "Москва"))
        self.comboBox.setItemText(1, _translate("Dialog", "Санкт-Петербург"))
        self.comboBox.setItemText(2, _translate("Dialog", "Сочи"))

        self.comboBox_2.setItemText(0, _translate("Dialog", "Airbus A320"))
        self.comboBox_2.setItemText(1, _translate("Dialog", "Boeing 737-800"))
        self.comboBox_2.setItemText(2, _translate("Dialog", "Sukhoi Superjet 100"))
        self.comboBox_2.setItemText(3, _translate("Dialog", "Airbus A321"))
        self.comboBox_2.setItemText(4, _translate("Dialog", "Boeing 777-300ER"))
        self.comboBox_2.setItemText(5, _translate("Dialog", "Ту-214"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
