"""
Dialog to present symbol search results to the user.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, 
                             QDialogButtonBox, QLabel, QListWidgetItem)
from PySide6.QtCore import Qt

class SymbolSearchDialog(QDialog):
    def __init__(self, parent=None, results=None):
        super().__init__(parent)
        self.setWindowTitle("Symbol Search")
        self.resize(500, 350)
        self.selected_symbol = None
        self.results = results or []
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        message = QLabel("The symbol was not found. Please select one of the following suggestions:")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
        # Set a bit more padding for items
        self.list_widget.setStyleSheet("QListWidget::item { padding: 8px; }")
        layout.addWidget(self.list_widget)
        
        for item in self.results:
            symbol = item.get('symbol', 'Unknown')
            name = item.get('shortname', item.get('longname', ''))
            exch = item.get('exchange', '')
            type_disp = item.get('typeDisp', '')
            
            display_text = f"{symbol} - {name} ({exch} {type_disp})"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, symbol)
            self.list_widget.addItem(list_item)

        # Select first item by default
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_symbol = current_item.data(Qt.UserRole)
            super().accept()
        else:
            super().reject()
