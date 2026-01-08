"""
Entry point for the PyMIHCharts application.

This script initializes the Qt application environment, sets up the 
Model-View-Controller (MVC) components, and enters the main event loop.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from models.data_manager import DataManager
from views.main_view import MainView
from controllers.main_controller import MainController


def main():
    """
    Main execution routine for PyMIHCharts.
    
    1. Sets up High-DPI scaling policies.
    2. Initializes the QApplication.
    3. Bootstraps the Model, View, and Controller.
    4. Displays the Main Window and starts the event loop.
    """
    
    # Enable crisp rendering on High-DPI displays (e.g., Retina, 4K)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # --- MVC Initialization ---
    
    # 1. Model: Manages data state and background workers
    model = DataManager()
    
    # 2. View: The top-level GUI container
    view = MainView()
    
    # 3. Controller: Connects Model and View through Signals/Slots
    # The controller is responsible for initial data loading and theme application
    controller = MainController(model, view)
    
    # Show the window and start the Qt event loop
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()