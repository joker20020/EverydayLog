from dotenv import load_dotenv
from ui import StartWindow
from qfluentwidgets import (
    setTheme,
    Theme
)
from PySide6.QtWidgets import QApplication

# env init
load_dotenv()


if __name__ == "__main__":

    app = QApplication()
    setTheme(Theme.AUTO)
    w = StartWindow()
    w.show()
    app.exec()

