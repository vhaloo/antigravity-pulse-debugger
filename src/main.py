import os
import sys
from .utils import (
    print_header, print_success, print_warning, print_error, print_info,
    find_sqlite_exe, find_conversation_dirs, check_running_processes,
    BOLD, CYAN, YELLOW, RED, GREEN, RESET, WHITE
)
from .diagnostics import run_diagnostics
from .repair import repair_database, fix_stuck_steps, fix_protobuf_types, archive_conflict_files

BANNER = fr"""{BOLD}{CYAN}
   _         _   _                               _ _         
  /_\  _ __ | |_(_)__ _ _ _ __ ___ _ _ (_) |_ _  _ 
 / _ \| '  \|  _| / _` | '_/ _` \ V / | _| ' \ || |
/_/ \_\_|_|_|\__|_\__, |_| \__,_|\_/|_|\__|_||_\_, |
                  |___/                        |__/ 
               P U L S E   D E B U G G E R
{RESET}"""

def show_menu():
    print(f"\n{BOLD}{WHITE}Select an option:{RESET}")
    print(f"  {BOLD}{GREEN}1.{RESET} Scan and Show Diagnostics Report")
    print(f"  {BOLD}{GREEN}2.{RESET} Repair Malformed DBs, Cancel Zombified Steps, and Fix Protobufs")
    print(f"  {BOLD}{GREEN}3.{RESET} Archive Sync Conflicts and Orphans (*(1)* files)")
    print(f"  {BOLD}{GREEN}4.{RESET} Check Running Processes")
    print(f"  {BOLD}{GREEN}5.{RESET} Exit")
    try:
        val = input(f"\n{BOLD}Choose option [1-5]:{RESET} ").strip()
        return val
    except (KeyboardInterrupt, EOFError):
        return "5"

def run_scan(conv_dirs):
    print_info("Starting full system diagnostics scan...")
    reports = {}
    total_corrupted = 0
    total_stuck = 0
    total_protobuf = 0
    total_conflicts = 0
    
    for name, path in conv_dirs.items():
        print(f"\nScanning Profile: {BOLD}{WHITE}{name}{RESET}")
        print(f"Path: {path}")
        report = run_diagnostics(name, path)
        reports[name] = report
        
        # Display summary for this folder
        print(f"  - Databases scanned: {report['total_dbs']}")
        if report['corrupted_dbs']:
            print_error(f"Found {len(report['corrupted_dbs'])} corrupted database(s):")
            for db, err in report['corrupted_dbs']:
                print(f"    • {db}: {err}")
            total_corrupted += len(report['corrupted_dbs'])
        else:
            print_success("No database file corruptions detected.")
            
        if report['stuck_dbs']:
            print_warning(f"Found {len(report['stuck_dbs'])} database(s) with stuck steps:")
            for db, count in report['stuck_dbs'].items():
                print(f"    • {db}: {count} stuck steps")
            total_stuck += sum(report['stuck_dbs'].values())
        else:
            print_success("No zombified/stuck agent steps found.")
            
        if report['malformed_protobufs']:
            print_warning(f"Found {len(report['malformed_protobufs'])} database(s) with invalid types in metadata:")
            for db, count in report['malformed_protobufs'].items():
                print(f"    • {db}: {count} rows with corrupted protobuf values")
            total_protobuf += sum(report['malformed_protobufs'].values())
        else:
            print_success("No metadata type mismatches (protobuf errors) found.")
            
        if report['conflict_files']:
            print_warning(f"Found {len(report['conflict_files'])} orphaned or conflict files:")
            for f in report['conflict_files']:
                print(f"    • {f}")
            total_conflicts += len(report['conflict_files'])
        else:
            print_success("No conflict files found.")
            
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}Global Diagnostics Summary:{RESET}")
    if total_corrupted == 0 and total_stuck == 0 and total_protobuf == 0 and total_conflicts == 0:
        print_success("All Antigravity systems are 100% clean and healthy!")
    else:
        if total_corrupted > 0:
            print_error(f"Total Corrupted Databases: {total_corrupted}")
        if total_stuck > 0:
            print_warning(f"Total Stuck Steps: {total_stuck}")
        if total_protobuf > 0:
            print_warning(f"Total Corrupted Protobuf Fields: {total_protobuf}")
        if total_conflicts > 0:
            print_warning(f"Total Sync Conflict Files: {total_conflicts}")
            
    return reports

def run_repair(conv_dirs, sqlite_exe):
    # Verify sqlite3.exe before doing recovery
    if not sqlite_exe:
        print_error("sqlite3.exe was not found on the system path or DaVinci Resolve directory.")
        print_warning("Integrity repair requires sqlite3.exe. Only Stuck Steps and Protobufs will be fixed.")
        
    print_info("Initializing system-wide repair process...")
    
    # Check if app is running
    active_procs = check_running_processes()
    if active_procs:
        print_warning(f"Antigravity processes are currently running: {', '.join(active_procs)}")
        print_warning("To prevent file locks, please close all clients before continuing.")
        ans = input("Proceed anyway? (y/N): ").strip().lower()
        if ans != 'y':
            print_info("Repair aborted by user.")
            return

    for name, path in conv_dirs.items():
        print(f"\n{BOLD}Repairing Profile: {name}{RESET}")
        archive_dir = os.path.join(os.path.dirname(path), "archive_corrupted")
        
        # Run diagnostic check first to know what to fix
        report = run_diagnostics(name, path)
        
        # 1. Recover corrupted databases
        for db, err in report['corrupted_dbs']:
            db_path = os.path.join(path, db)
            print_info(f"Attempting SQLite recovery on {db}...")
            ok, msg = repair_database(db_path, sqlite_exe, archive_dir)
            if ok:
                print_success(f"Recovered {db}: {msg}")
            else:
                print_error(f"Failed to recover {db}: {msg}")
                
        # 2. Fix stuck steps (status 1, 2, 8 -> 5)
        # Note: we re-scan databases since some may have been successfully recovered
        db_files = [f for f in os.listdir(path) if f.endswith('.db')]
        stuck_fixed = 0
        for db in db_files:
            db_path = os.path.join(path, db)
            if os.path.getsize(db_path) == 0:
                continue
            ok, count = fix_stuck_steps(db_path)
            if ok and count > 0:
                stuck_fixed += count
                print_success(f"Cleared {count} stuck step(s) in {db}")
                
        # 3. Fix malformed protobufs in gen_metadata
        pb_fixed = 0
        for db in db_files:
            db_path = os.path.join(path, db)
            if os.path.getsize(db_path) == 0:
                continue
            ok, count = fix_protobuf_types(db_path)
            if ok and count > 0:
                pb_fixed += count
                print_success(f"Fixed {count} malformed protobuf row(s) in {db}")
                
        print_success(f"Profile {name} repair completed.")

def run_archive(conv_dirs):
    print_info("Starting cleanup of conflict and backup files...")
    for name, path in conv_dirs.items():
        report = run_diagnostics(name, path)
        if report['conflict_files']:
            archive_dir = os.path.join(os.path.dirname(path), "archive_corrupted")
            print_info(f"Archiving conflict files in {name} to: {archive_dir}")
            count, errs = archive_conflict_files(path, report['conflict_files'], archive_dir)
            print_success(f"Archived {count} conflict/temporary files.")
            if errs:
                print_error(f"Encountered {len(errs)} errors during archiving:")
                for err in errs:
                    print(f"  - {err}")
        else:
            print_success(f"No conflict files to archive in profile {name}.")

def main():
    print(BANNER)
    print_header("System Diagnostics & Database Integrity Tool")
    
    # 1. Locate sqlite3.exe
    sqlite_exe = find_sqlite_exe()
    if sqlite_exe:
        print_success(f"Found SQL Engine: {sqlite_exe}")
    else:
        print_warning("DaVinci Resolve or system sqlite3.exe not detected.")
        print_info("SQLite database repair will not be available. Stuck steps / Protobuf fixes will still work.")
        
    # 2. Locate conversation folders
    conv_dirs = find_conversation_dirs()
    if not conv_dirs:
        print_error("No active Antigravity conversation folders found in ~/.gemini/")
        print("Please ensure Antigravity has been launched at least once on this user account.")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    print_success(f"Identified {len(conv_dirs)} active profile(s): {', '.join(conv_dirs.keys())}")
    
    # 3. Warning if application is running
    active_procs = check_running_processes()
    if active_procs:
        print_warning(f"Active processes detected: {', '.join(active_procs)}")
        print_info("It is recommended to close Antigravity before running operations.")
        
    # Main loop
    while True:
        choice = show_menu()
        if choice == "1":
            run_scan(conv_dirs)
        elif choice == "2":
            run_repair(conv_dirs, sqlite_exe)
        elif choice == "3":
            run_archive(conv_dirs)
        elif choice == "4":
            procs = check_running_processes()
            if procs:
                print_warning(f"Active processes: {', '.join(procs)}")
            else:
                print_success("No active Antigravity processes running.")
        elif choice == "5":
            print_info("Exiting Antigravity Pulse Debugger. Good day!")
            break
        else:
            print_error("Invalid option. Please choose between 1 and 5.")

if __name__ == "__main__":
    main()
