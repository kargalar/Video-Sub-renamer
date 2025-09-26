# Kütüphanelerin yüklü olup olmadığını kontrol et
print("Kütüphane kontrol sonuçları:")

# Python yollarını yazdır
import sys
print("Python yolları:")
for path in sys.path:
    print(f"- {path}")
print("\n")

# Gerekli kütüphaneleri kontrol et
required_libraries = [
    'tkinter'
]

missing_libraries = []
for lib in required_libraries:
    try:
        __import__(lib)
        print(f"✓ {lib} - yüklü")
    except ImportError:
        print(f"✗ {lib} - eksik")
        missing_libraries.append(lib)

if missing_libraries:
    print(f"\nEksik kütüphaneler: {', '.join(missing_libraries)}")
    print("Lütfen pip install ile eksik kütüphaneleri yükleyin.")
    sys.exit(1)

print("\nTüm gerekli kütüphaneler yüklü. Uygulama başlatılıyor...\n")

# Uygulamayı başlat
from ui.main_window import VideoSubRenamerApp

if __name__ == "__main__":
    try:
        app = VideoSubRenamerApp()
        app.run()
    except Exception as e:
        print(f"Uygulama başlatılırken hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()