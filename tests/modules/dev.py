from pathlib import Path
import sys

# Allow direct execution of this file from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

# Avoid shadowing the stdlib `dev` module with this file name.
sys.path = [path for path in sys.path if Path(path).resolve() != SCRIPT_DIR]

import src.modules.dev as mdev

print(mdev.test_regex(r'\b\w+\b', 'This is a test string.'))
print(mdev.generate_regex('This is a test string.'))

import re
pattern = re.compile(r"2020-03-12T13:34:56\.123Z INFO  \[org\.example\.Class\]: This is a #simple #logline containing a 'value'\.", re.IGNORECASE)
print(pattern.match("This is a test string."))