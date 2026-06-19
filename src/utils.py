import os
import sys
import ctypes
import shutil
import subprocess

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

def find_sqlite_exe():
    """Searches for sqlite3.exe on the system, prioritizing DaVinci Resolve's copy."""
    # 1. Check system path
    exe_path = shutil.which("sqlite3")
    if exe_path:
        return exe_path
        
    # 2. Check DaVinci Resolve path
    resolve_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\sqlite3.exe"
    if os.path.exists(resolve_path):
        return resolve_path
        
    # 3. Check Program Files search
    common_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    for cp in common_paths:
        try:
            # Look in DaVinci Resolve directory directly if DaVinci is installed differently
            test_path = os.path.join(cp, "Blackmagic Design", "DaVinci Resolve", "sqlite3.exe")
            if os.path.exists(test_path):
                return test_path
        except Exception:
            pass
            
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
            if "antigravity" in tasks:
                processes.append("Antigravity Desktop")
            if "language_server" in tasks:
                processes.append("Language Server")
            if "agy.exe" in tasks:
                processes.append("agy CLI")
    except Exception:
        pass
    return processes
