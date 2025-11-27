import zipfile
import os
import shutil

def create_zip():
    # Define paths
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    zip_name = "MailOtomasyonu_Final.zip"
    zip_path = os.path.join(desktop, zip_name)
    
    # Files to include
    files_to_include = [
        'bulk_email_app.py',
        'install_animation.py',
        'KUR.bat',
        'requirements.txt',
        'icon.ico',
        'README.md',
        'OKUBENI.md',
        'KURULUM_REHBERI.md',
        'MAC_BUILD.md',
        'MAC_SORUN_GIDERME.md',
        'build_mac.sh',
        'push_github.bat'
    ]
    
    # Folders to include (if any, e.g. .github for workflows)
    folders_to_include = ['.github']

    print(f"Creating zip at: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add specific files
            for file in files_to_include:
                if os.path.exists(file):
                    print(f"Adding {file}...")
                    zipf.write(file, file)
                else:
                    print(f"Warning: {file} not found.")
            
            # Add specific folders
            for folder in folders_to_include:
                if os.path.exists(folder):
                    print(f"Adding folder {folder}...")
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                            
        print("Zip created successfully!")
    except Exception as e:
        print(f"Error creating zip: {e}")

if __name__ == "__main__":
    create_zip()
