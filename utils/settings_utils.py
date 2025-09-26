"""
Settings utilities for application configuration management.
Handles theme preferences, folder paths, and user settings persistence.
"""

import os
import json


# Theme color definitions
LIGHT_THEME = {
    "bg": "#f0f0f0",
    "fg": "#000000",
    "treeview_bg": "#ffffff",
    "treeview_fg": "#000000",
    "treeview_selected_bg": "#0078d7",
    "treeview_selected_fg": "#ffffff",
    "entry_bg": "#ffffff",
    "entry_fg": "#000000",
    "button_bg": "#e1e1e1",
    "button_fg": "#000000",
    "menu_bg": "#f0f0f0",
    "menu_fg": "#000000",
    "listbox_bg": "#ffffff",
    "listbox_fg": "#000000",
    "drag_label_bg": "lightblue",
    "drag_label_fg": "#000000",
    "status_bg": "#f0f0f0",
    "status_fg": "#000000"
}

DARK_THEME = {
    "bg": "#2d2d2d",
    "fg": "#ffffff",
    "treeview_bg": "#3d3d3d",
    "treeview_fg": "#ffffff",
    "treeview_selected_bg": "#0078d7",
    "treeview_selected_fg": "#ffffff",
    "entry_bg": "#3d3d3d",
    "entry_fg": "#ffffff",
    "button_bg": "#4d4d4d",
    "button_fg": "#ffffff",
    "menu_bg": "#2d2d2d",
    "menu_fg": "#ffffff",
    "listbox_bg": "#3d3d3d",
    "listbox_fg": "#ffffff",
    "drag_label_bg": "#0078d7",
    "drag_label_fg": "#ffffff",
    "status_bg": "#2d2d2d",
    "status_fg": "#ffffff"
}


class SettingsManager:
    """Manages application settings and preferences."""

    def __init__(self):
        # Settings file path - store in user's documents folder
        user_docs = os.path.expanduser("~")  # User home directory
        app_folder = os.path.join(user_docs, "VideoSubRenamer")

        # Create app folder if it doesn't exist
        if not os.path.exists(app_folder):
            try:
                os.makedirs(app_folder)
                print("Debug: Created application settings folder")
            except Exception as e:
                print(f"Debug: Failed to create application folder: {str(e)}")

        self.settings_file = os.path.join(app_folder, "settings.json")

    def load_theme_preference(self):
        """Load saved theme preference."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    dark_theme = settings.get('dark_theme', False)
                    print(f"Debug: Loaded theme preference - dark: {dark_theme}")
                    return dark_theme
        except Exception as e:
            print(f"Debug: Error loading theme preference: {str(e)}")
        return False

    def save_theme_preference(self, is_dark_theme):
        """Save theme preference."""
        try:
            settings = self._load_all_settings()
            settings['dark_theme'] = is_dark_theme
            self._save_all_settings(settings)
            print(f"Debug: Saved theme preference - dark: {is_dark_theme}")
        except Exception as e:
            print(f"Debug: Error saving theme preference: {str(e)}")

    def load_folder_path(self):
        """Load saved folder path."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    folder_path = settings.get('last_folder', '')
                    print(f"Debug: Loaded folder path: {folder_path}")
                    return folder_path
        except Exception as e:
            print(f"Debug: Error loading folder path: {str(e)}")
        return ''

    def save_folder_path(self, folder_path):
        """Save folder path."""
        try:
            settings = self._load_all_settings()
            settings['last_folder'] = folder_path
            self._save_all_settings(settings)
            print(f"Debug: Saved folder path: {folder_path}")
        except Exception as e:
            print(f"Debug: Error saving folder path: {str(e)}")

    def load_skip_x_preference(self):
        """Load preference for skipping x-prefixed files."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    skip_x = settings.get('skip_x_files', False)
                    print(f"Debug: Loaded skip x-files preference: {skip_x}")
                    return skip_x
        except Exception as e:
            print(f"Debug: Error loading skip x-files preference: {str(e)}")
        return False

    def save_skip_x_preference(self, skip_x_files):
        """Save preference for skipping x-prefixed files."""
        try:
            settings = self._load_all_settings()
            settings['skip_x_files'] = skip_x_files
            self._save_all_settings(settings)
            print(f"Debug: Saved skip x-files preference: {skip_x_files}")
        except Exception as e:
            print(f"Debug: Error saving skip x-files preference: {str(e)}")

    def _load_all_settings(self):
        """Load all settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Debug: Error loading settings file: {str(e)}")
        return {}

    def _save_all_settings(self, settings):
        """Save all settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Debug: Error saving settings file: {str(e)}")

    def get_current_theme(self, is_dark_theme):
        """Get the current theme colors based on preference."""
        return DARK_THEME if is_dark_theme else LIGHT_THEME