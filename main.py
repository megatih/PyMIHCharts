"""
Entry point for the PyMIHCharts application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from models.data_manager import DataManager
from views.main_view import MainView
from controllers.main_controller import MainController


def main():
    """
    Initializes and starts the application using the MVC pattern.
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    
    # Initialize MVC components
    model = DataManager()
    view = MainView()
    controller = MainController(model, view)
    
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()