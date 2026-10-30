#!/usr/bin/env python
"""Root Django entrypoint used by Vercel's native Django detection."""

import os
import sys
from pathlib import Path

DJANGO_PROJECT = Path(__file__).resolve().parent / "nqoperfumes" / "myshop"
if str(DJANGO_PROJECT) not in sys.path:
    sys.path.insert(0, str(DJANGO_PROJECT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
