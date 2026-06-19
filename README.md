# Antigravity Pulse Debugger

An all-in-one terminal diagnostics, SQLite recovery, and agent state repair tool built specifically for Antigravity platforms on Windows. 

This utility detects database corruption, clears zombified background tasks, fixes protobuf format mismatches, and keeps your conversations directory optimized and conflict-free.

---

## Features

1. **Automatic SQLite Recovery**: Scans database files and automatically repairs malformed databases (`database disk image is malformed`, btree page offsets, rowid out-of-order) using a safe pipeline wrapping SQLite's `.recover` utility.
2. **Zombie Agent Cancellation**: Clears infinite spinner loading screens in both CLI and Desktop interfaces by updating orphaned steps stuck in running or waiting states (`1`, `2`, `8`) to a terminal state (`5` / `CANCELED`).
3. **Protobuf Type Mismatch Patches**: Detects corrupted columns in the `gen_metadata` tables (e.g. numeric types written in blob columns) and updates them to correct empty BLOB fields, preventing language server startup panics.
4. **Sync Conflict Archiving**: Automatically sweeps duplicate sync files (like `*(1).db-wal`), temporary SQLite states, and backup databases, moving them to a dedicated `archive_corrupted/` directory to prevent file locking and performance degradation.
5. **No Installation (Zero Dependencies)**: Written purely using Python's standard libraries. Features built-in console color rendering via native Windows Virtual Terminal Processing.

---

## Prerequisites

- **Python 3.8+** (must be added to your system environment variable `PATH`).
- **SQLite Engine**: The database recovery functionality relies on `sqlite3.exe`. The tool will automatically locate your DaVinci Resolve copy of `sqlite3.exe` (installed at `C:\Program Files\Blackmagic Design\DaVinci Resolve\sqlite3.exe`) or any copy on your system `PATH`.

---

## Usage

### 1. The Quick Launch (Easiest)
Simply double-click **`run_debugger.bat`** in the repository root. This will launch a colored terminal interface.

### 2. Manual CLI execution
Navigate to the root directory in Command Prompt or PowerShell and execute:
```bash
python -m src.main
```

---

## Technical Details

The tool works dynamically by scanning your local environment for Antigravity profile installations. It locates conversation databases by scanning all directories within `%USERPROFILE%\.gemini` containing a `conversations/` subdirectory (such as `.gemini\antigravity`, `.gemini\antigravity-cli`, and `.gemini\antigravity-ide`).

### SQLite Recover Pipeline
The utility repairs corruptions by copying the malformed file to a temporary area and running:
```powershell
"sqlite3.exe" "corrupted.db" ".recover" | "sqlite3.exe" "repaired.db"
```
It then verifies integrity using `PRAGMA integrity_check;` before safely swapping the active file with the repaired one.

### Stuck Steps Update
Active states (`1` / `PENDING`, `2` / `RUNNING`, `8` / `WAITING`) are updated inside the `steps` table:
```sql
UPDATE steps SET status = 5 WHERE status IN (1, 2, 8);
```

### Protobuf Reset
Malformed integer values in metadata fields are corrected:
```sql
UPDATE gen_metadata SET data = X'', size = 0 WHERE typeof(data) IN ('integer', 'real', 'text');
```

---

## License
MIT License. Created by Valentin Wittwe.
