from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
# PyInstaller keeps bundled resources separate; writable records live next to executable.
DATA_DIR = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else ROOT) / "data"
LOW_STOCK_DEFAULT = 5.0
EXPIRY_WARNING_DAYS = 7
