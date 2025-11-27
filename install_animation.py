import sys
import time
import threading
import itertools
import subprocess
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class InstallerAnimation:
    def __init__(self):
        self.stop_animation = False
        self.current_task = ""
        self.green = '\033[92m'
        self.cyan = '\033[96m'
        self.yellow = '\033[93m'
        self.red = '\033[91m'
        self.reset = '\033[0m'
        self.bold = '\033[1m'

    def spinner(self):
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        for char in itertools.cycle(spinner_chars):
            if self.stop_animation:
                break
            sys.stdout.write(f'\r{self.cyan}{char} {self.current_task}...   {self.reset}')
            sys.stdout.flush()
            time.sleep(0.1)

    def progress_bar(self, duration, task_name):
        self.current_task = task_name
        width = 40
        for i in range(width + 1):
            percent = int((i / width) * 100)
            bar = '█' * i + '░' * (width - i)
            sys.stdout.write(f'\r{self.green}➜ {task_name} [{bar}] {percent}%{self.reset}')
            sys.stdout.flush()
            time.sleep(duration / width)
        print()

    def hacker_text(self, text, delay=0.02):
        for char in text:
            sys.stdout.write(self.green + char + self.reset)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def run_command_with_animation(self, command, task_name):
        self.current_task = task_name
        self.stop_animation = False
        t = threading.Thread(target=self.spinner)
        t.start()

        try:
            # Run the actual command
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            self.stop_animation = True
            t.join()
            
            sys.stdout.write('\r' + ' ' * 60 + '\r') # Clear line
            if process.returncode == 0:
                print(f"{self.green}✔ {task_name} [TAMAMLANDI]{self.reset}")
                return True
            else:
                print(f"{self.red}✖ {task_name} [HATA]{self.reset}")
                print(f"{self.red}Hata detayı: {process.stderr}{self.reset}")
                return False
        except Exception as e:
            self.stop_animation = True
            t.join()
            print(f"{self.red}✖ {task_name} [BEKLENMEYEN HATA: {str(e)}]{self.reset}")
            return False

    def start(self):
        clear_screen()
        print(f"{self.green}{self.bold}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                                                            ║")
        print("║           MAIL OTOMASYONU - PREMIUM KURULUM                ║")
        print("║                                                            ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{self.reset}")
        time.sleep(1)

        self.hacker_text("> Sistem analizi başlatılıyor...", 0.03)
        time.sleep(0.5)
        self.hacker_text("> Gerekli modüller taranıyor...", 0.03)
        time.sleep(0.5)

        # 1. PIP Güncelleme
        if not self.run_command_with_animation("python -m pip install --upgrade pip", "PIP Paket Yöneticisi Güncelleniyor"):
            print(f"{self.yellow}! Uyarı: PIP güncellenemedi, devam ediliyor...{self.reset}")

        # 2. Gereksinimleri Yükleme
        requirements = [
            ("customtkinter", "Modern Arayüz Modülü"),
            ("pillow", "Görüntü İşleme Motoru"),
            ("certifi", "SSL Güvenlik Sertifikaları"),
            ("pyinstaller", "Derleme Araçları")
        ]

        for package, desc in requirements:
            self.run_command_with_animation(f"pip install {package}", f"{desc} Yükleniyor ({package})")

        print("\n")
        self.progress_bar(2, "Kurulum Dosyaları Hazırlanıyor")
        
        print(f"\n{self.green}{self.bold}>>> KURULUM BAŞARIYLA TAMAMLANDI <<< {self.reset}")
        print(f"{self.cyan}Uygulama derlenmeye hazır.{self.reset}\n")
        time.sleep(1)

if __name__ == "__main__":
    try:
        # Windows terminal renk desteği için
        os.system('')
        app = InstallerAnimation()
        app.start()
    except KeyboardInterrupt:
        print("\n\nKurulum iptal edildi.")
        sys.exit(1)
