"""
UI components for the video subtitle renamer application.
Handles theme management, UI setup, and display functions.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os


class UIComponents:
    """UI components and theme management for the application."""

    def __init__(self, root, settings_manager, matcher):
        self.root = root
        self.settings_manager = settings_manager
        self.matcher = matcher

        # UI variables
        self.folder_path_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        self.skip_x_var = tk.BooleanVar()
        self.debug_var = tk.BooleanVar()  # Debug mode toggle
        self.algorithm_var = tk.StringVar()  # Selected algorithm
        self.algorithm_var.set("Algorithm 1 (Year + Word)")  # Default algorithm

        # Theme variables
        self.is_dark_theme = self.settings_manager.load_theme_preference()
        self.skip_x_files = self.settings_manager.load_skip_x_preference()
        self.current_theme = self.settings_manager.get_current_theme(self.is_dark_theme)

        # UI elements
        self.file_tree = None
        self.context_menu = None
        self.theme_button = None
        self.drag_label = None
        self.debug_notebook = None  # Notebook for algorithm tabs in debug mode

        # Drag and drop variables
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.drag_source_item = None
        self.drag_source_values = None
        self.drop_target_item = None

    def setup_ui(self):
        """Setup the main UI components."""
        try:
            # Main frame
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Folder selection section
            folder_frame = ttk.LabelFrame(main_frame, text="Klasör Seçimi", padding="10")
            folder_frame.pack(fill=tk.X, pady=5)

            folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=70)
            folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            browse_button = ttk.Button(folder_frame, text="Gözat", command=self.browse_folder)
            browse_button.pack(side=tk.RIGHT)

            # Files section
            files_frame = ttk.LabelFrame(main_frame, text="Dosyalar", padding="10")
            files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            # Scrollbar for Treeview
            scrollbar = ttk.Scrollbar(files_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Treeview for file list
            columns = ("video_file", "subtitle_file", "status")
            self.file_tree = ttk.Treeview(files_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)

            # Column headers
            self.file_tree.heading("video_file", text="Video Dosyası")
            self.file_tree.heading("subtitle_file", text="Altyazı Dosyası")
            self.file_tree.heading("status", text="Durum")

            # Column widths
            self.file_tree.column("video_file", width=300)
            self.file_tree.column("subtitle_file", width=300)
            self.file_tree.column("status", width=100)

            self.file_tree.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.file_tree.yview)

            # Right-click context menu
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="Manuel Eşleştir", command=self.manual_match)
            self.context_menu.add_command(label="Eşleştirmeyi Kaldır", command=self.remove_match)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Manuel Altyazı Senkronizasyonu", command=self.sync_subtitle)
            self.context_menu.add_command(label="Otomatik Altyazı Senkronizasyonu", command=self.auto_sync_subtitle)

            # Bind right-click event
            self.file_tree.bind("<Button-3>", self.show_context_menu)

            # Bind drag and drop events
            self.file_tree.bind("<ButtonPress-1>", self.on_drag_start)
            self.file_tree.bind("<B1-Motion>", self.on_drag_motion)
            self.file_tree.bind("<ButtonRelease-1>", self.on_drag_release)

            # Buttons section
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=5)

            # Algorithm selection
            ttk.Label(button_frame, text="Algoritma:").pack(side=tk.LEFT, padx=(0, 5))
            algorithm_combo = ttk.Combobox(button_frame, textvariable=self.algorithm_var, state="readonly", width=25)
            algorithm_combo['values'] = list(self.matcher.get_all_algorithms().keys())
            algorithm_combo.pack(side=tk.LEFT, padx=(0, 10))

            scan_button = ttk.Button(button_frame, text="Dosyaları Tara", command=self.scan_files)
            scan_button.pack(side=tk.LEFT, padx=5)

            rename_button = ttk.Button(button_frame, text="Altyazıları Yeniden Adlandır", command=self.rename_subtitles)
            rename_button.pack(side=tk.LEFT, padx=5)

            sync_button = ttk.Button(button_frame, text="Manuel Senkronizasyon", command=self.sync_subtitle)
            sync_button.pack(side=tk.LEFT, padx=5)

            auto_sync_button = ttk.Button(button_frame, text="Otomatik Senkronizasyon", command=self.auto_sync_subtitle)
            auto_sync_button.pack(side=tk.LEFT, padx=5)

            # Theme toggle button - Set text based on current theme
            button_text = "Açık Tema" if self.is_dark_theme else "Karanlık Tema"
            self.theme_button = ttk.Button(button_frame, text=button_text, command=self.toggle_theme)
            self.theme_button.pack(side=tk.RIGHT, padx=5)

            # Skip x-prefixed files option
            self.skip_x_var.set(self.skip_x_files)
            skip_x_check = ttk.Checkbutton(button_frame, text="'x' ile başlayan videoları geç", variable=self.skip_x_var, command=self.toggle_skip_x)
            skip_x_check.pack(side=tk.RIGHT, padx=5)

            # Debug mode toggle
            debug_check = ttk.Checkbutton(button_frame, text="Debug Modu", variable=self.debug_var, command=self.toggle_debug_mode)
            debug_check.pack(side=tk.RIGHT, padx=5)

            # Debug notebook (initially hidden)
            self.debug_notebook = ttk.Notebook(main_frame)
            self.debug_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
            self.debug_notebook.pack_forget()  # Hide initially

            # Create algorithm tabs
            self.create_algorithm_tabs()

            # Status bar
            status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            print("Debug: UI components setup completed")

        except Exception as e:
            print(f"Debug: Error setting up UI: {str(e)}")

    # Placeholder methods for UI event handlers - these will be implemented in main application
    def manual_match(self):
        """Handle manual match selection."""
        try:
            # Get selected item
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir dosya seçin.")
                return

            # Get selected values
            values = self.file_tree.item(selected_item[0], "values")
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
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Remove match if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.folder_path_var.get()
                self.matcher.remove_match(folder_path, video_file, subtitle_file)
                self.display_matches()
                self.status_var.set(f"'{video_file}' ve '{subtitle_file}' eşleştirmesi kaldırıldı.")
            else:
                messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

        except Exception as e:
            print(f"Debug: Error removing match: {str(e)}")
            messagebox.showerror("Hata", f"Eşleştirme kaldırma hatası: {str(e)}")

    def rename_subtitles(self):
        """Handle subtitle renaming."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                return

            renamed_count, errors = self.matcher.rename_subtitles(folder_path)

            if errors:
                error_text = "\n".join(errors)
                messagebox.showerror("Hata", f"Altyazı yeniden adlandırma hataları:\n{error_text}")
            else:
                messagebox.showinfo("Başarılı", f"{renamed_count} altyazı dosyası yeniden adlandırıldı.")
                self.status_var.set(f"{renamed_count} altyazı yeniden adlandırıldı.")
                
                # Automatically clean prefixes after successful rename
                cleaned_count, clean_errors = self.matcher.clean_prefixes(folder_path, prefix="--")
                if clean_errors:
                    print(f"Debug: Prefix cleaning errors: {clean_errors}")
                else:
                    print(f"Debug: Automatically cleaned prefixes from {cleaned_count} files")

            # Re-scan to update display
            self.scan_files()

        except Exception as e:
            print(f"Debug: Error renaming subtitles: {str(e)}")
            messagebox.showerror("Hata", f"Altyazı yeniden adlandırma hatası: {str(e)}")

    def clean_prefixes(self):
        """Handle prefix cleaning for matched files."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                return

            cleaned_count, errors = self.matcher.clean_prefixes(folder_path, prefix="--")

            if errors:
                error_text = "\n".join(errors)
                messagebox.showerror("Hata", f"Prefix temizleme hataları:\n{error_text}")
            else:
                messagebox.showinfo("Başarılı", f"{cleaned_count} dosyanın prefix'i temizlendi.")
                self.status_var.set(f"{cleaned_count} dosya prefix'i temizlendi.")

            # Re-scan to update display
            self.scan_files()

        except Exception as e:
            print(f"Debug: Error cleaning prefixes: {str(e)}")
            messagebox.showerror("Hata", f"Prefix temizleme hatası: {str(e)}")

    def sync_subtitle(self):
        """Handle manual subtitle synchronization."""
        try:
            # Get selected item
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Sync if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.folder_path_var.get()
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
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
                return

            # Get selected values
            values = self.file_tree.item(selected_item[0], "values")
            video_file = values[0]
            subtitle_file = values[1]

            # Auto sync if both video and subtitle exist
            if video_file and subtitle_file:
                folder_path = self.folder_path_var.get()
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

    def show_manual_match_dialog(self, video_file, subtitle_file):
        """Show manual match dialog - placeholder."""
        print(f"Debug: Manual match dialog for {video_file} -> {subtitle_file}")

    def show_sync_dialog(self, subtitle_path, subtitle_file):
        """Show sync dialog - placeholder."""
        print(f"Debug: Sync dialog for {subtitle_file}")

    def perform_auto_sync(self, video_path, subtitle_path, subtitle_file):
        """Perform auto sync - placeholder."""
        print(f"Debug: Auto sync for {subtitle_file}")

    def show_context_menu(self, event):
        """Show context menu on right-click."""
        try:
            # Select clicked item
            item = self.file_tree.identify_row(event.y)
            if item:
                self.file_tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Debug: Error showing context menu: {str(e)}")

    def on_drag_start(self, event):
        """Handle drag start event."""
        try:
            item = self.file_tree.identify_row(event.y)
            if item:
                self.drag_source_item = item
                self.drag_source_values = self.file_tree.item(item, "values")
                self.drag_data["item"] = item
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y

                # Create drag label
                values = self.drag_source_values
                label_text = f"{values[0]} -> {values[1]}" if values[0] and values[1] else values[0] or values[1]
                self.drag_label = tk.Label(self.root, text=label_text,
                                         bg=self.current_theme["drag_label_bg"],
                                         fg=self.current_theme["drag_label_fg"])
                self.drag_label.place(x=event.x_root, y=event.y_root)

        except Exception as e:
            print(f"Debug: Error in drag start: {str(e)}")

    def on_drag_motion(self, event):
        """Handle drag motion event."""
        try:
            if self.drag_label:
                self.drag_label.place(x=event.x_root + 10, y=event.y_root + 10)
        except Exception as e:
            print(f"Debug: Error in drag motion: {str(e)}")

    def on_drag_release(self, event):
        """Handle drag release event."""
        try:
            if self.drag_label:
                self.drag_label.destroy()
                self.drag_label = None

            # Check if dropped on valid target
            item = self.file_tree.identify_row(event.y)
            if item and item != self.drag_source_item:
                target_values = self.file_tree.item(item, "values")

                # Perform manual match if valid drag-drop
                source_video = self.drag_source_values[0]
                source_sub = self.drag_source_values[1]
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
            self.drag_source_item = None
            self.drag_source_values = None
            self.drag_data = {"item": None, "x": 0, "y": 0}

        except Exception as e:
            print(f"Debug: Error in drag release: {str(e)}")

    def create_manual_match(self, video_file, subtitle_file):
        """Create a manual match between video and subtitle."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                return

            self.matcher.create_match(folder_path, video_file, subtitle_file)
            self.display_matches()
            self.status_var.set(f"'{video_file}' ve '{subtitle_file}' manuel olarak eşleştirildi.")

        except Exception as e:
            print(f"Debug: Error creating manual match: {str(e)}")

    def browse_folder(self):
        """Browse for folder selection."""
        try:
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder_path_var.set(folder_path)
                self.scan_files()
        except Exception as e:
            print(f"Debug: Error browsing folder: {str(e)}")

    # Theme management methods
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            self.is_dark_theme = not self.is_dark_theme

            if self.is_dark_theme:
                self.current_theme = self.settings_manager.DARK_THEME
                self.theme_button.config(text="Açık Tema")
            else:
                self.current_theme = self.settings_manager.LIGHT_THEME
                self.theme_button.config(text="Karanlık Tema")

            # Apply theme
            self.apply_theme()
            self.settings_manager.save_theme_preference(self.is_dark_theme)

            print(f"Debug: Theme toggled to {'dark' if self.is_dark_theme else 'light'}")

        except Exception as e:
            print(f"Debug: Error toggling theme: {str(e)}")

    def toggle_skip_x(self):
        """Toggle skipping x-prefixed files."""
        try:
            self.skip_x_files = self.skip_x_var.get()
            self.settings_manager.save_skip_x_preference(self.skip_x_files)

            # Re-scan if folder is selected
            if self.folder_path_var.get():
                self.scan_files()

            print(f"Debug: Skip x-files set to {self.skip_x_files}")

        except Exception as e:
            print(f"Debug: Error toggling skip x-files: {str(e)}")

    def toggle_debug_mode(self):
        """Toggle debug mode on/off."""
        try:
            debug_enabled = self.debug_var.get()

            if debug_enabled:
                # Show debug notebook and hide main file tree
                self.debug_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
                # Find the files frame and hide it
                for child in self.root.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        for subchild in child.winfo_children():
                            if hasattr(subchild, 'winfo_children'):
                                for subsubchild in subchild.winfo_children():
                                    if str(subsubchild).endswith('.!labelframe2'):  # Files frame
                                        subsubchild.pack_forget()
                                        break
            else:
                # Hide debug notebook and show main file tree
                self.debug_notebook.pack_forget()
                # Re-show the files frame
                self.root.update()  # Force UI update

            # Re-scan files to update debug tabs
            if self.folder_path_var.get():
                self.scan_files()

            print(f"Debug: Debug mode {'enabled' if debug_enabled else 'disabled'}")

        except Exception as e:
            print(f"Debug: Error toggling debug mode: {str(e)}")

    def create_algorithm_tabs(self):
        """Create tabs for each matching algorithm."""
        try:
            algorithms = self.matcher.get_all_algorithms()

            # Clear existing tabs
            for tab in self.debug_notebook.tabs():
                self.debug_notebook.forget(tab)

            # Create a tab for each algorithm
            self.algorithm_trees = {}
            for algo_name in algorithms.keys():
                # Create frame for this algorithm
                frame = ttk.Frame(self.debug_notebook)

                # Create treeview for matches
                tree = ttk.Treeview(frame, columns=("video", "subtitle", "score"), show="headings")
                tree.heading("video", text="Video Dosyası")
                tree.heading("subtitle", text="Altyazı Dosyası")
                tree.heading("score", text="Eşleşme Oranı (%)")

                tree.column("video", width=250)
                tree.column("subtitle", width=250)
                tree.column("score", width=100)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)

                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                self.debug_notebook.add(frame, text=algo_name)
                self.algorithm_trees[algo_name] = tree

            print("Debug: Algorithm tabs created")

        except Exception as e:
            print(f"Debug: Error creating algorithm tabs: {str(e)}")

    def update_algorithm_tabs(self):
        """Update algorithm tabs with current matches."""
        try:
            if not hasattr(self, 'algorithm_trees') or not self.debug_var.get():
                return

            algorithms = self.matcher.get_all_algorithms()

            for algo_name, algo_func in algorithms.items():
                tree = self.algorithm_trees.get(algo_name)
                if not tree:
                    continue

                # Clear existing items
                for item in tree.get_children():
                    tree.delete(item)

                # Find matches with this algorithm
                matches = self.matcher.find_matches_with_algorithm(algo_func, threshold=0.0)  # Show all matches

                # Add matches to tree
                for video_file, subtitle_file, score in matches:
                    percentage = f"{score:.1%}"
                    tree.insert("", tk.END, values=(video_file, subtitle_file, percentage))

                # Update tab text to show match count
                tab_count = len(matches)
                tab_text = f"{algo_name} ({tab_count})"
                tab_id = self.debug_notebook.tabs()[list(algorithms.keys()).index(algo_name)]
                self.debug_notebook.tab(tab_id, text=tab_text)

            print("Debug: Algorithm tabs updated")

        except Exception as e:
            print(f"Debug: Error updating algorithm tabs: {str(e)}")

    def scan_files(self):
        """Scan the selected folder for video and subtitle files."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                messagebox.showwarning("Uyarı", "Lütfen bir klasör seçin.")
                return

            if not os.path.isdir(folder_path):
                messagebox.showerror("Hata", "Seçilen yol bir klasör değil.")
                return

            # Scan files using matcher
            selected_algorithm = self.algorithm_var.get()
            self.matcher.scan_folder(folder_path, skip_x=self.skip_x_files, algorithm_name=selected_algorithm)

            # Display matches in main tree
            self.display_matches()

            # Update algorithm tabs if debug mode is enabled
            if self.debug_var.get():
                self.update_algorithm_tabs()

            # Update status
            video_count = len(self.matcher.video_files)
            subtitle_count = len(self.matcher.subtitle_files)
            match_count = len(self.matcher.matches)

            self.status_var.set(f"{video_count} video, {subtitle_count} altyazı bulundu. {match_count} eşleşme yapıldı.")

            print(f"Debug: Scanned {video_count} videos, {subtitle_count} subtitles, {match_count} matches")

        except Exception as e:
            print(f"Debug: Error scanning files: {str(e)}")
            messagebox.showerror("Hata", f"Dosya tarama hatası: {str(e)}")

    def display_matches(self):
        """Display current matches in the main file tree."""
        try:
            # Clear existing items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)

            # Add matches
            for video_file, subtitle_file in self.matcher.matches:
                self.file_tree.insert("", tk.END, values=(video_file, subtitle_file, "Eşleşti"))

            # Add unmatched videos
            for video_file in self.matcher.video_files:
                if not any(match[0] == video_file for match in self.matcher.matches):
                    self.file_tree.insert("", tk.END, values=(video_file, "", "Eşleşme Yok"))

            # Add unmatched subtitles
            for subtitle_file in self.matcher.subtitle_files:
                if not any(match[1] == subtitle_file for match in self.matcher.matches):
                    self.file_tree.insert("", tk.END, values=("", subtitle_file, "Eşleşme Yok"))

            print(f"Debug: Displayed {len(self.matcher.matches)} matches")

        except Exception as e:
            print(f"Debug: Error displaying matches: {str(e)}")

    # Placeholder methods for UI event handlers - these will be implemented in main application
        """Placeholder for manual match functionality."""
        """Placeholder for manual match functionality."""
        print("Debug: Manual match called")

    def remove_match(self):
        """Placeholder for remove match functionality."""
        print("Debug: Remove match called")

    def sync_subtitle(self):
        """Placeholder for subtitle sync functionality."""
        print("Debug: Sync subtitle called")

    def auto_sync_subtitle(self):
        """Placeholder for auto sync functionality."""
        print("Debug: Auto sync subtitle called")

    def show_context_menu(self, event):
        """Placeholder for context menu display."""
        print("Debug: Show context menu called")

    def on_drag_start(self, event):
        """Placeholder for drag start."""
        print("Debug: Drag start called")

    def on_drag_motion(self, event):
        """Placeholder for drag motion."""
        print("Debug: Drag motion called")

    def on_drag_release(self, event):
        """Placeholder for drag release."""
        print("Debug: Drag release called")

    def apply_theme(self):
        """Apply the current theme to all UI elements."""
        try:
            # Main window
            self.root.configure(bg=self.current_theme["bg"])

            # Create style
            style = ttk.Style()
            style.theme_use('clam')  # Use 'clam' theme for better customization

            # General style
            style.configure("TFrame", background=self.current_theme["bg"])
            style.configure("TLabel", background=self.current_theme["bg"], foreground=self.current_theme["fg"])

            # Button style
            style.configure("TButton",
                           background=self.current_theme["button_bg"],
                           foreground=self.current_theme["button_fg"],
                           bordercolor=self.current_theme["button_bg"],
                           lightcolor=self.current_theme["button_bg"],
                           darkcolor=self.current_theme["button_bg"],
                           focuscolor=self.current_theme["button_bg"])

            style.map("TButton",
                     background=[("active", self.current_theme["treeview_selected_bg"]),
                                ("pressed", self.current_theme["treeview_selected_bg"])],
                     foreground=[("active", self.current_theme["treeview_selected_fg"]),
                                ("pressed", self.current_theme["treeview_selected_fg"])])

            # Entry style
            style.configure("TEntry",
                           fieldbackground=self.current_theme["entry_bg"],
                           foreground=self.current_theme["entry_fg"],
                           bordercolor=self.current_theme["button_bg"],
                           lightcolor=self.current_theme["button_bg"],
                           darkcolor=self.current_theme["button_bg"])

            # LabelFrame style
            style.configure("TLabelframe",
                           background=self.current_theme["bg"],
                           foreground=self.current_theme["fg"],
                           bordercolor=self.current_theme["button_bg"],
                           lightcolor=self.current_theme["button_bg"],
                           darkcolor=self.current_theme["button_bg"])

            style.configure("TLabelframe.Label",
                           background=self.current_theme["bg"],
                           foreground=self.current_theme["fg"])

            # Treeview style
            style.configure("Treeview",
                           background=self.current_theme["treeview_bg"],
                           foreground=self.current_theme["treeview_fg"],
                           fieldbackground=self.current_theme["treeview_bg"],
                           bordercolor=self.current_theme["button_bg"],
                           lightcolor=self.current_theme["button_bg"],
                           darkcolor=self.current_theme["button_bg"])

            style.configure("Treeview.Heading",
                           background=self.current_theme["button_bg"],
                           foreground=self.current_theme["button_fg"],
                           relief="flat")

            style.map("Treeview",
                     background=[("selected", self.current_theme["treeview_selected_bg"])],
                     foreground=[("selected", self.current_theme["treeview_selected_fg"])])

            style.map("Treeview.Heading",
                     background=[("active", self.current_theme["treeview_selected_bg"])],
                     foreground=[("active", self.current_theme["treeview_selected_fg"])])

            # Scrollbar style
            style.configure("TScrollbar",
                           background=self.current_theme["button_bg"],
                           troughcolor=self.current_theme["bg"],
                           bordercolor=self.current_theme["button_bg"],
                           arrowcolor=self.current_theme["fg"])

            # Menu
            if self.context_menu:
                self.context_menu.config(bg=self.current_theme["menu_bg"], fg=self.current_theme["menu_fg"],
                                        activebackground=self.current_theme["treeview_selected_bg"],
                                        activeforeground=self.current_theme["treeview_selected_fg"])

            # Status bar
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Label) and child.cget("relief") == "sunken":
                    style.configure("Statusbar.TLabel",
                                   background=self.current_theme["status_bg"],
                                   foreground=self.current_theme["status_fg"])
                    child.configure(style="Statusbar.TLabel")

            # Update drag label colors if it exists
            if self.drag_label:
                self.drag_label.configure(bg=self.current_theme["drag_label_bg"], fg=self.current_theme["drag_label_fg"])

            print("Debug: Theme applied successfully")

        except Exception as e:
            print(f"Debug: Error applying theme: {str(e)}")