import os
import sys
import ctypes
import shutil
import subprocess
import urllib.request
import re
import zipfile
import io

# Enable Virtual Terminal Processing on Windows for ANSI colors
try:
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        # -11 is STD_OUTPUT_HANDLE, 7 is ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{WHITE}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def print_success(msg):
    print(f"{GREEN}[OK] {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}[i]  {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}[!]  {msg}{RESET}")

def print_error(msg):
    print(f"{RED}[ERR] {msg}{RESET}")

def download_sqlite_bin():
    """Downloads and extracts sqlite3.exe to the current directory on Windows."""
    print_info("sqlite3.exe was not found. Attempting to download it automatically from sqlite.org...")
    try:
        url = "https://www.sqlite.org/download.html"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Search for win-x64 tools
        match = re.search(r'(\d+/sqlite-tools-win-x64-\d+\.zip)', html)
        if match:
            download_url = f"https://www.sqlite.org/{match.group(1)}"
        else:
            download_url = "https://www.sqlite.org/2026/sqlite-tools-win-x64-3490000.zip"
            
        print_info(f"Downloading SQLite tools from: {download_url}")
        req_dl = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req_dl, timeout=30) as zip_response:
            zip_data = zip_response.read()
            
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            for member in z.namelist():
                if member.endswith("sqlite3.exe"):
                    # Extract to local folder
                    with z.open(member) as source, open("sqlite3.exe", "wb") as target:
                        shutil.copyfileobj(source, target)
                    print_success("sqlite3.exe successfully downloaded and installed locally!")
                    return os.path.abspath("sqlite3.exe")
    except Exception as e:
        print_error(f"Failed to automatically download SQLite: {e}")
    return None

def find_sqlite_exe(auto_download=True):
    """Searches for sqlite3 on the system, prioritizing DaVinci Resolve's copy or local/PATH copies."""
    exe_name = "sqlite3.exe" if sys.platform == "win32" else "sqlite3"
    
    # 1. Check system path
    exe_path = shutil.which(exe_name)
    if exe_path:
        return exe_path
        
    # 2. Check local folder
    local_path = os.path.abspath(exe_name)
    if os.path.exists(local_path):
        return local_path
        
    if sys.platform == "win32":
        # 3. Check DaVinci Resolve path
        resolve_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\sqlite3.exe"
        if os.path.exists(resolve_path):
            return resolve_path
            
        # 4. Check Program Files search
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
        ]
        for cp in common_paths:
            try:
                test_path = os.path.join(cp, "Blackmagic Design", "DaVinci Resolve", "sqlite3.exe")
                if os.path.exists(test_path):
                    return test_path
            except Exception:
                pass
                
        # 5. Auto download if requested
        if auto_download:
            return download_sqlite_bin()
            
    return None

def find_conversation_dirs():
    """Scans .gemini subdirectories to find active conversation folders."""
    home = os.path.expanduser("~")
    gemini_base = os.path.join(home, ".gemini")
    
    found_dirs = {}
    if not os.path.exists(gemini_base):
        return found_dirs
        
    # Scan child directories under ~/.gemini
    for entry in os.scandir(gemini_base):
        if entry.is_dir():
            conv_path = os.path.join(entry.path, "conversations")
            if os.path.exists(conv_path):
                found_dirs[entry.name] = conv_path
                
    return found_dirs

def check_running_processes():
    """Checks if any Antigravity applications or processes are active."""
    processes = []
    try:
        if sys.platform == "win32":
            # Quick check via tasklist to see if process names are present
            res = subprocess.run("tasklist", capture_output=True, text=True, errors='ignore')
            tasks = res.stdout.lower()
            if "antigravity.exe" in tasks:
                processes.append("Antigravity Desktop")
            if "language_server.exe" in tasks:
                processes.append("Language Server")
            if "agy.exe" in tasks:
                processes.append("agy CLI")
    except Exception:
        pass
    return processes

def kill_all_processes():
    """Attempts to terminate all running Antigravity processes."""
    if sys.platform != "win32":
        print_error("Process termination is only supported on Windows.")
        return False
        
    targets = ["Antigravity.exe", "language_server.exe", "agy.exe"]
    success_killed = []
    failed_killed = []
    
    for target in targets:
        try:
            # Check if running first
            res = subprocess.run("tasklist", capture_output=True, text=True, errors='ignore')
            if target.lower() in res.stdout.lower():
                print_info(f"Terminating {target}...")
                kill_res = subprocess.run(f"taskkill /F /IM {target}", capture_output=True, text=True, shell=True)
                if kill_res.returncode == 0:
                    success_killed.append(target)
                else:
                    failed_killed.append(target)
        except Exception as e:
            failed_killed.append(f"{target} ({str(e)})")
            
    if success_killed:
        print_success(f"Successfully terminated: {', '.join(success_killed)}")
    if failed_killed:
        print_error(f"Failed to terminate: {', '.join(failed_killed)}")
        
    if not success_killed and not failed_killed:
        print_success("No active Antigravity processes were found to terminate.")
        
    return len(failed_killed) == 0
