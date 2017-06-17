#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton,
                             QHBoxLayout, QVBoxLayout, QApplication, QDialog, QComboBox, QListWidget,
                             QAbstractItemView, QWidget, QListWidgetItem)

import itsdownloading


class Login(QDialog):
    def __init__(self):
        super().__init__()

        self.username = QLineEdit(self)
        self.password = QLineEdit(self)
        self.school = QComboBox()
        self.school.addItems(['ntnu', 'hist'])
        self.password.setEchoMode(QLineEdit.Password)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.login)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.status = QLabel()
        self.setWindowTitle('Login')
        self.setWindowIcon(QIcon('itsdownloading.ico'))

        self.build_layout()

    def build_layout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(self.school)
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(QLabel('Username'))
        vbox.addWidget(self.username)
        vbox.addWidget(QLabel('Password'))
        vbox.addWidget(self.password)
        vbox.addWidget(self.status)
        vbox.addLayout(hbox)
        vbox.addStretch(1)
        self.setLayout(vbox)

    def login(self):
        itsdownloading.settings.set_school_and_base_url(self.school.currentText())
        self.status.setText('Contacting {}'.format(itsdownloading.settings.base_url))
        self.status.setStyleSheet('QLabel { }')
        app.processEvents()
        if itsdownloading.attempt_login(self.username.text(), self.password.text()):
            self.status.setText('Successfully logged in')
            self.status.setStyleSheet('QLabel { color : green; }')
            self.accept()
        else:
            self.status.setText('Invalid username or password')
            self.status.setStyleSheet('QLabel { color : red; }')


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.courses = QListWidget()
        self.courses.setSelectionMode(QAbstractItemView.MultiSelection)
        self.download_button = QPushButton('Download')
        self.download_button.clicked.connect(self.download)

        self.setWindowIcon(QIcon('itsdownloading.ico'))

        self.build_layout()
        self.update_list()

    def build_layout(self):
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(self.download_button)

        vbox.addWidget(self.courses)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def update_list(self):
        for item in itsdownloading.get_courses_and_projects().items():
            self.courses.addItem(CourseOrProject(item))

    def download(self):
        for selected in self.courses.selectedItems():
            itsdownloading.download_course_or_project(selected.url)


class CourseOrProject(QListWidgetItem):
    def __init__(self, item: tuple):
        name, self.url = item
        super().__init__(name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = Login()
    if login.exec_():
        window = Window()
        window.show()
        sys.exit(app.exec_())
