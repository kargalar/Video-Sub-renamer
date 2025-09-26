# Kütüphanelerin yüklü olup olmadığını kontrol et
print("Kütüphane kontrol sonuçları:")

# Python yollarını yazdır
import sys
print("Python yolları:")
for path in sys.path:
    print(f"- {path}")
print("\n")

import speech_recognition
import pydub
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import sys
import json
import difflib
import datetime
import codecs
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import threading
import moviepy
from moviepy import VideoFileClip


# SRT dosyalarını işlemek için kendi sınıfımız
class SubtitleItem:
    def __init__(self, index=0, start=None, end=None, content="", proprietary=""):
        self.index = index
        self.start = start or datetime.timedelta()
        self.end = end or datetime.timedelta()
        self.content = content
        self.proprietary = proprietary

    def __str__(self):
        return f"Subtitle(index={self.index}, start={self.start}, end={self.end}, content='{self.content}')"

def parse_srt(srt_content):
    """SRT dosyasını parse et ve SubtitleItem listesi döndür"""
    subs = []
    blocks = srt_content.strip().replace('\r\n', '\n').split('\n\n')

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        if len(lines) < 3:
            continue

        # İndeks
        try:
            index = int(lines[0])
        except ValueError:
            continue

        # Zaman aralığı
        time_line = lines[1]
        try:
            start_time, end_time = time_line.split(' --> ')
            start = parse_time(start_time)
            end = parse_time(end_time)
        except (ValueError, IndexError):
            continue

        # İçerik
        content = '\n'.join(lines[2:])

        # SubtitleItem oluştur
        sub = SubtitleItem(index=index, start=start, end=end, content=content)
        subs.append(sub)

    return subs

def parse_time(time_str):
    """SRT zaman formatını datetime.timedelta'ya dönüştür"""
    hours, minutes, seconds = time_str.replace(',', '.').split(':')
    hours = int(hours)
    minutes = int(minutes)
    seconds_parts = seconds.split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

    return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def format_time(td):
    """datetime.timedelta'yı SRT zaman formatına dönüştür"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = td.microseconds // 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def compose_srt(subs):
    """SubtitleItem listesini SRT formatına dönüştür"""
    result = []

    for i, sub in enumerate(subs, 1):
        # İndeks
        result.append(str(i))

        # Zaman aralığı
        result.append(f"{format_time(sub.start)} --> {format_time(sub.end)}")

        # İçerik
        result.append(sub.content)

        # Boş satır
        result.append("")

    return "\n".join(result)



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

        # Son klasör yolunu yükle
        last_folder = self.load_folder_path()
        if last_folder:
            self.folder_path_var.set(last_folder)

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

    def load_folder_path(self):
        """Kaydedilmiş klasör yolunu yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('last_folder', '')
        except Exception as e:
            print(f"Klasör yolu yüklenirken hata oluştu: {str(e)}")
        return ''

    def save_folder_path(self):
        """Klasör yolunu kaydet"""
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
            settings['last_folder'] = self.folder_path_var.get()
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Klasör yolu kaydedilirken hata oluştu: {str(e)}")

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
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Manuel Altyazı Senkronizasyonu", command=self.sync_subtitle)
        self.context_menu.add_command(label="Otomatik Altyazı Senkronizasyonu", command=self.auto_sync_subtitle)

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

        sync_button = ttk.Button(button_frame, text="Manuel Senkronizasyon", command=self.sync_subtitle)
        sync_button.pack(side=tk.LEFT, padx=5)

        auto_sync_button = ttk.Button(button_frame, text="Otomatik Senkronizasyon", command=self.auto_sync_subtitle)
        auto_sync_button.pack(side=tk.LEFT, padx=5)

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
            self.save_folder_path()  # Klasör yolunu kaydet
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

        # Eşleşmeyen videolara -- ön eki ekle
        folder_path = self.folder_path_var.get()
        for video_file in unmatched_videos:
            if not video_file.startswith('--'):
                old_path = os.path.join(folder_path, video_file)
                new_name = '--' + video_file
                new_path = os.path.join(folder_path, new_name)
                try:
                    os.rename(old_path, new_path)
                    # Listeyi güncelle
                    self.video_files = [new_name if v == video_file else v for v in self.video_files]
                except Exception as e:
                    print(f"Dosya yeniden adlandırılamadı: {video_file} - {str(e)}")

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

    def on_drag_release(self, _):
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
        folder_path = self.folder_path_var.get()

        # Eğer video -- ile başlıyorsa, --'yi kaldır
        if video_file.startswith('--'):
            old_path = os.path.join(folder_path, video_file)
            new_video_name = video_file[2:]  # --'yi kaldır
            new_path = os.path.join(folder_path, new_video_name)
            try:
                os.rename(old_path, new_path)
                video_file = new_video_name  # Yeni adı kullan
                # Listeyi güncelle
                self.video_files = [new_video_name if v == '--' + new_video_name else v for v in self.video_files]
            except Exception as e:
                print(f"Dosya yeniden adlandırılamadı: {video_file} - {str(e)}")

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
            folder_path = self.folder_path_var.get()
            for i, (v, s) in enumerate(self.matches):
                if v == video_file and s == subtitle_file:
                    self.matches.pop(i)
                    # Video dosyasına -- ön eki ekle
                    if not video_file.startswith('--'):
                        old_path = os.path.join(folder_path, video_file)
                        new_name = '--' + video_file
                        new_path = os.path.join(folder_path, new_name)
                        try:
                            os.rename(old_path, new_path)
                            # Listeyi güncelle
                            self.video_files = [new_name if v == video_file else v for v in self.video_files]
                        except Exception as e:
                            print(f"Dosya yeniden adlandırılamadı: {video_file} - {str(e)}")
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

    def sync_subtitle(self):
        """Seçili altyazı dosyasını senkronize et"""
        # Seçili öğeyi al
        selected_item = self.file_tree.selection()
        if not selected_item:
            messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
            return

        # Seçili öğenin değerlerini al
        values = self.file_tree.item(selected_item[0], "values")
        video_file = values[0]
        subtitle_file = values[1]

        # Eğer hem video hem de altyazı varsa, senkronizasyon penceresini aç
        if video_file and subtitle_file:
            folder_path = self.folder_path_var.get()
            if not folder_path or not os.path.isdir(folder_path):
                messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin.")
                return

            subtitle_path = os.path.join(folder_path, subtitle_file)

            # Altyazı dosyasının varlığını kontrol et
            if not os.path.exists(subtitle_path):
                messagebox.showerror("Hata", f"Altyazı dosyası bulunamadı: {subtitle_file}")
                return

            # Altyazı senkronizasyon penceresini aç
            self.show_sync_dialog(subtitle_path, subtitle_file)
        else:
            messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

    def show_sync_dialog(self, subtitle_path, subtitle_file):
        """Altyazı senkronizasyon penceresini göster"""
        # Altyazı senkronizasyon penceresi
        sync_dialog = tk.Toplevel(self.root)
        sync_dialog.title(f"Altyazı Senkronizasyonu - {subtitle_file}")
        sync_dialog.geometry("600x400")
        sync_dialog.transient(self.root)
        sync_dialog.grab_set()

        # Tema uygula
        sync_dialog.configure(bg=self.current_theme["bg"])

        # Ana çerçeve
        main_frame = ttk.Frame(sync_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Açıklama
        ttk.Label(main_frame, text="Altyazı zamanlamasını ayarlayın:").pack(pady=(0, 10))

        # Zaman kaydırma bölümü
        time_frame = ttk.LabelFrame(main_frame, text="Zaman Kaydırma", padding="10")
        time_frame.pack(fill=tk.X, pady=5)

        # Saniye ve milisaniye giriş alanları
        input_frame = ttk.Frame(time_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Saniye:").grid(row=0, column=0, padx=5, pady=5)
        seconds_var = tk.StringVar(value="0")
        seconds_entry = ttk.Entry(input_frame, textvariable=seconds_var, width=10)
        seconds_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Milisaniye:").grid(row=0, column=2, padx=5, pady=5)
        milliseconds_var = tk.StringVar(value="0")
        milliseconds_entry = ttk.Entry(input_frame, textvariable=milliseconds_var, width=10)
        milliseconds_entry.grid(row=0, column=3, padx=5, pady=5)

        # Yön seçimi (ileri/geri)
        direction_var = tk.StringVar(value="forward")
        forward_radio = ttk.Radiobutton(input_frame, text="İleri", variable=direction_var, value="forward")
        forward_radio.grid(row=0, column=4, padx=5, pady=5)
        backward_radio = ttk.Radiobutton(input_frame, text="Geri", variable=direction_var, value="backward")
        backward_radio.grid(row=0, column=5, padx=5, pady=5)

        # Slider
        slider_frame = ttk.Frame(time_frame)
        slider_frame.pack(fill=tk.X, pady=10)

        ttk.Label(slider_frame, text="-10s").pack(side=tk.LEFT)
        time_slider = ttk.Scale(slider_frame, from_=-10, to=10, orient=tk.HORIZONTAL, length=400)
        time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        time_slider.set(0)  # Başlangıç değeri
        ttk.Label(slider_frame, text="+10s").pack(side=tk.LEFT)

        # Slider değeri değiştiğinde saniye ve milisaniye alanlarını güncelle
        def update_time_values(_):
            value = time_slider.get()
            if value >= 0:
                direction_var.set("forward")
            else:
                direction_var.set("backward")
                value = abs(value)

            seconds = int(value)
            milliseconds = int((value - seconds) * 1000)
            seconds_var.set(str(seconds))
            milliseconds_var.set(str(milliseconds))

        time_slider.bind("<Motion>", update_time_values)

        # Önizleme bölümü
        preview_frame = ttk.LabelFrame(main_frame, text="Önizleme", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Altyazı içeriğini göster
        preview_text = tk.Text(preview_frame, wrap=tk.WORD, height=10,
                              bg=self.current_theme["treeview_bg"],
                              fg=self.current_theme["treeview_fg"])
        preview_text.pack(fill=tk.BOTH, expand=True)

        # Altyazı dosyasını yükle ve önizleme göster
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
            preview_text.insert(tk.END, subtitle_content[:1000] + "...\n\n(Önizleme ilk 1000 karakteri göstermektedir)")
        except Exception as e:
            preview_text.insert(tk.END, f"Altyazı dosyası yüklenirken hata oluştu: {str(e)}")

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Senkronize et butonu
        def apply_sync():
            try:
                seconds = int(seconds_var.get() or "0")
                milliseconds = int(milliseconds_var.get() or "0")
                direction = direction_var.get()

                # Toplam zaman farkını hesapla (milisaniye cinsinden)
                time_shift = seconds * 1000 + milliseconds
                if direction == "backward":
                    time_shift = -time_shift

                # Altyazıyı senkronize et
                success = self.shift_subtitle_timing(subtitle_path, time_shift)

                if success:
                    messagebox.showinfo("Başarılı", f"Altyazı başarıyla senkronize edildi.\nZaman kaydırma: {time_shift} ms")
                    sync_dialog.destroy()
                else:
                    messagebox.showerror("Hata", "Altyazı senkronize edilirken bir hata oluştu.")
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

        ttk.Button(button_frame, text="Senkronize Et", command=apply_sync).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=sync_dialog.destroy).pack(side=tk.LEFT, padx=5)

    def shift_subtitle_timing(self, subtitle_path, time_shift_ms):
        """Altyazı zamanlamasını kaydır"""
        try:
            # Altyazı dosyasını oku
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()

            # SRT dosyasını parse et
            subs = parse_srt(subtitle_content)

            # Zaman kaydırma miktarını timedelta olarak hesapla
            time_shift = datetime.timedelta(milliseconds=time_shift_ms)

            # Her altyazı için zamanlamayı kaydır
            for sub in subs:
                sub.start += time_shift
                sub.end += time_shift

                # Negatif zamanları düzelt
                if sub.start.total_seconds() < 0:
                    sub.start = datetime.timedelta(0)
                if sub.end.total_seconds() < 0:
                    sub.end = datetime.timedelta(milliseconds=1)

            # Değiştirilmiş altyazıyı kaydet
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(compose_srt(subs))

            return True
        except Exception as e:
            print(f"Altyazı senkronize edilirken hata oluştu: {str(e)}")
            return False

    def auto_sync_subtitle(self):


        # Seçili öğeyi al
        selected_item = self.file_tree.selection()
        if not selected_item:
            messagebox.showinfo("Bilgi", "Lütfen bir eşleşme seçin.")
            return

        # Seçili öğenin değerlerini al
        values = self.file_tree.item(selected_item[0], "values")
        video_file = values[0]
        subtitle_file = values[1]

        # Eğer hem video hem de altyazı varsa, otomatik senkronizasyon işlemini başlat
        if video_file and subtitle_file:
            folder_path = self.folder_path_var.get()
            if not folder_path or not os.path.isdir(folder_path):
                messagebox.showerror("Hata", "Lütfen geçerli bir klasör seçin.")
                return

            video_path = os.path.join(folder_path, video_file)
            subtitle_path = os.path.join(folder_path, subtitle_file)

            # Dosyaların varlığını kontrol et
            if not os.path.exists(video_path):
                messagebox.showerror("Hata", f"Video dosyası bulunamadı: {video_file}")
                return

            if not os.path.exists(subtitle_path):
                messagebox.showerror("Hata", f"Altyazı dosyası bulunamadı: {subtitle_file}")
                return

            # Otomatik senkronizasyon penceresini göster
            self.show_auto_sync_dialog(video_path, subtitle_path, video_file, subtitle_file)
        else:
            messagebox.showinfo("Bilgi", "Lütfen eşleşmiş bir video ve altyazı seçin.")

    def show_auto_sync_dialog(self, video_path, subtitle_path, video_file, _):
        """Otomatik senkronizasyon penceresini göster"""
        # Otomatik senkronizasyon penceresi
        sync_dialog = tk.Toplevel(self.root)
        sync_dialog.title(f"Otomatik Altyazı Senkronizasyonu - {video_file}")
        sync_dialog.geometry("600x400")
        sync_dialog.transient(self.root)
        sync_dialog.grab_set()

        # Tema uygula
        sync_dialog.configure(bg=self.current_theme["bg"])

        # Ana çerçeve
        main_frame = ttk.Frame(sync_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Açıklama
        ttk.Label(main_frame, text="Video ve altyazı otomatik olarak senkronize edilecek.").pack(pady=(0, 10))
        ttk.Label(main_frame, text="Bu işlem birkaç dakika sürebilir.").pack(pady=(0, 10))

        # İlerleme çubuğu
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, pady=10)

        # Durum etiketi
        status_var = tk.StringVar(value="Hazırlanıyor...")
        status_label = ttk.Label(main_frame, textvariable=status_var)
        status_label.pack(pady=10)

        # Sonuç çerçevesi
        result_frame = ttk.LabelFrame(main_frame, text="Sonuç", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Sonuç metni
        result_text = tk.Text(result_frame, wrap=tk.WORD, height=10,
                             bg=self.current_theme["treeview_bg"],
                             fg=self.current_theme["treeview_fg"])
        result_text.pack(fill=tk.BOTH, expand=True)
        result_text.insert(tk.END, "İşlem başlatıldığında sonuçlar burada gösterilecek.")

        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Başlat butonu
        start_button = ttk.Button(button_frame, text="Başlat",
                                 command=lambda: self.start_auto_sync(video_path, subtitle_path,
                                                                    progress_var, status_var,
                                                                    result_text, start_button,
                                                                    cancel_button, sync_dialog))
        start_button.pack(side=tk.LEFT, padx=5)

        # İptal butonu
        cancel_button = ttk.Button(button_frame, text="İptal", command=sync_dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def start_auto_sync(self, video_path, subtitle_path, progress_var, status_var,
                       result_text, start_button, cancel_button, dialog):
        """Otomatik senkronizasyon işlemini başlat"""
        # Butonları devre dışı bırak
        start_button.config(state=tk.DISABLED)
        cancel_button.config(state=tk.DISABLED)

        # Sonuç metnini temizle
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "İşlem başlatıldı...\n")

        # İşlemi arka planda çalıştır
        thread = threading.Thread(target=self.run_auto_sync,
                                 args=(video_path, subtitle_path, progress_var, status_var,
                                      result_text, start_button, cancel_button, dialog))
        thread.daemon = True
        thread.start()

    def run_auto_sync(self, video_path, subtitle_path, progress_var, status_var,
                     result_text, start_button, cancel_button, _):
        """Otomatik senkronizasyon işlemini arka planda çalıştır"""
        try:
            # İlerleme ve durum güncelleme
            def update_ui(progress, status, result=None):
                progress_var.set(progress)
                status_var.set(status)
                if result:
                    result_text.insert(tk.END, result + "\n")
                    result_text.see(tk.END)

            # 1. Adım: Video dosyasından ses çıkarma
            update_ui(10, "Video dosyasından ses çıkarılıyor...")

            # Geçici dosya oluştur
            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, "temp_audio.wav")

            # Video dosyasından ses çıkar
            video = mp.VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)

            update_ui(30, "Ses dosyası çıkarıldı.", "Ses dosyası başarıyla çıkarıldı.")

            # 2. Adım: Altyazı dosyasını okuma
            update_ui(40, "Altyazı dosyası okunuyor...")

            try:
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    subtitle_content = f.read()
                subs = parse_srt(subtitle_content)

                # İlk birkaç altyazıyı al (en fazla 5)
                first_subs = subs[:min(5, len(subs))]

                update_ui(50, "Altyazı dosyası okundu.",
                         f"Altyazı dosyası okundu. Toplam {len(subs)} altyazı bulundu.")

            except Exception as e:
                update_ui(100, "Hata!", f"Altyazı dosyası okunurken hata oluştu: {str(e)}")
                self.enable_buttons(start_button, cancel_button)
                return

            # 3. Adım: Konuşma tanıma
            update_ui(60, "Ses dosyası analiz ediliyor...")

            # Konuşma tanıma için ses dosyasını yükle
            recognizer = sr.Recognizer()

            # İlk altyazıların zamanlarını al
            first_sub_times = [(sub.start.total_seconds(), sub.end.total_seconds(), sub.content)
                              for sub in first_subs]

            # Ses dosyasını yükle
            audio = AudioSegment.from_file(audio_path)

            # Zaman farkını hesaplamak için değişkenler
            time_diffs = []

            # Her bir altyazı için konuşma tanıma yap
            for i, (start_time, end_time, content) in enumerate(first_sub_times):
                update_ui(60 + (i * 5), f"Altyazı {i+1}/{len(first_sub_times)} analiz ediliyor...")

                # Ses dosyasından ilgili kısmı al (biraz daha geniş bir aralık)
                start_ms = max(0, int(start_time * 1000) - 2000)  # 2 saniye önce başla
                end_ms = min(len(audio), int(end_time * 1000) + 2000)  # 2 saniye sonra bitir

                # Ses segmentini al
                segment = audio[start_ms:end_ms]

                # Geçici ses dosyası oluştur
                segment_path = os.path.join(temp_dir, f"segment_{i}.wav")
                segment.export(segment_path, format="wav")

                # Konuşma tanıma
                try:
                    with sr.AudioFile(segment_path) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data, language="tr-TR")

                        # Altyazı içeriği ile karşılaştır
                        similarity = self.text_similarity(content, text)

                        if similarity > 0.3:  # Benzerlik eşiği
                            # Konuşma tanıma zamanını hesapla
                            # Bu basit bir yaklaşım, gerçek uygulamada daha karmaşık olabilir
                            detected_time = start_ms / 1000.0  # saniye cinsinden
                            subtitle_time = start_time

                            # Zaman farkını hesapla
                            time_diff = detected_time - subtitle_time
                            time_diffs.append(time_diff)

                            update_ui(60 + (i * 5), f"Altyazı {i+1} analiz edildi.",
                                     f"Altyazı: '{content}'\nTanınan: '{text}'\nBenzerlik: {similarity:.2f}\nZaman farkı: {time_diff:.2f} saniye")
                        else:
                            update_ui(60 + (i * 5), f"Altyazı {i+1} analiz edildi.",
                                     f"Altyazı: '{content}'\nTanınan: '{text}'\nBenzerlik düşük: {similarity:.2f}")

                except Exception as e:
                    update_ui(60 + (i * 5), f"Altyazı {i+1} analiz edilemedi.",
                             f"Hata: {str(e)}")

                # Geçici dosyayı temizle
                try:
                    os.remove(segment_path)
                except:
                    pass

            # 4. Adım: Zaman farkını hesapla ve altyazıyı kaydır
            update_ui(90, "Zaman farkı hesaplanıyor...")

            if time_diffs:
                # Ortalama zaman farkını hesapla
                avg_time_diff = sum(time_diffs) / len(time_diffs)

                # Milisaniye cinsinden zaman farkı
                time_shift_ms = int(avg_time_diff * 1000)

                update_ui(95, "Altyazı kaydırılıyor...",
                         f"Ortalama zaman farkı: {avg_time_diff:.2f} saniye ({time_shift_ms} ms)")

                # Altyazıyı kaydır
                success = self.shift_subtitle_timing(subtitle_path, time_shift_ms)

                if success:
                    update_ui(100, "Tamamlandı!",
                             f"Altyazı başarıyla senkronize edildi. Zaman kaydırma: {time_shift_ms} ms")
                else:
                    update_ui(100, "Hata!",
                             "Altyazı kaydırılırken bir hata oluştu.")
            else:
                update_ui(100, "Tamamlandı!",
                         "Zaman farkı hesaplanamadı. Altyazı değiştirilmedi.")

            # Geçici ses dosyasını temizle
            try:
                os.remove(audio_path)
            except:
                pass

        except Exception as e:
            # Hata durumunda
            progress_var.set(100)
            status_var.set("Hata!")
            result_text.insert(tk.END, f"İşlem sırasında bir hata oluştu: {str(e)}\n")
            result_text.see(tk.END)

        finally:
            # Butonları tekrar aktif hale getir
            self.enable_buttons(start_button, cancel_button)

    def enable_buttons(self, start_button, cancel_button):
        """Butonları tekrar aktif hale getir"""
        # Ana thread'de çalıştır
        self.root.after(0, lambda: start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: cancel_button.config(state=tk.NORMAL))

    def text_similarity(self, text1, text2):
        """İki metin arasındaki benzerliği hesapla"""
        # Metinleri temizle ve küçük harfe çevir
        text1 = re.sub(r'[^\w\s]', '', text1.lower())
        text2 = re.sub(r'[^\w\s]', '', text2.lower())

        # Kelimelere ayır
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Ortak kelime sayısı
        common_words = words1.intersection(words2)

        # Benzerlik oranı
        if not words1 or not words2:
            return 0.0

        return len(common_words) / max(len(words1), len(words2))

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoSubRenamer(root)
    root.mainloop()

