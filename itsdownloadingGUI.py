import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.init_window()
        self.show()

    def init_window(self):
        self.setWindowTitle('Itsdownloading')
        self.setWindowIcon(QIcon('itsdownloading.ico'))


app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())
