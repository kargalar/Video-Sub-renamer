"""
UI components for the video subtitle renamer application.
Handles theme management, UI setup, and display functions.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


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

        # Theme variables
        self.is_dark_theme = self.settings_manager.load_theme_preference()
        self.skip_x_files = self.settings_manager.load_skip_x_preference()
        self.current_theme = self.settings_manager.get_current_theme(self.is_dark_theme)

        # UI elements
        self.file_tree = None
        self.context_menu = None
        self.theme_button = None
        self.drag_label = None

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

            # Status bar
            status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            print("Debug: UI components setup completed")

        except Exception as e:
            print(f"Debug: Error setting up UI: {str(e)}")

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

    def display_matches(self):
        """Display matches in the treeview."""
        try:
            # Clear treeview
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)

            # Display matches
            for video_file, subtitle_file in self.matcher.matches:
                self.file_tree.insert("", tk.END, values=(video_file, subtitle_file, "Eşleşti"))

            # Display unmatched video files
            matched_videos = [match[0] for match in self.matcher.matches]
            for video_file in self.matcher.video_files:
                if video_file not in matched_videos:
                    if self.skip_x_files and video_file.lower().startswith('x'):
                        status = "Altyazıya dahil edilmiş"
                    else:
                        status = "Eşleşme bulunamadı"
                    self.file_tree.insert("", tk.END, values=(video_file, "", status))

            # Display unmatched subtitle files
            matched_subtitles = [match[1] for match in self.matcher.matches]
            for subtitle_file in self.matcher.subtitle_files:
                if subtitle_file not in matched_subtitles:
                    self.file_tree.insert("", tk.END, values=("", subtitle_file, "Eşleşme bulunamadı"))

            print(f"Debug: Displayed {len(self.matcher.matches)} matches")

        except Exception as e:
            print(f"Debug: Error displaying matches: {str(e)}")

    def browse_folder(self):
        """Browse for folder selection."""
        try:
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder_path_var.set(folder_path)
                self.settings_manager.save_folder_path(folder_path)
                self.scan_files()
                print(f"Debug: Folder selected: {folder_path}")
        except Exception as e:
            print(f"Debug: Error browsing folder: {str(e)}")

    def scan_files(self):
        """Scan files in selected folder."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                return

            # Scan directory
            video_files, subtitle_files = self.matcher.scan_directory(folder_path, self.skip_x_files)

            # Display results
            self.display_matches()

            self.status_var.set(f"{len(video_files)} video dosyası, {len(subtitle_files)} altyazı dosyası bulundu.")
            print(f"Debug: Scanned {len(video_files)} videos, {len(subtitle_files)} subtitles")

        except Exception as e:
            messagebox.showerror("Hata", f"Dosyalar taranırken bir hata oluştu: {str(e)}")
            print(f"Debug: Error scanning files: {str(e)}")

    def rename_subtitles(self):
        """Rename subtitle files to match video files."""
        try:
            folder_path = self.folder_path_var.get()
            if not folder_path:
                messagebox.showerror("Hata", "Lütfen bir klasör seçin.")
                return

            renamed_count, errors = self.matcher.rename_subtitles(folder_path)

            # Show errors if any
            if errors:
                error_message = "\n".join(errors)
                messagebox.showerror("Hatalar", f"Bazı dosyalar yeniden adlandırılamadı:\n{error_message}")

            # Update status bar
            if renamed_count > 0:
                self.status_var.set(f"{renamed_count} altyazı dosyası başarıyla yeniden adlandırıldı.")
                self.scan_files()  # Refresh list
            else:
                self.status_var.set("Hiçbir dosya yeniden adlandırılmadı.")

            print(f"Debug: Renamed {renamed_count} subtitle files")

        except Exception as e:
            messagebox.showerror("Hata", f"Altyazılar yeniden adlandırılırken hata: {str(e)}")
            print(f"Debug: Error renaming subtitles: {str(e)}")

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

    # Placeholder methods for UI event handlers - these will be implemented in main application
    def manual_match(self):
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