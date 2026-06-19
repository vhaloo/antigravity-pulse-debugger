import os
import sqlite3
import shutil
import time
import subprocess
from .utils import print_success, print_error, print_info

def repair_database(db_path, sqlite_exe, archive_dir):
    """Attempts to recover a malformed SQLite database using sqlite3.exe's .recover option."""
    db_file = os.path.basename(db_path)
    timestamp = int(time.time())
    
    if not os.path.exists(sqlite_exe):
        return False, "sqlite3.exe was not found. Cannot perform recovery."
        
    temp_corrupted = f"{db_path}.temp_corrupted"
    temp_recovered = f"{db_path}.temp_recovered"
    
    try:
        # Step 1: Copy to temp working file and archive copy
        shutil.copy2(db_path, temp_corrupted)
        archive_corrupted_path = os.path.join(archive_dir, f"{db_file}.corrupted_{timestamp}")
        shutil.copy2(db_path, archive_corrupted_path)
        
        # Step 2: Run SQLite recovery pipeline
        cmd = f'"{sqlite_exe}" "{temp_corrupted}" ".recover" | "{sqlite_exe}" "{temp_recovered}"'
        subprocess.run(cmd, shell=True, capture_output=True)
        
        if not os.path.exists(temp_recovered):
            return False, "Recovery pipeline did not produce a recovered database."
            
        # Step 3: Verify recovered database integrity
        conn = None
        is_healthy = False
        try:
            conn = sqlite3.connect(temp_recovered)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()[0]
            if res == "ok":
                is_healthy = True
        except Exception as e:
            res = str(e)
        finally:
            if conn:
                conn.close()
                
        if is_healthy:
            # Step 4: Backup the original and swap
            backup_path = os.path.join(archive_dir, f"{db_file}.backup_{timestamp}")
            shutil.move(db_path, backup_path)
            shutil.copy2(temp_recovered, db_path)
            return True, f"Original backed up to archive; successfully replaced with repaired database."
        else:
            return False, f"Integrity check of recovered database failed: {res}"
            
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp files
        for p in [temp_corrupted, temp_recovered]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

def fix_stuck_steps(db_path):
    """Updates stuck steps (status 1, 2, 8) to status 5 (Cancelled)."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM steps WHERE status IN (1, 2, 8);")
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute("UPDATE steps SET status = 5 WHERE status IN (1, 2, 8);")
                conn.commit()
                return True, count
        return True, 0
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()

def fix_protobuf_types(db_path):
    """Fixes malformed (numeric/text) records in the gen_metadata table by resetting them to empty BLOBs."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gen_metadata';")
        if cursor.fetchone():
            # Check count
            cursor.execute("SELECT COUNT(*) FROM gen_metadata WHERE typeof(data) IN ('integer', 'real', 'text');")
            count = cursor.fetchone()[0]
            if count > 0:
                # Update with empty blob (X'') and size=0
                cursor.execute("UPDATE gen_metadata SET data = X'', size = 0 WHERE typeof(data) IN ('integer', 'real', 'text');")
                conn.commit()
                return True, count
        return True, 0
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()

def archive_conflict_files(conv_path, conflict_files, archive_dir):
    """Moves conflict/backup files out of active directory to archive folder."""
    moved_count = 0
    errors = []
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    for f in conflict_files:
        src = os.path.join(conv_path, f)
        dst = os.path.join(archive_dir, f)
        try:
            # If destination already exists, append timestamp
            if os.path.exists(dst):
                base, ext = os.path.splitext(f)
                dst = os.path.join(archive_dir, f"{base}_{int(time.time())}{ext}")
            shutil.move(src, dst)
            moved_count += 1
        except Exception as e:
            errors.append(f"{f}: {str(e)}")
            
    return moved_count, errors
