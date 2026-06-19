# 🚀 Antigravity Pulse Debugger

Welcome! This tool is designed to diagnose and repair issues with your Antigravity applications automatically in just **one click**. 

**You do NOT need to know anything about programming to use this tool.** 

---

## ⚡ Direct Quick Start (One-Click Run)

To run the debugger right now:
1. Click this link: **[Run run_debugger.bat](file:///C:/Users/Vhaloo/Documents/AntigravityDebugger/run_debugger.bat)** (or double-click the `run_debugger.bat` file in this folder).
2. A console window will open. Follow the on-screen options to scan and repair your databases!

---

## 🔧 Automatic Prerequisites Setup (No Install Needed)

The debugger is completely self-contained and handles its own setup:
* **Python**: If Python is missing from your system, the script will offer to install it for you automatically using the built-in Windows Package Manager (`winget`).
* **SQLite Engine**: If the database repair engine (`sqlite3.exe`) is missing, the tool will automatically download it from the official SQLite website and configure it locally.

---

## 📋 What Does It Do?

When you run the tool, you can choose from these options:
1. **Scan and Show Diagnostics Report**: Tells you if there is any corruption or stuck files without changing anything (safe view mode).
2. **Full Repair**: Runs a safe, non-destructive repair:
   * **Fixes Corrupted Databases**: Rebuilds damaged databases securely.
   * **Unblocks Frozen Tasks**: Cancels stuck background agents that cause infinite loading screens.
   * **Fixes Protocol Mismatches**: Repairs invalid data types that cause crashes.
3. **Archive Conflict Files**: Sweeps and moves temporary/conflicted files (like OneDrive duplicates) to a safe `archive_corrupted` backup folder.

---

## 🛡️ Safe and Non-Destructive

* **Auto-Backups**: Before modifying any database, the tool creates a backup copy in your `archive_corrupted` folder. Your conversation history is always safe.
* **Radical Accuracy**: Only invalid, malformed, or zombified records are updated.

---

## 💻 Running via Command Line (For Developers)

If you prefer to run it manually from Command Prompt or PowerShell:
```bash
python -m src.main
```

---

*MIT License. Created by Valentin Wittwe.*
