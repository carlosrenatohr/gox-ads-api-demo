from pathlib import Path
import os

# Access to the root of the project
ROOT = Path(__file__).resolve().parents[2]

def get_env(name: str, *, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise ValueError(f"Missing environment variable: {name}")
    return value

def resolve_from_root(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs).expanduser()
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()
