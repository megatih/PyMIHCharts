"""
Manager for persistent storage of recently used ticker symbols.

Handles reading and writing to an XML file in the platform's 
recommended configuration directory.
"""

import os
import xml.etree.ElementTree as ET
from typing import List, Dict
from PySide6.QtCore import QStandardPaths

class RecentSymbolsManager:
    """
    Manages a list of symbols and their usage counts, persisted in XML.
    """
    
    def __init__(self, filename: str = "recentsymbols.xml"):
        self.filename = filename
        self.config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        self.file_path = os.path.join(self.config_dir, self.filename)
        self.symbols_data: Dict[str, int] = {}
        
        self._ensure_config_dir()
        self.load_symbols()

    def _ensure_config_dir(self):
        """Creates the configuration directory if it doesn't exist."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def load_symbols(self):
        """Reads the symbol popularity data from the XML file."""
        if not os.path.exists(self.file_path):
            self.symbols_data = {}
            return

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            data = {}
            for symbol_elem in root.findall('symbol'):
                name = symbol_elem.get('name')
                count = int(symbol_elem.get('count', 0))
                if name:
                    data[name.upper()] = count
            self.symbols_data = data
        except (ET.ParseError, ValueError, Exception):
            # If the file is corrupted, start fresh
            self.symbols_data = {}

    def save_symbols(self):
        """Writes the symbol popularity data to the XML file."""
        root = ET.Element("recentsymbols")
        for name, count in self.symbols_data.items():
            symbol_elem = ET.SubElement(root, "symbol")
            symbol_elem.set("name", name)
            symbol_elem.set("count", str(count))

        tree = ET.ElementTree(root)
        try:
            tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            print(f"Error saving recent symbols: {e}")

    def increment_symbol(self, symbol: str):
        """Increments the count for a symbol and saves changes."""
        symbol = symbol.upper().strip()
        if not symbol:
            return

        self.symbols_data[symbol] = self.symbols_data.get(symbol, 0) + 1
        self.save_symbols()

    def get_top_symbols(self, limit: int = 20) -> List[str]:
        """Returns the top symbols ordered by popularity count."""
        sorted_symbols = sorted(
            self.symbols_data.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
        return [symbol for symbol, count in sorted_symbols[:limit]]
