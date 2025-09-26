"""
Main window for the video subtitle renamer application.
Integrates all UI components and business logic.
"""

import tkinter as tk
from tkinter import messagebox

from utils.settings_utils import SettingsManager
from utils.subtitle_utils import SubtitleItem, parse_srt, format_time, compose_srt
from core.matcher import FileMatcher
from ui.components import UIComponents


class VideoSubRenamerApp:
    """Main application window integrating all components."""

    def __init__(self):
        try:
            # Initialize root window
            self.root = tk.Tk()
            self.root.title("Video Altyazı Yeniden Adlandırıcı")
            self.root.geometry("800x600")
            self.root.resizable(True, True)

            # Initialize managers
            self.settings_manager = SettingsManager()
            self.matcher = FileMatcher()
            self.ui = UIComponents(self.root, self.settings_manager, self.matcher)

            # Setup UI
            self.ui.setup_ui()

            # Apply initial theme
            self.ui.apply_theme()

            # Load last folder path and auto-scan
            last_folder = self.settings_manager.load_folder_path()
            if last_folder:
                self.ui.folder_path_var.set(last_folder)
                # Auto-scan will be handled by UIComponents

            print("Debug: VideoSubRenamerApp initialized successfully")

        except Exception as e:
            print(f"Debug: Error initializing VideoSubRenamerApp: {str(e)}")
            messagebox.showerror("Başlatma Hatası", f"Uygulama başlatılırken hata oluştu: {str(e)}")

    def run(self):
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Debug: Error in main loop: {str(e)}")

    # UI event handler implementations
    def manual_match(self):
        """Handle manual match selection."""
        try:
            # Get selected item
            selected_item = self.ui.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir dosya seçin.")
                return

            # Get selected values
            values = self.ui.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Show manual match dialog
            self.show_manual_match_dialog(video_file, subtitle_file)

        except Exception as e:
            print(f"Debug: Error in manual match: {str(e)}")
            messagebox.showerror("Hata", f"Manuel eşleştirme hatası: {str(e)}")

    def remove_match(self):
        """Handle match removal."""
        try:
            # Get selected item
            selected_item = self.ui.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.ui.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Remove match if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.ui.folder_path_var.get()
                self.matcher.remove_match(folder_path, video_file, subtitle_file)
                self.ui.display_matches()
                self.ui.status_var.set(f"'{video_file}' ve '{subtitle_file}' eşleştirmesi kaldırıldı.")
            else:
                messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

        except Exception as e:
            print(f"Debug: Error removing match: {str(e)}")
            messagebox.showerror("Hata", f"Eşleştirme kaldırma hatası: {str(e)}")

    def sync_subtitle(self):
        """Handle manual subtitle synchronization."""
        try:
            # Get selected item
            selected_item = self.ui.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.ui.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Sync if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.ui.folder_path_var.get()
                if not folder_path:
                    messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                    return

                subtitle_path = os.path.join(folder_path, subtitle_file)

                # Check subtitle file exists
                if not os.path.exists(subtitle_path):
                    messagebox.showerror("Hata", f"Altyazı dosyası bulunamadı: {subtitle_file}")
                    return

                # Show sync dialog
                self.show_sync_dialog(subtitle_path, subtitle_file)
            else:
                messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

        except Exception as e:
            print(f"Debug: Error syncing subtitle: {str(e)}")
            messagebox.showerror("Hata", f"Altyazı senkronizasyon hatası: {str(e)}")

    def auto_sync_subtitle(self):
        """Handle automatic subtitle synchronization."""
        try:
            # Get selected item
            selected_item = self.ui.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.ui.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Auto sync if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.ui.folder_path_var.get()
                if not folder_path:
                    messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                    return

                subtitle_path = os.path.join(folder_path, subtitle_file)
                video_path = os.path.join(folder_path, video_file)

                # Check files exist
                if not os.path.exists(subtitle_path):
                    messagebox.showerror("Hata", f"Altyazı dosyası bulunamadı: {subtitle_file}")
                    return
                if not os.path.exists(video_path):
                    messagebox.showerror("Hata", f"Video dosyası bulunamadı: {video_file}")
                    return

                # Perform auto sync
                self.perform_auto_sync(video_path, subtitle_path, subtitle_file)
            else:
                messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

        except Exception as e:
            print(f"Debug: Error auto syncing subtitle: {str(e)}")
            messagebox.showerror("Hata", f"Otomatik senkronizasyon hatası: {str(e)}")

    def show_context_menu(self, event):
        """Show context menu on right-click."""
        try:
            # Select clicked item
            item = self.ui.file_tree.identify_row(event.y)
            if item:
                self.ui.file_tree.selection_set(item)
                self.ui.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Debug: Error showing context menu: {str(e)}")

    def on_drag_start(self, event):
        """Handle drag start event."""
        try:
            item = self.ui.file_tree.identify_row(event.y)
            if item:
                self.ui.drag_source_item = item
                self.ui.drag_source_values = self.ui.file_tree.item(item, "values")
                self.ui.drag_data["item"] = item
                self.ui.drag_data["x"] = event.x
                self.ui.drag_data["y"] = event.y

                # Create drag label
                values = self.ui.drag_source_values
                label_text = f"{values[0]} -> {values[1]}" if values[0] and values[1] else values[0] or values[1]
                self.ui.drag_label = tk.Label(self.root, text=label_text,
                                             bg=self.ui.current_theme["drag_label_bg"],
                                             fg=self.ui.current_theme["drag_label_fg"])
                self.ui.drag_label.place(x=event.x_root, y=event.y_root)

        except Exception as e:
            print(f"Debug: Error in drag start: {str(e)}")

    def on_drag_motion(self, event):
        """Handle drag motion event."""
        try:
            if self.ui.drag_label:
                self.ui.drag_label.place(x=event.x_root + 10, y=event.y_root + 10)
        except Exception as e:
            print(f"Debug: Error in drag motion: {str(e)}")

    def on_drag_release(self, event):
        """Handle drag release event."""
        try:
            if self.ui.drag_label:
                self.ui.drag_label.destroy()
                self.ui.drag_label = None

            # Check if dropped on valid target
            item = self.ui.file_tree.identify_row(event.y)
            if item and item != self.ui.drag_source_item:
                target_values = self.ui.file_tree.item(item, "values")

                # Perform manual match if valid drag-drop
                source_video = self.ui.drag_source_values[0]
                source_sub = self.ui.drag_source_values[1]
                target_video = target_values[0]
                target_sub = target_values[1]

                # Determine match direction
                if source_video and target_sub and not target_video:
                    # Video to subtitle
                    self.create_manual_match(source_video, target_sub)
                elif source_sub and target_video and not target_sub:
                    # Subtitle to video
                    self.create_manual_match(target_video, source_sub)

            # Reset drag data
            self.ui.drag_source_item = None
            self.ui.drag_source_values = None
            self.ui.drag_data = {"item": None, "x": 0, "y": 0}

        except Exception as e:
            print(f"Debug: Error in drag release: {str(e)}")

    def create_manual_match(self, video_file, subtitle_file):
        """Create a manual match between video and subtitle."""
        try:
            folder_path = self.ui.folder_path_var.get()
            if not folder_path:
                return

            self.matcher.create_match(folder_path, video_file, subtitle_file)
            self.ui.display_matches()
            self.ui.status_var.set(f"'{video_file}' ve '{subtitle_file}' manuel olarak eşleştirildi.")

        except Exception as e:
            print(f"Debug: Error creating manual match: {str(e)}")

    # Placeholder methods for dialogs - these would need full implementation
    def show_manual_match_dialog(self, video_file, subtitle_file):
        """Show manual match dialog - placeholder."""
        print(f"Debug: Manual match dialog for {video_file} -> {subtitle_file}")

    def show_sync_dialog(self, subtitle_path, subtitle_file):
        """Show sync dialog - placeholder."""
        print(f"Debug: Sync dialog for {subtitle_file}")

    def perform_auto_sync(self, video_path, subtitle_path, subtitle_file):
        """Perform auto sync - placeholder."""
        print(f"Debug: Auto sync for {subtitle_file}")


# Import os here to avoid circular imports
import os