from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton


class ConfirmAccountWindow(QMainWindow):
    """this class sets up the window that displays the confirm account widget"""

    def __init__(self):
        super(ConfirmAccountWindow, self).__init__()
        self.form_widget = ConfirmAccountWidget(self)
        self.setCentralWidget(self.form_widget)


class ConfirmAccountWidget(QWidget):
    """this class sets up the design for the confirm account window"""

    def __init__(self, parent):
        super(ConfirmAccountWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        label_text = 'Paste the link from the web browser after logging into spotify\n(should be a google url):'
        self.layout.addWidget(QLabel(label_text))
        self.text_field = QLineEdit()
        self.layout.addWidget(self.text_field)
        self.button = QPushButton('Confirm Account')
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
