import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
app.setApplicationName("Juana Cash")
app.setStyle("Fusion")
window = MainWindow()
window.show()
sys.exit(app.exec())