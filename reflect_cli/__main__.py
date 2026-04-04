"""Allow running as: python -m reflect_cli"""

import sys
from reflect_cli.cli import main

sys.exit(main() or 0)
