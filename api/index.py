"""Vercel Python Function entry point for the Django application."""

import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DJANGO_PROJECT = REPOSITORY_ROOT / "nqoperfumes" / "myshop"
sys.path.insert(0, str(DJANGO_PROJECT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings")

from myshop.wsgi import application  # noqa: E402

# Vercel discovers the WSGI callable named app.
app = application
