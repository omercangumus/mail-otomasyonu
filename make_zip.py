import zipfile
import os

def create_zip():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    zip_path = os.path.join(desktop, "MailOtomasyonu_Final.zip")
    
    files = [
        'bulk_email_app.py',
        'install_animation.py',
        'KUR.bat',
        'KUR.command',
        'requirements.txt',
        'icon.ico',
        'README.md',
        'OKUBENI.md',
        'KURULUM_REHBERI.md',
        'MAC_BUILD.md',
        'MAC_SORUN_GIDERME.md',
        'push_github.bat'
    ]
    
    folders = ['.github']
    
    print(f"Creating: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            if os.path.exists(file):
                print(f"+ {file}")
                zipf.write(file, file)
        
        for folder in folders:
            if os.path.exists(folder):
                print(f"+ {folder}/")
                for root, dirs, files_list in os.walk(folder):
                    for file in files_list:
                        path = os.path.join(root, file)
                        zipf.write(path, path)
    
    print("\n✅ Zip oluşturuldu!")

if __name__ == "__main__":
    create_zip()
