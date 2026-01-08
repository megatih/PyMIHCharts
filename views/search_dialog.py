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
        self.resize(400, 300)
        self.selected_symbol = None
        self.results = results or []
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Symbol not found. Did you mean one of these?"))
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
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
            # If nothing selected but OK clicked, maybe just close?
            # Or enforce selection? Let's treat as cancel if nothing selected.
            super().reject()
