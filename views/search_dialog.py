"""
Dialog to present symbol search results to the user.

Provides a selection interface when the user enters an ambiguous 
or incorrect ticker symbol.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, 
                             QDialogButtonBox, QLabel, QListWidgetItem, QWidget)
from PySide6.QtCore import Qt

class SymbolSearchDialog(QDialog):
    """
    A modal dialog that presents a list of suggested symbols from Yahoo Finance.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, results: Optional[List[Dict[str, Any]]] = None):
        """
        Initializes the dialog with search suggestions.
        
        Args:
            parent: The parent window for modal behavior.
            results: A list of result dictionaries from yfinance Search.
        """
        super().__init__(parent)
        self.setWindowTitle("Symbol Search")
        self.resize(500, 350)
        self.selected_symbol: Optional[str] = None
        self.results = results or []
        
        self._init_ui()

    def _init_ui(self):
        """Builds the suggestion list and control buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        message = QLabel("The symbol was not found. Please select one of the following suggestions:")
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Display the suggestions in a scrollable list
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
        # Apply slight padding for better readability on high-DPI screens
        self.list_widget.setStyleSheet("QListWidget::item { padding: 8px; }")
        layout.addWidget(self.list_widget)
        
        # Populate the list with formatted item details
        for item in self.results:
            symbol = item.get('symbol', 'Unknown')
            name = item.get('shortname', item.get('longname', ''))
            exch = item.get('exchange', '')
            type_disp = item.get('typeDisp', '')
            
            display_text = f"{symbol} - {name} ({exch} {type_disp})"
            list_item = QListWidgetItem(display_text)
            # Store the raw symbol in UserRole for easy retrieval on selection
            list_item.setData(Qt.UserRole, symbol)
            self.list_widget.addItem(list_item)

        # Pre-select the top result for convenience
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        # Standard OK/Cancel button box
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        """Overrides QDialog.accept to capture the selected symbol before closing."""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_symbol = current_item.data(Qt.UserRole)
            super().accept()
        else:
            # Prevent closing with 'OK' if no item is selected
            super().reject()