from pathlib import Path
import sys

# Allow direct execution of this file from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

# Avoid shadowing the stdlib `random` module with this file name.
sys.path = [path for path in sys.path if Path(path).resolve() != SCRIPT_DIR]

import src.modules.random as mrandom

print(mrandom.random_gradient())