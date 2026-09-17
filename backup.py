#!/usr/bin/env python3
"""Auto backup PostgreSQL -> local + optional S3 via rclone."""
import os, subprocess, datetime, pathlib

DB_URL = os.getenv("DATABASE_URL", "")
BACKUP_DIR = pathlib.Path(os.getenv("BACKUP_DIR", "./backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def backup():
    today = datetime.date.today().isoformat()
    out = BACKUP_DIR / f"backup_{today}.sql"
    # Parse DB_URL for pg_dump
    # Fallback: use pg_dump with DATABASE_URL env
    if "postgresql" in DB_URL:
        # Use pg_dump via subprocess with URI
        cmd = ["pg_dump", DB_URL.replace("postgresql+asyncpg://", "postgresql://"), "-f", str(out)]
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Backup saved {out} ({out.stat().st_size/1024:.1f} KB)")
            # Keep 7 days
            for p in sorted(BACKUP_DIR.glob("backup_*.sql"))[:-7]:
                p.unlink()
                print(f"🗑️ Removed old {p}")
            # Optional rclone: rclone copy ./backups remote:backups
            if os.getenv("RCLONE_REMOTE"):
                subprocess.run(["rclone", "copy", str(BACKUP_DIR), os.getenv("RCLONE_REMOTE")], check=False)
        except Exception as e:
            print(f"❌ Backup failed {e}")
    else:
        # SQLite backup: copy file
        src = DB_URL.replace("sqlite+aiosqlite:///", "").strip() or "./bot.db"
        if os.path.exists(src):
            import shutil
            shutil.copy(src, out.with_suffix(".db"))
            print(f"✅ SQLite copied {out}")

if __name__ == "__main__":
    backup()
