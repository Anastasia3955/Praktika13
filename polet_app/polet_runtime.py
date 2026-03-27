from datetime import datetime
import os
from pathlib import Path
import re
import sqlite3
import sys

import PyQt5
from PyQt5.QtCore import QDate, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QCompleter,
    QDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStyleFactory,
    QTableWidgetItem,
)

from login import Ui_Dialog as login_interface
from main import Ui_MainWindow as main_interface
from tovar import Ui_Dialog as tovar_interface
from zakaz import Ui_Dialog as zakaz_interface


def configure_qt_runtime():
    pyqt_root = Path(PyQt5.__file__).resolve().parent
    qt_root = pyqt_root / "Qt5"
    plugin_root = qt_root / "plugins"
    platform_root = plugin_root / "platforms"
    bin_root = qt_root / "bin"

    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_root))
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_root))

    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    if str(bin_root) not in path_parts:
        os.environ["PATH"] = (
            str(bin_root) + os.pathsep + current_path if current_path else str(bin_root)
        )

    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is not None and bin_root.exists():
        add_dll_directory(str(bin_root))

    return plugin_root


QT_PLUGIN_ROOT = configure_qt_runtime()

DEFAULT_ROLE = "Гость"
ADMIN_ROLE = "Администратор"
MANAGER_ROLE = "Менеджер"
TICKET_FILTER_LABEL = "Все типы самолетов"
DEFAULT_TICKET_ICON = "import/picture.png"

AUTH_USERS = {
    "admin": {
        "password": "admin",
        "role": ADMIN_ROLE,
        "display_name": "Администратор Полет",
    },
    "manager": {
        "password": "manager",
        "role": MANAGER_ROLE,
        "display_name": "Менеджер Полет",
    },
}


class ValidationError(Exception):
    pass


def locate_database_path():
    current = Path(__file__).resolve()
    candidates = [
        current.with_name("Polet.db"),
        Path.cwd() / "Polet.db",
        Path.home() / "Desktop" / "Git" / "Polet.db",
    ]

    for parent in current.parents:
        candidates.append(parent / "Polet.db")
        candidates.append(parent / "Git" / "Polet.db")

    seen = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except FileNotFoundError:
            candidate = candidate.absolute()

        if candidate in seen:
            continue
        seen.add(candidate)

        if candidate.exists():
            return candidate

    raise FileNotFoundError("Не удалось найти файл Polet.db.")


def locate_resource(relative_path):
    current = Path(__file__).resolve()
    candidates = [
        current.parent / relative_path,
        Path.cwd() / relative_path,
    ]

    for parent in current.parents:
        candidates.append(parent / relative_path)

    seen = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except FileNotFoundError:
            candidate = candidate.absolute()

        if candidate in seen:
            continue
        seen.add(candidate)

        if candidate.exists():
            return candidate

    return None


def icon_from_relative(relative_path):
    path = locate_resource(relative_path)
    if path is None:
        return QIcon()
    return QIcon(str(path))


def normalize_iso_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError("Дата должна быть в формате YYYY-MM-DD.") from exc


def iso_to_display(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


def qdate_from_iso(value):
    date_value = QDate.fromString(str(value), "yyyy-MM-dd")
    if date_value.isValid():
        return date_value
    return QDate.currentDate()


def client_display_name(row):
    parts = [row["Фамилия"], row["Имя"], row["Отчество"]]
    full_name = " ".join(part for part in parts if part)
    return f"{full_name} [{row['Код_клиента']}]"


class Repository:
    def __init__(self, database_path):
        self.database_path = database_path
        self.connection = sqlite3.connect(str(database_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self):
        self.connection.close()

    def list_ticket_types(self):
        rows = self.connection.execute(
            """
            SELECT DISTINCT "Тип_самолета"
            FROM "Авиабилеты"
            WHERE TRIM(COALESCE("Тип_самолета", '')) <> ''
            ORDER BY "Тип_самолета"
            """
        ).fetchall()
        return [row[0] for row in rows]

    def list_destinations(self):
        rows = self.connection.execute(
            """
            SELECT DISTINCT "Конечный_пункт"
            FROM "Авиабилеты"
            WHERE TRIM(COALESCE("Конечный_пункт", '')) <> ''
            ORDER BY "Конечный_пункт"
            """
        ).fetchall()
        return [row[0] for row in rows]

    def list_clients(self):
        return self.connection.execute(
            """
            SELECT "Код_клиента", "Фамилия", "Имя", "Отчество", "Город"
            FROM "Клиенты"
            ORDER BY "Фамилия", "Имя", "Отчество"
            """
        ).fetchall()

    def get_client_by_id(self, client_id):
        return self.connection.execute(
            """
            SELECT "Код_клиента", "Фамилия", "Имя", "Отчество", "Город"
            FROM "Клиенты"
            WHERE "Код_клиента" = ?
            """,
            (client_id,),
        ).fetchone()

    def resolve_client(self, user_input):
        value = user_input.strip()
        if not value:
            return None

        bracket_match = re.search(r"\[(\d+)\]\s*$", value)
        if bracket_match:
            return self.get_client_by_id(int(bracket_match.group(1)))

        if value.isdigit():
            return self.get_client_by_id(int(value))

        for row in self.list_clients():
            full_name = " ".join(
                part for part in [row["Фамилия"], row["Имя"], row["Отчество"]] if part
            )
            if value.casefold() == full_name.casefold():
                return row

        return None

    def next_ticket_id(self):
        row = self.connection.execute(
            'SELECT COALESCE(MAX("Код_билета"), 0) + 1 FROM "Авиабилеты"'
        ).fetchone()
        return int(row[0])

    def next_order_id(self):
        row = self.connection.execute(
            'SELECT COALESCE(MAX("Номер_заказа"), 0) + 1 FROM "Заказы"'
        ).fetchone()
        return int(row[0])

    def ticket_sales_count(self, ticket_id):
        row = self.connection.execute(
            """
            SELECT COALESCE(SUM("Количество"), 0)
            FROM "Заказы"
            WHERE "Авиабилеты_Код_билета" = ?
            """,
            (ticket_id,),
        ).fetchone()
        return int(row[0])

    def ticket_has_orders(self, ticket_id):
        row = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM "Заказы"
            WHERE "Авиабилеты_Код_билета" = ?
            """,
            (ticket_id,),
        ).fetchone()
        return int(row[0]) > 0

    def list_tickets(self, search_text="", ticket_type="", sort_mode="none"):
        pattern = f"%{search_text.strip()}%"
        sql = """
            SELECT
                t."Код_билета" AS ticket_id,
                t."Маршрут" AS route,
                t."Конечный_пункт" AS destination,
                t."Тип_самолета" AS plane_type,
                t."Дата_вылета" AS departure_date,
                t."Продолжительность_полета" AS duration_hours,
                t."Цена" AS price,
                COALESCE(SUM(o."Количество"), 0) AS quantity,
                COALESCE(MAX(o."Скидка"), 0) AS discount
            FROM "Авиабилеты" t
            LEFT JOIN "Заказы" o
                ON o."Авиабилеты_Код_билета" = t."Код_билета"
            WHERE (
                CAST(t."Код_билета" AS TEXT) LIKE ?
                OR t."Маршрут" LIKE ?
                OR t."Конечный_пункт" LIKE ?
                OR t."Тип_самолета" LIKE ?
                OR t."Дата_вылета" LIKE ?
            )
        """
        params = [pattern, pattern, pattern, pattern, pattern]

        if ticket_type and ticket_type != TICKET_FILTER_LABEL:
            sql += ' AND t."Тип_самолета" = ?'
            params.append(ticket_type)

        sql += """
            GROUP BY
                t."Код_билета",
                t."Маршрут",
                t."Конечный_пункт",
                t."Тип_самолета",
                t."Дата_вылета",
                t."Продолжительность_полета",
                t."Цена"
        """

        if sort_mode == "asc":
            sql += ' ORDER BY quantity ASC, t."Код_билета" ASC'
        elif sort_mode == "desc":
            sql += ' ORDER BY quantity DESC, t."Код_билета" ASC'
        else:
            sql += ' ORDER BY t."Код_билета" ASC'

        return self.connection.execute(sql, params).fetchall()

    def get_ticket(self, ticket_id):
        return self.connection.execute(
            """
            SELECT
                "Код_билета",
                "Маршрут",
                "Конечный_пункт",
                "Тип_самолета",
                "Дата_вылета",
                "Продолжительность_полета",
                "Цена"
            FROM "Авиабилеты"
            WHERE "Код_билета" = ?
            """,
            (ticket_id,),
        ).fetchone()

    def insert_ticket(self, ticket_id, route, destination, plane_type, departure_date, duration_hours, price):
        with self.connection:
            if ticket_id is None:
                self.connection.execute(
                    """
                    INSERT INTO "Авиабилеты" (
                        "Маршрут",
                        "Конечный_пункт",
                        "Тип_самолета",
                        "Дата_вылета",
                        "Продолжительность_полета",
                        "Цена"
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (route, destination, plane_type, departure_date, duration_hours, price),
                )
            else:
                self.connection.execute(
                    """
                    INSERT INTO "Авиабилеты" (
                        "Код_билета",
                        "Маршрут",
                        "Конечный_пункт",
                        "Тип_самолета",
                        "Дата_вылета",
                        "Продолжительность_полета",
                        "Цена"
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ticket_id, route, destination, plane_type, departure_date, duration_hours, price),
                )

    def update_ticket(self, ticket_id, route, destination, plane_type, departure_date, duration_hours, price):
        with self.connection:
            self.connection.execute(
                """
                UPDATE "Авиабилеты"
                SET
                    "Маршрут" = ?,
                    "Конечный_пункт" = ?,
                    "Тип_самолета" = ?,
                    "Дата_вылета" = ?,
                    "Продолжительность_полета" = ?,
                    "Цена" = ?
                WHERE "Код_билета" = ?
                """,
                (route, destination, plane_type, departure_date, duration_hours, price, ticket_id),
            )

    def delete_ticket(self, ticket_id):
        if self.ticket_has_orders(ticket_id):
            raise ValidationError("Этот билет уже используется в заказах, удалить его нельзя.")
        with self.connection:
            self.connection.execute(
                'DELETE FROM "Авиабилеты" WHERE "Код_билета" = ?',
                (ticket_id,),
            )

    def list_orders(self):
        return self.connection.execute(
            """
            SELECT
                o."Номер_заказа" AS order_id,
                o."Клиенты_Код_клиента" AS client_id,
                o."Авиабилеты_Код_билета" AS ticket_id,
                o."Количество" AS quantity,
                COALESCE(o."Скидка", 0) AS discount,
                o."Дата_заказа" AS order_date,
                t."Дата_вылета" AS departure_date,
                t."Маршрут" AS route,
                c."Фамилия" AS last_name,
                c."Имя" AS first_name,
                c."Отчество" AS middle_name,
                c."Город" AS city
            FROM "Заказы" o
            JOIN "Авиабилеты" t
                ON t."Код_билета" = o."Авиабилеты_Код_билета"
            JOIN "Клиенты" c
                ON c."Код_клиента" = o."Клиенты_Код_клиента"
            ORDER BY o."Номер_заказа"
            """
        ).fetchall()

    def get_order(self, order_id):
        return self.connection.execute(
            """
            SELECT
                o."Номер_заказа" AS order_id,
                o."Клиенты_Код_клиента" AS client_id,
                o."Авиабилеты_Код_билета" AS ticket_id,
                o."Количество" AS quantity,
                COALESCE(o."Скидка", 0) AS discount,
                o."Дата_заказа" AS order_date,
                t."Дата_вылета" AS departure_date,
                t."Маршрут" AS route,
                c."Фамилия" AS last_name,
                c."Имя" AS first_name,
                c."Отчество" AS middle_name,
                c."Город" AS city
            FROM "Заказы" o
            JOIN "Авиабилеты" t
                ON t."Код_билета" = o."Авиабилеты_Код_билета"
            JOIN "Клиенты" c
                ON c."Код_клиента" = o."Клиенты_Код_клиента"
            WHERE o."Номер_заказа" = ?
            """,
            (order_id,),
        ).fetchone()

    def insert_order(self, client_id, ticket_id, quantity, discount, order_date):
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO "Заказы" (
                    "Клиенты_Код_клиента",
                    "Авиабилеты_Код_билета",
                    "Количество",
                    "Скидка",
                    "Дата_заказа"
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, ticket_id, quantity, discount, order_date),
            )

    def update_order(self, order_id, client_id, ticket_id, quantity, discount, order_date):
        with self.connection:
            self.connection.execute(
                """
                UPDATE "Заказы"
                SET
                    "Клиенты_Код_клиента" = ?,
                    "Авиабилеты_Код_билета" = ?,
                    "Количество" = ?,
                    "Скидка" = ?,
                    "Дата_заказа" = ?
                WHERE "Номер_заказа" = ?
                """,
                (client_id, ticket_id, quantity, discount, order_date, order_id),
            )

    def delete_order(self, order_id):
        with self.connection:
            self.connection.execute(
                'DELETE FROM "Заказы" WHERE "Номер_заказа" = ?',
                (order_id,),
            )


class mainWindow(QMainWindow):
    def __init__(self, repository):
        super().__init__()
        self.repo = repository
        self.ui = main_interface()
        self.ui.setupUi(self)

        self.current_role = DEFAULT_ROLE
        self.current_login = ""
        self.current_fio = ""

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
        self.ui.tableWidget.cellDoubleClicked.connect(self.edit_tovar)
        self.ui.tableWidget_2.cellDoubleClicked.connect(self.edit_zakaz)

        self._configure_ticket_filter()

    def _configure_ticket_filter(self, selected_text=None):
        types = self.repo.list_ticket_types()
        current_text = selected_text if selected_text is not None else self.ui.comboBox.currentText()

        self.ui.comboBox.blockSignals(True)
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem(TICKET_FILTER_LABEL)
        self.ui.comboBox.addItems(types)

        if current_text and current_text in [TICKET_FILTER_LABEL, *types]:
            self.ui.comboBox.setCurrentText(current_text)
        else:
            self.ui.comboBox.setCurrentIndex(0)

        self.ui.comboBox.blockSignals(False)

    def _is_admin(self):
        return self.current_role == ADMIN_ROLE

    def _selected_ticket_id(self):
        row = self.ui.tableWidget.currentRow()
        if row == -1:
            return None
        item = self.ui.tableWidget.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _selected_order_id(self):
        row = self.ui.tableWidget_2.currentRow()
        if row == -1:
            return None
        item = self.ui.tableWidget_2.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def read_zakaz(self):
        data = self.repo.list_orders()
        self.ui.tableWidget_2.setRowCount(len(data))

        for row_index, row in enumerate(data):
            full_name = " ".join(
                part for part in [row["last_name"], row["first_name"], row["middle_name"]] if part
            )
            values = [
                str(row["ticket_id"]),
                iso_to_display(row["order_date"]),
                iso_to_display(row["departure_date"]),
                row["route"],
                full_name,
                str(row["order_id"]),
                f"Скидка {row['discount']}%, {row['quantity']} шт.",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, int(row["order_id"]))
                self.ui.tableWidget_2.setItem(row_index, column_index, item)

    def search_tovar(self):
        search_text = self.ui.lineEdit.text()
        selected_type = self.ui.comboBox.currentText()

        if self.ui.radioButton_3.isChecked():
            sort_mode = "asc"
        elif self.ui.radioButton.isChecked():
            sort_mode = "desc"
        else:
            sort_mode = "none"

        data = self.repo.list_tickets(search_text, selected_type, sort_mode)
        self.ui.tableWidget.setRowCount(len(data))
        self.ui.tableWidget.setIconSize(QSize(180, 120))
        default_icon = icon_from_relative(DEFAULT_TICKET_ICON)

        for row_index, row in enumerate(data):
            icon_item = QTableWidgetItem()
            icon_item.setIcon(default_icon)
            icon_item.setData(Qt.UserRole, int(row["ticket_id"]))

            summary = (
                f"Авиабилет | Рейс {row['route']}<br>"
                f"Описание товара: Пункт: {row['destination']}, вылет: {iso_to_display(row['departure_date'])}, "
                f"длительность: {row['duration_hours']} ч.<br>"
                f"Производитель: {row['destination']}<br>"
                f"Поставщик: {row['plane_type']}<br>"
            )

            if float(row["discount"]) > 0:
                discounted_price = float(row["price"]) * (100 - float(row["discount"])) / 100
                summary += (
                    f'Цена: <span style="color: red; text-decoration: line-through;">{row["price"]}</span>'
                    f'<span style="color: black; font-weight: bold;">   {discounted_price:.2f}</span><br>'
                )
            else:
                summary += f"Цена: {row['price']}<br>"

            summary += "Единица измерения: билет<br>"
            summary += f"Количество на складе: {row['quantity']}"

            info_label = QLabel()
            info_label.setTextFormat(Qt.RichText)
            info_label.setWordWrap(True)
            info_label.setMargin(6)
            info_label.setText(summary)

            discount_item = QTableWidgetItem(f"{row['discount']}%")
            bg_color = None

            if float(row["discount"]) > 15:
                bg_color = "#2E8B57"
            if int(row["quantity"]) == 0:
                bg_color = "#E0FFFF"

            if bg_color:
                color = QColor(bg_color)
                icon_item.setBackground(color)
                discount_item.setBackground(color)
                info_label.setStyleSheet(f"background-color: {bg_color}; padding: 6px;")
            else:
                info_label.setStyleSheet("padding: 6px;")

            self.ui.tableWidget.setItem(row_index, 0, icon_item)
            self.ui.tableWidget.setCellWidget(row_index, 1, info_label)
            self.ui.tableWidget.setItem(row_index, 2, discount_item)

        self.ui.tableWidget.resizeRowsToContents()
        self._configure_ticket_filter(selected_type)

    def set_roles(self, current_role=DEFAULT_ROLE, current_fio="", current_login=""):
        self.current_role = current_role
        self.current_fio = current_fio
        self.current_login = current_login

        if current_role == MANAGER_ROLE:
            self.ui.label_2.setText(current_fio)
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

        elif current_role == ADMIN_ROLE:
            self.ui.label_2.setText(current_fio)
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

        else:
            self.ui.label_2.setText(DEFAULT_ROLE)
            self.ui.comboBox.setEnabled(False)
            self.ui.lineEdit.setEnabled(False)
            self.ui.pushButton.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.groupBox_2.hide()
            self.ui.pushButton_2.setEnabled(False)
            self.ui.pushButton_4.setEnabled(False)
            self.ui.radioButton.setEnabled(False)
            self.ui.radioButton_2.setEnabled(False)
            self.ui.radioButton_3.setEnabled(False)

        self.search_tovar()

    def logout(self):
        self.hide()
        login_win.ui.lineEdit.clear()
        login_win.ui.lineEdit_2.clear()
        login_win.show()

    def add_tovar(self):
        tovarWindow(self.repo, parent=self).exec_()

    def add_zakaz(self):
        zakazWindow(self.repo, parent=self).exec_()

    def del_tovar(self):
        ticket_id = self._selected_ticket_id()
        if ticket_id is None:
            QMessageBox.critical(self, "Ошибка", "Выберите билет для удаления.", QMessageBox.Ok)
            return

        try:
            self.repo.delete_ticket(ticket_id)
        except ValidationError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc), QMessageBox.Ok)
            return
        except Exception:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить выбранный билет.", QMessageBox.Ok)
            return

        self.search_tovar()
        QMessageBox.information(self, "Информация", "Билет успешно удален.", QMessageBox.Ok)

    def del_zakaz(self):
        order_id = self._selected_order_id()
        if order_id is None:
            QMessageBox.critical(self, "Ошибка", "Выберите заказ для удаления.", QMessageBox.Ok)
            return

        try:
            self.repo.delete_order(order_id)
        except Exception:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить выбранный заказ.", QMessageBox.Ok)
            return

        self.read_zakaz()
        self.search_tovar()
        QMessageBox.information(self, "Информация", "Заказ успешно удален.", QMessageBox.Ok)

    def edit_tovar(self, row, _column):
        if not self._is_admin():
            return
        item = self.ui.tableWidget.item(row, 0)
        if item is None:
            return
        tovarWindow(self.repo, ticket_id=item.data(Qt.UserRole), parent=self).exec_()

    def edit_zakaz(self, row, _column):
        if not self._is_admin():
            return
        item = self.ui.tableWidget_2.item(row, 0)
        if item is None:
            return
        zakazWindow(self.repo, order_id=item.data(Qt.UserRole), parent=self).exec_()


class loginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = login_interface()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.disconnect()
        self.ui.buttonBox.rejected.disconnect()
        self.ui.buttonBox.accepted.connect(self.log)
        self.ui.buttonBox.rejected.connect(self.log_gost)

    def log(self):
        entered_login = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()
        user_data = AUTH_USERS.get(entered_login)

        if user_data and user_data["password"] == password:
            QMessageBox.information(
                self,
                "Информация",
                f"Вы зашли как {user_data['display_name']}.",
                QMessageBox.Ok,
            )
            main_win.set_roles(user_data["role"], user_data["display_name"], entered_login)
        else:
            QMessageBox.information(
                self,
                "Информация",
                "Логин или пароль не найден. Вы зашли как Гость.",
                QMessageBox.Ok,
            )
            main_win.set_roles()

        self.hide()
        main_win.show()

    def log_gost(self):
        QMessageBox.information(self, "Информация", "Вы зашли как Гость.", QMessageBox.Ok)
        self.hide()
        main_win.set_roles()
        main_win.show()


class zakazWindow(QDialog):
    def __init__(self, repository, order_id=None, parent=None):
        super().__init__(parent)
        self.repo = repository
        self.order_id = order_id
        self.ui = zakaz_interface()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.disconnect()
        self.ui.buttonBox.rejected.disconnect()
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.lineEdit.setPlaceholderText("Код билета")
        self.ui.lineEdit_5.setPlaceholderText("Фамилия Имя Отчество или код клиента")
        self.ui.lineEdit_7.setPlaceholderText("Скидка, %")
        self.ui.spinBox_2.setReadOnly(True)
        self.ui.lineEdit_8.setReadOnly(True)
        self.ui.lineEdit_4.setReadOnly(True)
        self.ui.dateEdit_2.setEnabled(False)

        completer = QCompleter([client_display_name(row) for row in self.repo.list_clients()], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.lineEdit_5.setCompleter(completer)

        self.ui.lineEdit.textChanged.connect(self._refresh_ticket_preview)
        self.ui.lineEdit_5.textChanged.connect(self._refresh_client_preview)

        if self.order_id is None:
            self.ui.spinBox_2.setValue(self.repo.next_order_id())
            self.ui.dateEdit.setDate(QDate.currentDate())
            self.ui.dateEdit_2.setDate(QDate.currentDate())
        else:
            self._load_order()

    def _load_order(self):
        order = self.repo.get_order(self.order_id)
        if order is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить выбранный заказ.", QMessageBox.Ok)
            self.reject()
            return

        self.ui.lineEdit.setText(str(order["ticket_id"]))
        self.ui.dateEdit.setDate(qdate_from_iso(order["order_date"]))
        self.ui.dateEdit_2.setDate(qdate_from_iso(order["departure_date"]))
        self.ui.lineEdit_4.setText(str(order["route"]))

        client_name = " ".join(
            part for part in [order["last_name"], order["first_name"], order["middle_name"]] if part
        )
        self.ui.lineEdit_5.setText(client_name)
        self.ui.spinBox_2.setValue(int(order["order_id"]))
        self.ui.lineEdit_7.setText(str(order["discount"]))
        self.ui.lineEdit_8.setText(str(order["client_id"]))
        self.ui.spinBox.setValue(int(order["quantity"]))

    def _refresh_ticket_preview(self):
        ticket_value = self.ui.lineEdit.text().strip()
        if not ticket_value.isdigit():
            self.ui.lineEdit_4.clear()
            self.ui.dateEdit_2.setDate(QDate.currentDate())
            return

        ticket = self.repo.get_ticket(int(ticket_value))
        if ticket is None:
            self.ui.lineEdit_4.clear()
            self.ui.dateEdit_2.setDate(QDate.currentDate())
            return

        self.ui.lineEdit_4.setText(ticket["Маршрут"])
        self.ui.dateEdit_2.setDate(qdate_from_iso(ticket["Дата_вылета"]))

    def _refresh_client_preview(self):
        client_row = self.repo.resolve_client(self.ui.lineEdit_5.text())
        self.ui.lineEdit_8.setText("" if client_row is None else str(client_row["Код_клиента"]))

    def _collect_payload(self):
        ticket_text = self.ui.lineEdit.text().strip()
        if not ticket_text.isdigit():
            raise ValidationError("Укажите корректный код билета.")

        ticket_id = int(ticket_text)
        if self.repo.get_ticket(ticket_id) is None:
            raise ValidationError("Билет с указанным кодом не найден.")

        client_row = self.repo.resolve_client(self.ui.lineEdit_5.text())
        if client_row is None:
            raise ValidationError("Клиент не найден. Используйте ФИО или код клиента.")

        discount_text = self.ui.lineEdit_7.text().strip().replace("%", "").replace(",", ".")
        if discount_text:
            try:
                discount = float(discount_text)
            except ValueError as exc:
                raise ValidationError("Скидка должна быть числом.") from exc
        else:
            discount = 0.0

        if discount < 0:
            raise ValidationError("Скидка не может быть отрицательной.")

        return {
            "ticket_id": ticket_id,
            "client_id": int(client_row["Код_клиента"]),
            "quantity": int(self.ui.spinBox.value()),
            "discount": discount,
            "order_date": self.ui.dateEdit.date().toString("yyyy-MM-dd"),
        }

    def save(self):
        try:
            payload = self._collect_payload()
            if self.order_id is None:
                self.repo.insert_order(**payload)
                message = "Заказ успешно добавлен."
            else:
                self.repo.update_order(order_id=self.order_id, **payload)
                message = "Информация о заказе успешно изменена."
        except ValidationError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc), QMessageBox.Ok)
            return
        except sqlite3.IntegrityError:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось сохранить заказ. Проверьте корректность данных.",
                QMessageBox.Ok,
            )
            return

        QMessageBox.information(self, "Информация", message, QMessageBox.Ok)
        main_win.read_zakaz()
        main_win.search_tovar()
        self.accept()


class tovarWindow(QDialog):
    def __init__(self, repository, ticket_id=None, parent=None):
        super().__init__(parent)
        self.repo = repository
        self.ticket_id = ticket_id
        self.ui = tovar_interface()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.disconnect()
        self.ui.buttonBox.rejected.disconnect()
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.pushButton.setEnabled(False)
        self.ui.lineEdit_11.setEnabled(False)
        self.ui.lineEdit.setPlaceholderText("Код билета")
        self.ui.lineEdit_2.setPlaceholderText("Маршрут")
        self.ui.lineEdit_3.setPlaceholderText("Конечный пункт")
        self.ui.lineEdit_5.setPlaceholderText("Тип самолета")
        self.ui.lineEdit_10.setPlaceholderText("Дата вылета (YYYY-MM-DD)")
        self.ui.spinBox_2.setMinimum(1)
        self.ui.spinBox_2.setMaximum(48)
        self.ui.spinBox.setReadOnly(True)
        self.ui.spinBox.setEnabled(False)

        self.ui.comboBox.blockSignals(True)
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem("")
        self.ui.comboBox.addItems(self.repo.list_destinations())
        self.ui.comboBox.blockSignals(False)

        self.ui.comboBox_2.blockSignals(True)
        self.ui.comboBox_2.clear()
        self.ui.comboBox_2.addItem("")
        self.ui.comboBox_2.addItems(self.repo.list_ticket_types())
        self.ui.comboBox_2.blockSignals(False)

        self.ui.comboBox.currentTextChanged.connect(self._apply_destination_hint)
        self.ui.comboBox_2.currentTextChanged.connect(self._apply_plane_hint)

        if self.ticket_id is None:
            self.ui.lineEdit.setText(str(self.repo.next_ticket_id()))
            self.ui.lineEdit_10.setText(QDate.currentDate().toString("yyyy-MM-dd"))
            self.ui.spinBox.setValue(0)
        else:
            self._load_ticket()

    def _apply_destination_hint(self, value):
        if value and not self.ui.lineEdit_3.text().strip():
            self.ui.lineEdit_3.setText(value)

    def _apply_plane_hint(self, value):
        if value and not self.ui.lineEdit_5.text().strip():
            self.ui.lineEdit_5.setText(value)

    def _load_ticket(self):
        ticket = self.repo.get_ticket(self.ticket_id)
        if ticket is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить выбранный билет.", QMessageBox.Ok)
            self.reject()
            return

        self.ui.lineEdit.setText(str(ticket["Код_билета"]))
        self.ui.lineEdit.setReadOnly(True)
        self.ui.lineEdit_2.setText(ticket["Маршрут"])
        self.ui.lineEdit_3.setText(ticket["Конечный_пункт"])
        self.ui.doubleSpinBox.setValue(float(ticket["Цена"]))
        self.ui.lineEdit_5.setText(ticket["Тип_самолета"])
        self.ui.comboBox_2.setCurrentText(ticket["Тип_самолета"])
        self.ui.comboBox.setCurrentText(ticket["Конечный_пункт"])
        self.ui.spinBox_2.setValue(int(ticket["Продолжительность_полета"]))
        self.ui.spinBox.setValue(self.repo.ticket_sales_count(self.ticket_id))
        self.ui.lineEdit_10.setText(ticket["Дата_вылета"])

    def _collect_payload(self):
        ticket_text = self.ui.lineEdit.text().strip()
        if not ticket_text:
            ticket_id = None
        elif ticket_text.isdigit():
            ticket_id = int(ticket_text)
        else:
            raise ValidationError("Код билета должен быть числом.")

        route = self.ui.lineEdit_2.text().strip()
        destination = self.ui.lineEdit_3.text().strip() or self.ui.comboBox.currentText().strip()
        plane_type = self.ui.lineEdit_5.text().strip() or self.ui.comboBox_2.currentText().strip()
        departure_date = normalize_iso_date(self.ui.lineEdit_10.text())
        duration_hours = int(self.ui.spinBox_2.value())
        price = float(self.ui.doubleSpinBox.value())

        if not route:
            raise ValidationError("Укажите маршрут.")
        if not destination:
            raise ValidationError("Укажите конечный пункт.")
        if not plane_type:
            raise ValidationError("Укажите тип самолета.")
        if duration_hours <= 0:
            raise ValidationError("Продолжительность полета должна быть больше нуля.")
        if price <= 0:
            raise ValidationError("Цена должна быть больше нуля.")

        return {
            "ticket_id": ticket_id,
            "route": route,
            "destination": destination,
            "plane_type": plane_type,
            "departure_date": departure_date,
            "duration_hours": duration_hours,
            "price": price,
        }

    def save(self):
        try:
            payload = self._collect_payload()
            if self.ticket_id is None:
                self.repo.insert_ticket(**payload)
                message = "Билет успешно добавлен."
            else:
                payload.pop("ticket_id", None)
                self.repo.update_ticket(ticket_id=self.ticket_id, **payload)
                message = "Информация о билете успешно изменена."
        except ValidationError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc), QMessageBox.Ok)
            return
        except sqlite3.IntegrityError:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось сохранить билет. Проверьте корректность данных.",
                QMessageBox.Ok,
            )
            return

        QMessageBox.information(self, "Информация", message, QMessageBox.Ok)
        main_win.search_tovar()
        main_win.read_zakaz()
        self.accept()


repository = None
main_win = None
login_win = None


def run_app():
    global repository, main_win, login_win

    app = QApplication(sys.argv)
    app.addLibraryPath(str(QT_PLUGIN_ROOT))
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setFont(QFont("Times New Roman", 12))

    try:
        repository = Repository(locate_database_path())
    except Exception as error:
        QMessageBox.critical(None, "Ошибка", f"Не удалось открыть Polet.db:\n{error}", QMessageBox.Ok)
        sys.exit(1)

    main_win = mainWindow(repository)
    login_win = loginWindow()
    login_win.show()

    exit_code = app.exec_()
    repository.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    run_app()
