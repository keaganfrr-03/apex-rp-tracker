"""Where the app keeps its files (database + backups)."""
import os
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("APEX_RP_DATA_DIR")
    if override:
        p = Path(override)
    elif os.name == "nt":
        p = Path(os.environ.get("APPDATA", str(Path.home()))) / "ApexRPTracker"
    else:
        p = Path.home() / ".apex_rp_tracker"
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return data_dir() / "apex_rp.db"


def backup_dir() -> Path:
    p = data_dir() / "backups"
    p.mkdir(parents=True, exist_ok=True)
    return p
