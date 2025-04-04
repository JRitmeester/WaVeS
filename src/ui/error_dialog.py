from PyQt5.QtWidgets import QMessageBox

class ErrorDialog(QMessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QMessageBox.Critical)
        self.setText("Error")
        self.setInformativeText('More information')
        self.setWindowTitle("Error")
        self.exec_()
