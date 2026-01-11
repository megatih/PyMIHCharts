"""
Manager for persistent storage of recently used ticker symbols.

This module handles reading and writing symbol popularity data to a JSON file
located in the platform's standard application configuration directory.
"""

import os
import json
from typing import List, Dict
from PySide6.QtCore import QStandardPaths

class RecentSymbolsManager:
    """
    Manages a list of symbols and their usage counts, persisted in JSON.
    
    This class handles the transition from legacy XML storage to JSON and
    provides a popularity-based retrieval system for the UI.
    """
    
    def __init__(self, filename: str = "recentsymbols.json"):
        """
        Initializes the manager and performs data migration if necessary.
        
        Args:
            filename: The name of the JSON file to store data in.
        """
        self.filename = filename
        self.config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        self.file_path = os.path.join(self.config_dir, self.filename)
        self.symbols_data: Dict[str, int] = {}
        
        self._ensure_config_dir()
        self._cleanup_legacy_xml()
        self.load_symbols()

    def _ensure_config_dir(self):
        """Creates the configuration directory if it doesn't exist."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def _cleanup_legacy_xml(self):
        """
        Removes the old XML configuration file if it exists.
        Transitioning to JSON for better maintainability and nested data support.
        """
        old_xml_path = os.path.join(self.config_dir, "recentsymbols.xml")
        if os.path.exists(old_xml_path):
            try:
                os.remove(old_xml_path)
            except Exception as e:
                print(f"Note: Could not remove legacy XML file: {e}")

    def load_symbols(self):
        """Reads the symbol popularity data from the JSON file."""
        if not os.path.exists(self.file_path):
            self.symbols_data = {}
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.symbols_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            # Fallback to empty if file is corrupt
            self.symbols_data = {}

    def save_symbols(self):
        """Writes the symbol popularity data to the JSON file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.symbols_data, f, indent=4)
        except Exception as e:
            # Minimal logging as per operational guidelines
            print(f"Error saving recent symbols: {e}")

    def increment_symbol(self, symbol: str):
        """
        Increments the usage count for a specific symbol.
        
        Args:
            symbol: Ticker symbol string.
        """
        symbol = symbol.upper().strip()
        if not symbol:
            return

        self.symbols_data[symbol] = self.symbols_data.get(symbol, 0) + 1
        self.save_symbols()

    def get_top_symbols(self, limit: int = 20) -> List[str]:
        """
        Retrieves symbols sorted by their popularity (usage count).
        
        Args:
            limit: Maximum number of symbols to return.
            
        Returns:
            List of ticker symbols.
        """
        sorted_symbols = sorted(
            self.symbols_data.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
        return [symbol for symbol, count in sorted_symbols[:limit]]