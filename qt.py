#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton,
                             QHBoxLayout, QVBoxLayout, QApplication, QDialog, QComboBox)

import itsdownloading


class Login(QDialog):
    def __init__(self):
        super().__init__()

        self.username = QLineEdit(self)
        self.password = QLineEdit(self)
        self.school = QComboBox()
        self.school.addItems(['ntnu', 'hist'])
        self.password.setEchoMode(QLineEdit.Password)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.login)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(QtCore.QCoreApplication.instance().quit)

        self.status = QLabel()

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.school)
        hbox.addWidget(ok_button)
        hbox.addWidget(cancel_button)

        vbox = QVBoxLayout()

        self.setLayout(vbox)

        vbox.addStretch(1)
        vbox.addWidget(QLabel('Username'))
        vbox.addWidget(self.username)
        vbox.addWidget(QLabel('Password'))
        vbox.addWidget(self.password)
        vbox.addWidget(self.status)
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.setWindowTitle('Login')
        self.show()

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Login()
    sys.exit(app.exec_())
