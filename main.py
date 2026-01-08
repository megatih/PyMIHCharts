"""
Entry point for the PyMIHCharts application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from models.data_manager import DataManager
from views.main_view import MainView
from controllers.main_controller import MainController


def main():
    """
    Initializes and starts the application using the MVC pattern.
    """
    # High DPI scaling policy
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setFont(QFont("sans-serif", 9))
    
    # Initialize MVC components
    model = DataManager()
    view = MainView()
    controller = MainController(model, view)
    
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
