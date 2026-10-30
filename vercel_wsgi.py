"""Root WSGI shim for Vercel's native Django runtime."""

import sys
from pathlib import Path

DJANGO_PROJECT = Path(__file__).resolve().parent / "nqoperfumes" / "myshop"
if str(DJANGO_PROJECT) not in sys.path:
    sys.path.insert(0, str(DJANGO_PROJECT))

from myshop.wsgi import application  # noqa: E402

__all__ = ["application"]
