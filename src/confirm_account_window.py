from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from src.util import resource_path
from os.path import join
from PyQt5.QtGui import QIcon


class ConfirmAccountWindow(QMainWindow):
    """this class sets up the window that displays the confirm account widget"""

    def __init__(self):
        super(ConfirmAccountWindow, self).__init__()
        self.form_widget = ConfirmAccountWidget(self)
        self.setCentralWidget(self.form_widget)
        self.setWindowIcon(QIcon(resource_path(join('assets', 'icon.png'))))


class ConfirmAccountWidget(QWidget):
    """this class sets up the UI for the confirm account window"""

    def __init__(self, parent):
        super(ConfirmAccountWidget, self).__init__(parent)
        self.text_field = QLineEdit()
        self.button = QPushButton('Confirm Account')

        label_text = 'Paste the link from the web browser after logging into spotify\n(should be a google url):'
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel(label_text))
        self.layout.addWidget(self.text_field)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)
