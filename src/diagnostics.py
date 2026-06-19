import os
import sqlite3
from .utils import RED, GREEN, YELLOW, RESET

def run_diagnostics(profile_name, conv_path):
    """Scans all databases in a conversation path for integrity issues, stuck steps, and malformed types."""
    report = {
        "profile": profile_name,
        "path": conv_path,
        "total_dbs": 0,
        "corrupted_dbs": [],
        "stuck_dbs": {},
        "malformed_protobufs": {},
        "conflict_files": []
    }
    
    if not os.path.exists(conv_path):
        return report
        
    # Scan for conflict files (*(1)*, shm/wal orphans, etc.)
    for f in os.listdir(conv_path):
        f_path = os.path.join(conv_path, f)
        if os.path.isfile(f_path):
            # Check for conflict files
            if " (1)" in f or ".temp_" in f or ".pre_repair" in f or ".backup_" in f:
                report["conflict_files"].append(f)
                
    db_files = [f for f in os.listdir(conv_path) if f.endswith('.db')]
    report["total_dbs"] = len(db_files)
    
    for db_file in sorted(db_files):
        db_path = os.path.join(conv_path, db_file)
        
        # Skip checking if file is size 0 (empty)
        sz = os.path.getsize(db_path)
        if sz == 0:
            print(f"  • {db_file} (0 KB) -> {YELLOW}EMPTY{RESET}")
            continue
            
        print(f"  • Scanning {db_file} ({sz/1024:.1f} KB)... ", end="", flush=True)
            
        conn = None
        is_corrupted = False
        res = "ok"
        stuck_count = 0
        malformed_count = 0
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. Check integrity
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()[0]
            if res != "ok":
                is_corrupted = True
                report["corrupted_dbs"].append((db_file, res))
                
            # 2. Check for stuck steps (status 1=PENDING/INIT, 2=RUNNING, 8=WAITING)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM steps WHERE status IN (1, 2, 8);")
                stuck_count = cursor.fetchone()[0]
                if stuck_count > 0:
                    report["stuck_dbs"][db_file] = stuck_count
                    
            # 3. Check for malformed protobufs (numeric data in gen_metadata.data blob column)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gen_metadata';")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM gen_metadata WHERE typeof(data) IN ('integer', 'real', 'text');")
                malformed_count = cursor.fetchone()[0]
                if malformed_count > 0:
                    report["malformed_protobufs"][db_file] = malformed_count
                    
        except Exception as e:
            is_corrupted = True
            res = str(e)
            report["corrupted_dbs"].append((db_file, res))
        finally:
            if conn:
                conn.close()
                
        # Verbose terminal reporting
        status_strs = []
        if is_corrupted:
            status_strs.append(f"{RED}CORRUPTED ({res}){RESET}")
        if stuck_count > 0:
            status_strs.append(f"{YELLOW}{stuck_count} stuck steps{RESET}")
        if malformed_count > 0:
            status_strs.append(f"{YELLOW}{malformed_count} bad protobufs{RESET}")
            
        if not status_strs:
            print(f"{GREEN}[OK]{RESET}")
        else:
            print(f"{', '.join(status_strs)}")
                
    return report
