import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import sys
import json
import difflib

class VideoSubRenamer:
    # Tema renkleri
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

    def __init__(self, root):
        self.root = root
        self.root.title("Video Altyazı Yeniden Adlandırıcı")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Ayarlar dosyası - Kullanıcının belgeleri klasöründe sakla
        user_docs = os.path.expanduser("~")  # Kullanıcı ana dizini
        app_folder = os.path.join(user_docs, "VideoSubRenamer")

        # Uygulama klasörünü oluştur (yoksa)
        if not os.path.exists(app_folder):
            try:
                os.makedirs(app_folder)
            except Exception as e:
                print(f"Uygulama klasörü oluşturulamadı: {str(e)}")

        self.settings_file = os.path.join(app_folder, "settings.json")

        # Tema değişkeni
        self.is_dark_theme = self.load_theme_preference()
        self.current_theme = self.DARK_THEME if self.is_dark_theme else self.LIGHT_THEME

        self.setup_ui()

        # Başlangıç temasını uygula
        self.apply_theme()

    def load_theme_preference(self):
        """Kaydedilmiş tema tercihini yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('dark_theme', False)
        except Exception as e:
            print(f"Tema tercihi yüklenirken hata oluştu: {str(e)}")
        return False

    def save_theme_preference(self):
        """Tema tercihini kaydet"""
        try:
            settings = {'dark_theme': self.is_dark_theme}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Tema tercihi kaydedilirken hata oluştu: {str(e)}")

    def toggle_theme(self):
        """Temayı değiştir (açık/karanlık)"""
        self.is_dark_theme = not self.is_dark_theme

        if self.is_dark_theme:
            self.current_theme = self.DARK_THEME
            self.theme_button.config(text="Açık Tema")
        else:
            self.current_theme = self.LIGHT_THEME
            self.theme_button.config(text="Karanlık Tema")

        # Temayı uygula
        self.apply_theme()

        # Tema tercihini kaydet
        self.save_theme_preference()

    def apply_theme(self):
        """Mevcut temayı uygula"""
        # Ana pencere
        self.root.configure(bg=self.current_theme["bg"])

        # Stil oluştur
        style = ttk.Style()
        style.theme_use('clam')  # Daha iyi özelleştirme için 'clam' temasını kullan

        # Genel stil
        style.configure("TFrame", background=self.current_theme["bg"])
        style.configure("TLabel", background=self.current_theme["bg"], foreground=self.current_theme["fg"])

        # Buton stili
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

        # Entry stili
        style.configure("TEntry",
                       fieldbackground=self.current_theme["entry_bg"],
                       foreground=self.current_theme["entry_fg"],
                       bordercolor=self.current_theme["button_bg"],
                       lightcolor=self.current_theme["button_bg"],
                       darkcolor=self.current_theme["button_bg"])

        # LabelFrame stili
        style.configure("TLabelframe",
                       background=self.current_theme["bg"],
                       foreground=self.current_theme["fg"],
                       bordercolor=self.current_theme["button_bg"],
                       lightcolor=self.current_theme["button_bg"],
                       darkcolor=self.current_theme["button_bg"])

        style.configure("TLabelframe.Label",
                       background=self.current_theme["bg"],
                       foreground=self.current_theme["fg"])

        # Treeview stili
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

        # Scrollbar stili
        style.configure("TScrollbar",
                       background=self.current_theme["button_bg"],
                       troughcolor=self.current_theme["bg"],
                       bordercolor=self.current_theme["button_bg"],
                       arrowcolor=self.current_theme["fg"])

        # Menü
        self.context_menu.config(bg=self.current_theme["menu_bg"], fg=self.current_theme["menu_fg"],
                                activebackground=self.current_theme["treeview_selected_bg"],
                                activeforeground=self.current_theme["treeview_selected_fg"])

        # Durum çubuğu
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Label) and child.cget("relief") == "sunken":
                style.configure("Statusbar.TLabel",
                               background=self.current_theme["status_bg"],
                               foreground=self.current_theme["status_fg"])
                child.configure(style="Statusbar.TLabel")

        # Sürükleme etiketi için renkleri güncelle
        if hasattr(self, 'drag_label') and self.drag_label:
            self.drag_label.configure(bg=self.current_theme["drag_label_bg"], fg=self.current_theme["drag_label_fg"])

    def setup_ui(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Klasör seçme bölümü
        folder_frame = ttk.LabelFrame(main_frame, text="Klasör Seçimi", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)

        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=70)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_button = ttk.Button(folder_frame, text="Gözat", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT)

        # Dosya listesi bölümü
        files_frame = ttk.LabelFrame(main_frame, text="Dosyalar", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview için scrollbar
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Dosya listesi için treeview
        columns = ("video_file", "subtitle_file", "status")
        self.file_tree = ttk.Treeview(files_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)

        # Sütun başlıkları
        self.file_tree.heading("video_file", text="Video Dosyası")
        self.file_tree.heading("subtitle_file", text="Altyazı Dosyası")
        self.file_tree.heading("status", text="Durum")

        # Sütun genişlikleri
        self.file_tree.column("video_file", width=300)
        self.file_tree.column("subtitle_file", width=300)
        self.file_tree.column("status", width=100)

        self.file_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_tree.yview)

        # Sağ tıklama menüsü
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Manuel Eşleştir", command=self.manual_match)
        self.context_menu.add_command(label="Eşleştirmeyi Kaldır", command=self.remove_match)

        # Sağ tıklama olayını bağla
        self.file_tree.bind("<Button-3>", self.show_context_menu)

        # Sürükle-bırak olaylarını bağla
        self.file_tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.file_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.file_tree.bind("<ButtonRelease-1>", self.on_drag_release)

        # Sürükle-bırak değişkenleri
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.drag_source_item = None
        self.drag_source_values = None
        self.drop_target_item = None

        # Butonlar bölümü
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        scan_button = ttk.Button(button_frame, text="Dosyaları Tara", command=self.scan_files)
        scan_button.pack(side=tk.LEFT, padx=5)

        rename_button = ttk.Button(button_frame, text="Altyazıları Yeniden Adlandır", command=self.rename_subtitles)
        rename_button.pack(side=tk.LEFT, padx=5)

        # Tema değiştirme butonu - Mevcut temaya göre metin ayarla
        button_text = "Açık Tema" if self.is_dark_theme else "Karanlık Tema"
        self.theme_button = ttk.Button(button_frame, text=button_text, command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=5)

        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Veri yapıları
        self.video_files = []
        self.subtitle_files = []
        self.matches = []

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_var.set(folder_path)
            self.scan_files()

    def scan_files(self):
        folder_path = self.folder_path_var.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin.")
            return

        # Dosya listelerini temizle
        self.video_files = []
        self.subtitle_files = []
        self.matches = []

        # Treeview'ı temizle
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # Video ve altyazı uzantıları
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
        subtitle_extensions = ['.srt', '.sub', '.idx', '.ass', '.ssa']

        # Klasördeki dosyaları tara
        try:
            files = os.listdir(folder_path)

            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    ext = ext.lower()

                    if ext in video_extensions:
                        self.video_files.append(file)
                    elif ext in subtitle_extensions:
                        self.subtitle_files.append(file)

            # Eşleşmeleri bul
            self.find_matches()

            # Sonuçları göster
            self.display_matches()

            self.status_var.set(f"{len(self.video_files)} video dosyası, {len(self.subtitle_files)} altyazı dosyası bulundu.")

        except Exception as e:
            messagebox.showerror("Hata", f"Dosyalar taranırken bir hata oluştu: {str(e)}")

    def find_matches(self):
        # Eşleşmeleri temizle
        self.matches = []

        # Kullanılmış altyazı dosyalarını takip et
        used_subtitles = set()

        # Önce tam eşleşmeleri bul (uzantı hariç dosya adları aynı olanlar)
        for video_file in self.video_files:
            video_name, _ = os.path.splitext(video_file)

            for subtitle_file in self.subtitle_files:
                if subtitle_file in used_subtitles:
                    continue

                subtitle_name, _ = os.path.splitext(subtitle_file)

                # Tam eşleşme kontrolü
                if video_name.lower() == subtitle_name.lower():
                    self.matches.append((video_file, subtitle_file))
                    used_subtitles.add(subtitle_file)
                    break

        # Tam eşleşme bulunamayan video dosyaları için benzerlik skoru hesapla
        unmatched_videos = [v for v in self.video_files if v not in [m[0] for m in self.matches]]

        # Eşleşme sonuçlarını ve skorlarını sakla
        potential_matches = []

        # Her eşleşmemiş video dosyası için olası altyazı eşleşmelerini bul
        for video_file in unmatched_videos:
            video_name, _ = os.path.splitext(video_file)

            for subtitle_file in self.subtitle_files:
                # Eğer bu altyazı dosyası zaten kullanılmışsa, atla
                if subtitle_file in used_subtitles:
                    continue

                subtitle_name, _ = os.path.splitext(subtitle_file)

                # Gelişmiş benzerlik skoru hesapla
                score = self.similarity_score(video_name, subtitle_name)

                # Eğer skor eşik değerinden yüksekse, potansiyel eşleşme olarak ekle
                if score > 0.5:  # Eşik değeri
                    potential_matches.append((video_file, subtitle_file, score))

        # Potansiyel eşleşmeleri skora göre sırala (en yüksek skordan en düşüğe)
        potential_matches.sort(key=lambda x: x[2], reverse=True)

        # En iyi eşleşmeleri seç
        for video_file, subtitle_file, score in potential_matches:
            # Eğer bu video veya altyazı zaten eşleştirilmişse, atla
            if video_file in [m[0] for m in self.matches] or subtitle_file in used_subtitles:
                continue

            # Eşleşmeyi ekle
            self.matches.append((video_file, subtitle_file))
            used_subtitles.add(subtitle_file)

            # Durum çubuğunda bilgi göster
            if score < 0.7:
                self.status_var.set(f"Düşük benzerlik skoru: '{video_file}' ve '{subtitle_file}' ({score:.2f})")

        # Eşleşmeyen dosyaları göster
        unmatched_videos = [v for v in self.video_files if v not in [m[0] for m in self.matches]]
        unmatched_subtitles = [s for s in self.subtitle_files if s not in used_subtitles]

        if unmatched_videos or unmatched_subtitles:
            if len(unmatched_videos) > 0 and len(unmatched_subtitles) > 0:
                self.status_var.set(f"{len(unmatched_videos)} video ve {len(unmatched_subtitles)} altyazı eşleştirilemedi. Manuel eşleştirme yapabilirsiniz.")

    def levenshtein_distance(self, s1, s2):
        """İki string arasındaki Levenshtein mesafesini hesaplar (düzenleme mesafesi)"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def similarity_score(self, str1, str2):
        """Gelişmiş benzerlik skoru hesaplama"""
        str1 = str1.lower()
        str2 = str2.lower()

        # Tam eşleşme kontrolü (uzantı hariç dosya adları aynıysa)
        if str1 == str2:
            return 1.0

        # Sezon ve bölüm bilgisini çıkar
        # Daha kapsamlı regex pattern: s01e01, 1x01, season 1 episode 1 gibi formatları yakalar
        season_ep_patterns = [
            r's(\d+)e(\d+)',  # s01e01 formatı
            r'(\d+)x(\d+)',   # 1x01 formatı
            r'season\s*(\d+)\s*episode\s*(\d+)',  # season 1 episode 1 formatı
            r'e(\d+)',        # sadece bölüm numarası (e01)
        ]

        # Her iki string'den sezon ve bölüm numaralarını çıkar
        str1_season = None
        str1_episode = None
        str2_season = None
        str2_episode = None

        for pattern in season_ep_patterns:
            str1_match = re.search(pattern, str1)
            if str1_match:
                if len(str1_match.groups()) == 2:
                    str1_season = int(str1_match.group(1))
                    str1_episode = int(str1_match.group(2))
                else:
                    str1_episode = int(str1_match.group(1))
                break

        for pattern in season_ep_patterns:
            str2_match = re.search(pattern, str2)
            if str2_match:
                if len(str2_match.groups()) == 2:
                    str2_season = int(str2_match.group(1))
                    str2_episode = int(str2_match.group(2))
                else:
                    str2_episode = int(str2_match.group(1))
                break

        # Eğer her ikisinde de sezon ve bölüm bilgisi varsa ve aynıysa en yüksek puan ver
        if str1_season is not None and str2_season is not None and str1_episode is not None and str2_episode is not None:
            if str1_season == str2_season and str1_episode == str2_episode:
                return 1.0
            # Sezon aynı ama bölüm farklıysa düşük puan ver
            elif str1_season == str2_season:
                return 0.3
            # Tamamen farklıysa çok düşük puan ver
            else:
                return 0.1

        # Sadece bölüm numarası varsa ve aynıysa yüksek puan ver
        elif str1_episode is not None and str2_episode is not None and str1_episode == str2_episode:
            return 0.8

        # Alt küme kontrolü (bir string diğerinin içinde geçiyorsa)
        if str1 in str2:
            # Eğer str1, str2'nin başında veya sonunda ise daha yüksek puan ver
            if str2.startswith(str1) or str2.endswith(str1):
                return 0.9
            # Ortada ise biraz daha düşük puan ver
            else:
                return 0.8
        elif str2 in str1:
            # Eğer str2, str1'in başında veya sonunda ise daha yüksek puan ver
            if str1.startswith(str2) or str1.endswith(str2):
                return 0.9
            # Ortada ise biraz daha düşük puan ver
            else:
                return 0.8

        # Kelime bazlı benzerlik
        words1 = set(re.findall(r'\w+', str1))
        words2 = set(re.findall(r'\w+', str2))

        if words1 and words2:
            # Ortak kelime oranı
            common_words = words1.intersection(words2)
            word_similarity = len(common_words) / max(len(words1), len(words2))

            # Eğer ortak kelime oranı yüksekse
            if word_similarity > 0.7:
                return 0.7 + (word_similarity * 0.3)  # 0.7 ile 1.0 arasında bir değer

        # Difflib ile benzerlik (sequence matcher)
        sequence_similarity = difflib.SequenceMatcher(None, str1, str2).ratio()

        # Levenshtein mesafesi ile benzerlik
        max_len = max(len(str1), len(str2))
        if max_len > 0:
            levenshtein_similarity = 1 - (self.levenshtein_distance(str1, str2) / max_len)
        else:
            levenshtein_similarity = 0

        # Ortak karakter sayısını bul
        common_chars = sum(1 for c in str1 if c in str2)

        # Temel benzerlik oranını hesapla
        char_similarity = common_chars / max(len(str1), len(str2)) if max(len(str1), len(str2)) > 0 else 0

        # Tüm benzerlik skorlarının ağırlıklı ortalamasını al
        final_similarity = (
            sequence_similarity * 0.4 +
            levenshtein_similarity * 0.3 +
            char_similarity * 0.3
        )

        return final_similarity

    def display_matches(self):
        # Treeview'ı temizle
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # Eşleşmeleri göster
        for video_file, subtitle_file in self.matches:
            self.file_tree.insert("", tk.END, values=(video_file, subtitle_file, "Eşleşti"))

        # Eşleşmeyen video dosyalarını göster
        matched_videos = [match[0] for match in self.matches]
        for video_file in self.video_files:
            if video_file not in matched_videos:
                self.file_tree.insert("", tk.END, values=(video_file, "", "Eşleşme bulunamadı"))

        # Eşleşmeyen altyazı dosyalarını göster
        matched_subtitles = [match[1] for match in self.matches]
        for subtitle_file in self.subtitle_files:
            if subtitle_file not in matched_subtitles:
                self.file_tree.insert("", tk.END, values=("", subtitle_file, "Eşleşme bulunamadı"))

    def show_context_menu(self, event):
        # Tıklanan öğeyi seç
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def manual_match(self):
        # Seçili öğeyi al
        selected_item = self.file_tree.selection()
        if not selected_item:
            messagebox.showinfo("Bilgi", "Lütfen bir dosya seçin.")
            return

        # Seçili öğenin değerlerini al
        values = self.file_tree.item(selected_item[0], "values")
        video_file = values[0]
        subtitle_file = values[1]

        folder_path = self.folder_path_var.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin.")
            return

        # Eğer video dosyası seçilmişse
        if video_file and not subtitle_file:
            # Altyazı dosyasını seçmek için iletişim kutusu göster
            subtitle_options = [f for f in self.subtitle_files if f not in [match[1] for match in self.matches]]
            if not subtitle_options:
                messagebox.showinfo("Bilgi", "Eşleştirilecek altyazı dosyası kalmadı.")
                return

            # Altyazı seçme penceresi
            self.show_subtitle_selector(video_file, subtitle_options)

        # Eğer altyazı dosyası seçilmişse
        elif subtitle_file and not video_file:
            # Video dosyasını seçmek için iletişim kutusu göster
            video_options = [f for f in self.video_files if f not in [match[0] for match in self.matches]]
            if not video_options:
                messagebox.showinfo("Bilgi", "Eşleştirilecek video dosyası kalmadı.")
                return

            # Video seçme penceresi
            self.show_video_selector(subtitle_file, video_options)

    def show_subtitle_selector(self, video_file, subtitle_options):
        # Altyazı seçme penceresi
        selector = tk.Toplevel(self.root)
        selector.title("Altyazı Dosyası Seç")
        selector.geometry("500x400")
        selector.transient(self.root)
        selector.grab_set()

        # Tema uygula
        selector.configure(bg=self.current_theme["bg"])

        # Açıklama
        label = ttk.Label(selector, text=f"'{video_file}' için bir altyazı dosyası seçin:")
        label.pack(pady=10)

        # Liste kutusu
        subtitle_listbox = tk.Listbox(selector, width=70, height=15,
                                     bg=self.current_theme["listbox_bg"],
                                     fg=self.current_theme["listbox_fg"],
                                     selectbackground=self.current_theme["treeview_selected_bg"],
                                     selectforeground=self.current_theme["treeview_selected_fg"],
                                     borderwidth=1,
                                     highlightbackground=self.current_theme["button_bg"])
        subtitle_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Altyazı dosyalarını listeye ekle
        for subtitle in subtitle_options:
            subtitle_listbox.insert(tk.END, subtitle)

        # Butonlar
        button_frame = ttk.Frame(selector)
        button_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(button_frame, text="Seç", command=lambda: self.add_manual_match(video_file, subtitle_listbox.get(subtitle_listbox.curselection()[0]) if subtitle_listbox.curselection() else None, selector)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=selector.destroy).pack(side=tk.LEFT, padx=5)

    def show_video_selector(self, subtitle_file, video_options):
        # Video seçme penceresi
        selector = tk.Toplevel(self.root)
        selector.title("Video Dosyası Seç")
        selector.geometry("500x400")
        selector.transient(self.root)
        selector.grab_set()

        # Tema uygula
        selector.configure(bg=self.current_theme["bg"])

        # Açıklama
        label = ttk.Label(selector, text=f"'{subtitle_file}' için bir video dosyası seçin:")
        label.pack(pady=10)

        # Liste kutusu
        video_listbox = tk.Listbox(selector, width=70, height=15,
                                  bg=self.current_theme["listbox_bg"],
                                  fg=self.current_theme["listbox_fg"],
                                  selectbackground=self.current_theme["treeview_selected_bg"],
                                  selectforeground=self.current_theme["treeview_selected_fg"],
                                  borderwidth=1,
                                  highlightbackground=self.current_theme["button_bg"])
        video_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Video dosyalarını listeye ekle
        for video in video_options:
            video_listbox.insert(tk.END, video)

        # Butonlar
        button_frame = ttk.Frame(selector)
        button_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(button_frame, text="Seç", command=lambda: self.add_manual_match(video_listbox.get(video_listbox.curselection()[0]) if video_listbox.curselection() else None, subtitle_file, selector)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=selector.destroy).pack(side=tk.LEFT, padx=5)

    def add_manual_match(self, video_file, subtitle_file, selector):
        if not video_file or not subtitle_file:
            messagebox.showinfo("Bilgi", "Lütfen bir dosya seçin.")
            return

        # create_match fonksiyonunu kullan (aynı mantık)
        self.create_match(video_file, subtitle_file)
        selector.destroy()



    def on_drag_start(self, event):
        """Sürükleme işlemini başlat"""
        # Tıklanan öğeyi belirle
        item = self.file_tree.identify_row(event.y)
        if not item:
            return

        # Sürükleme verilerini kaydet
        self.drag_source_item = item
        self.drag_source_values = self.file_tree.item(item, "values")
        self.drag_data["item"] = item
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        # Sürüklenen öğeyi vurgula
        self.file_tree.selection_set(item)

        # Görsel geri bildirim için sürükleme etiketini oluştur
        self.create_drag_image(event)

    def create_drag_image(self, event):
        """Sürükleme sırasında görsel geri bildirim için etiket oluştur"""
        # Mevcut sürükleme etiketini temizle
        if hasattr(self, 'drag_label') and self.drag_label:
            self.drag_label.destroy()

        # Sürüklenen öğenin değerlerini al
        values = self.drag_source_values
        video_file = values[0]
        subtitle_file = values[1]

        # Hangi dosyanın sürüklendiğini belirle - Sadece tıklanan dosyayı göster
        column = self.file_tree.identify_column(event.x)

        # Tıklanan sütuna göre video veya altyazı göster
        if column == "#1":  # Video sütunu
            if video_file:
                drag_text = f"{video_file}"
            else:
                drag_text = "???"
        elif column == "#2":  # Altyazı sütunu
            if subtitle_file:
                drag_text = f"{subtitle_file}"
            else:
                drag_text = "???"
        else:
            # Durum sütunu veya belirsiz durum
            if video_file and not subtitle_file:
                drag_text = f"{video_file}"
            elif subtitle_file and not video_file:
                drag_text = f"{subtitle_file}"
            else:
                drag_text = "???"

        # Sürükleme etiketini oluştur
        self.drag_label = tk.Label(self.root, text=drag_text, relief=tk.RAISED,
                                  bg=self.current_theme["drag_label_bg"],
                                  fg=self.current_theme["drag_label_fg"],
                                  padx=5, pady=3, borderwidth=2)
        self.drag_label.place(x=event.x_root - self.root.winfo_rootx(),
                             y=event.y_root - self.root.winfo_rooty())

    def on_drag_motion(self, event):
        """Sürükleme sırasında"""
        if not self.drag_source_item:
            return

        # İmleç altındaki öğeyi belirle
        target_item = self.file_tree.identify_row(event.y)
        if target_item and target_item != self.drag_source_item:
            # Hedef öğeyi vurgula
            self.file_tree.selection_set(target_item)
            self.drop_target_item = target_item

        # Sürükleme etiketini güncelle
        if hasattr(self, 'drag_label') and self.drag_label:
            self.drag_label.place(x=event.x_root - self.root.winfo_rootx(),
                                 y=event.y_root - self.root.winfo_rooty())

    def on_drag_release(self, event):
        """Sürükleme işlemini bitir ve bırakma işlemini gerçekleştir"""
        # Sürükleme etiketini temizle
        if hasattr(self, 'drag_label') and self.drag_label:
            self.drag_label.destroy()
            self.drag_label = None

        if not self.drag_source_item or not self.drop_target_item:
            self.reset_drag_data()
            return

        # Kaynak ve hedef öğelerin değerlerini al
        source_values = self.drag_source_values
        target_values = self.file_tree.item(self.drop_target_item, "values")

        source_video = source_values[0]
        source_subtitle = source_values[1]
        target_video = target_values[0]
        target_subtitle = target_values[1]

        # Eşleştirme mantığı - Genişletilmiş

        # 1. Video -> Altyazı (veya boş)
        if source_video and target_subtitle and not target_video:
            self.create_match(source_video, target_subtitle)

        # 2. Altyazı -> Video (veya boş)
        elif source_subtitle and target_video and not target_subtitle:
            self.create_match(target_video, source_subtitle)

        # 3. Eşleşmiş öğe -> Video (eşleşmeyi güncelle)
        elif source_video and source_subtitle and target_video and not target_subtitle:
            self.create_match(target_video, source_subtitle)

        # 4. Eşleşmiş öğe -> Altyazı (eşleşmeyi güncelle)
        elif source_video and source_subtitle and not target_video and target_subtitle:
            self.create_match(source_video, target_subtitle)

        # 5. Video -> Eşleşmiş öğe (eşleşmeyi güncelle)
        elif source_video and not source_subtitle and target_video and target_subtitle:
            self.create_match(source_video, target_subtitle)

        # 6. Altyazı -> Eşleşmiş öğe (eşleşmeyi güncelle)
        elif not source_video and source_subtitle and target_video and target_subtitle:
            self.create_match(target_video, source_subtitle)

        # 7. Eşleşmiş öğe -> Eşleşmiş öğe (eşleşmeleri değiştir)
        elif source_video and source_subtitle and target_video and target_subtitle:
            # Eşleşmeleri doğrudan değiştir (onay sorma)
            self.swap_matches(source_video, source_subtitle, target_video, target_subtitle)

        # Diğer durumlar için kullanıcıya bilgi ver
        else:
            messagebox.showinfo("Bilgi", "Eşleştirme için bir video dosyasını bir altyazı dosyasının üzerine (veya tersi) sürükleyin.")

        self.reset_drag_data()

    def swap_matches(self, video1, subtitle1, video2, subtitle2):
        """İki eşleşmeyi birbiriyle değiştir"""
        # Yeni eşleşme listesi oluştur
        new_matches = []

        # Tüm eşleşmeleri gözden geçir
        for v, s in self.matches:
            if v == video1 and s == subtitle1:
                # İlk eşleşmeyi değiştir
                new_matches.append((video1, subtitle2))
            elif v == video2 and s == subtitle2:
                # İkinci eşleşmeyi değiştir
                new_matches.append((video2, subtitle1))
            else:
                # Diğer eşleşmeleri koru
                new_matches.append((v, s))

        # Eşleşme listesini güncelle
        self.matches = new_matches

        # Listeyi güncelle
        self.display_matches()
        self.status_var.set(f"Eşleşmeler değiştirildi: '{video1}' ve '{video2}'")

    def reset_drag_data(self):
        """Sürükleme verilerini sıfırla"""
        self.drag_source_item = None
        self.drag_source_values = None
        self.drop_target_item = None
        self.drag_data = {"item": None, "x": 0, "y": 0}

    def create_match(self, video_file, subtitle_file):
        """Yeni bir eşleştirme oluştur veya mevcut eşleştirmeyi güncelle"""
        # Önce tüm eşleşmeleri kopyala
        new_matches = []

        # Altyazı ve video için mevcut eşleşmeleri kontrol et
        video_matched = False

        # Tüm eşleşmeleri gözden geçir
        for v, s in self.matches:
            # Eğer bu video dosyası ise, yeni altyazı ile eşleştir
            if v == video_file:
                new_matches.append((video_file, subtitle_file))
                video_matched = True
            # Eğer bu altyazı dosyası ise, atla (kaldır)
            elif s == subtitle_file:
                continue
            # Diğer eşleşmeleri koru
            else:
                new_matches.append((v, s))

        # Eğer video hiç eşleşmemişse, yeni eşleşme ekle
        if not video_matched:
            new_matches.append((video_file, subtitle_file))

        # Eşleşme listesini güncelle
        self.matches = new_matches

        # Listeyi güncelle
        self.display_matches()

        # Kullanıcıya bilgi ver
        self.status_var.set(f"'{video_file}' ve '{subtitle_file}' eşleştirildi.")

    def remove_match(self):
        # Seçili öğeyi al
        selected_item = self.file_tree.selection()
        if not selected_item:
            messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
            return

        # Seçili öğenin değerlerini al
        values = self.file_tree.item(selected_item[0], "values")
        video_file = values[0]
        subtitle_file = values[1]

        # Eğer hem video hem de altyazı varsa, eşleşmeyi kaldır
        if video_file and subtitle_file:
            for i, (v, s) in enumerate(self.matches):
                if v == video_file and s == subtitle_file:
                    self.matches.pop(i)
                    self.display_matches()
                    return

    def rename_subtitles(self):
        folder_path = self.folder_path_var.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin.")
            return

        if not self.matches:
            messagebox.showinfo("Bilgi", "Yeniden adlandırılacak eşleşme bulunamadı.")
            return

        renamed_count = 0
        errors = []

        for video_file, subtitle_file in self.matches:
            video_name, _ = os.path.splitext(video_file)
            _, subtitle_ext = os.path.splitext(subtitle_file)

            new_subtitle_name = video_name + subtitle_ext

            # Eğer yeni isim zaten varsa, atla
            if new_subtitle_name == subtitle_file:
                continue

            try:
                old_path = os.path.join(folder_path, subtitle_file)
                new_path = os.path.join(folder_path, new_subtitle_name)

                # Eğer hedef dosya zaten varsa, yedekle
                if os.path.exists(new_path):
                    backup_name = new_subtitle_name + ".bak"
                    backup_path = os.path.join(folder_path, backup_name)
                    os.rename(new_path, backup_path)

                # Altyazıyı yeniden adlandır
                os.rename(old_path, new_path)
                renamed_count += 1

            except Exception as e:
                errors.append(f"{subtitle_file}: {str(e)}")

        # Hata varsa göster
        if errors:
            error_message = "\n".join(errors)
            messagebox.showerror("Hatalar", f"Bazı dosyalar yeniden adlandırılamadı:\n{error_message}")

        # Durum çubuğunda bilgi göster
        if renamed_count > 0:
            self.status_var.set(f"{renamed_count} altyazı dosyası başarıyla yeniden adlandırıldı.")
            self.scan_files()  # Listeyi güncelle
        else:
            self.status_var.set("Hiçbir dosya yeniden adlandırılmadı.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSubRenamer(root)
    root.mainloop()
