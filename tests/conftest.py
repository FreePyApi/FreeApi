import os
import sys
from pathlib import Path


os.environ.setdefault("ENV", "development")
os.environ.setdefault("FREEAPI_CURRENT_VERSION", "1.0.0")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))
