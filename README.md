# Bulk Email Automation Application

A desktop GUI application that automates bulk email sending based on configurable date intervals with full data persistence.

## Features

✅ **Date-Based Automation** - Sends emails based on configurable intervals (e.g., every 30 days)
✅ **Data Persistence** - Saves all settings and last send date to JSON
✅ **Modern UI** - Built with customtkinter for a sleek, dark-themed interface
✅ **Threaded Operations** - Non-blocking email sending
✅ **Smart Status Display** - Shows countdown to next send or overdue alerts
✅ **Email Validation** - Validates email addresses before saving
✅ **Test Connection** - Verify SMTP settings before sending
✅ **Force Send** - Testing mode to bypass date checks

## Installation

### Option 1: Use Pre-built Executable (Recommended)
If you have a `.exe` (Windows) or `.app` (Mac) file, simply double-click to run. No Python installation needed.

### Option 2: Run from Source
1. Install Python 3.8 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python bulk_email_app.py
   ```

## Building Executables

To create standalone executables for distribution:

### Windows (.exe)
```batch
build_windows.bat
```
Result: `dist/Toplu E-posta Otomasyonu.exe`

### Mac (.app)
```bash
chmod +x build_mac.sh
./build_mac.sh
```
Result: `dist/Toplu E-posta Otomasyonu.app` (automatically copied to Desktop)

📖 **Detailed build instructions**: See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)

## Usage

2. **First Time Setup:**
   - Go to **Configuration** tab
   - Enter your SMTP settings (Gmail: smtp.gmail.com, port 587)
   - Enter your email and app password (see below)
   - Set your email subject and message
   - Set the send interval (in days)
   - Click "Save Settings"
   - Click "Test Connection" to verify

3. **Add Recipients:**
   - Go to **Recipients** tab
   - Enter email addresses (one per line)
   - Or click "Import from File" to load from a text file
   - Click "Save Recipients"

4. **Dashboard:**
   - View current status (due or not due)
   - See countdown to next send date
   - Click "Check & Process Now" to check and send if due
   - Use "Reset & Force Send" for testing

## Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Select "Mail" and your device
4. Copy the 16-character password
5. Use this password in the application (not your regular password)

## Files

- `bulk_email_app.py` - Main application file
- `settings.json` - Auto-generated settings file (created on first run)
- `requirements.txt` - Python dependencies

## How It Works

1. When you send emails, the app saves the current date to `settings.json`
2. On startup, the app checks how many days have passed since the last send
3. If days passed >= interval, it alerts you that emails are due
4. The computer can be turned off between runs - the date is persisted in JSON

## Notes

⚠️ **Important:** Use app-specific passwords, not your main email password
⚠️ **Gmail:** May require "Less secure app access" or App Passwords
⚠️ **Testing:** Use the "Force Send" button to test without waiting for the interval

## Troubleshooting

**Connection Failed:**
- Verify SMTP server and port
- Check your email and app password
- Ensure your email provider allows SMTP access

**Emails Not Sending:**
- Check recipient email addresses are valid
- Verify all configuration fields are filled
- Check the activity log for error messages

## License

Free to use and modify.
