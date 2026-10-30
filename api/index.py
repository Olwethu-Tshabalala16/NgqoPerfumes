"""Vercel Python Function entry point for the Django application."""

import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DJANGO_PROJECT = REPOSITORY_ROOT / "nqoperfumes" / "myshop"
sys.path.insert(0, str(DJANGO_PROJECT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings")

# Fail at function startup with a direct configuration message instead of
# allowing a misleading generic 500 when production secrets are absent.
if os.getenv("VERCEL"):
    missing = [
        name
        for name in ("DJANGO_SECRET_KEY", "DATABASE_URL")
        if not os.getenv(name, "").strip()
    ]
    if missing:
        raise RuntimeError(
            "NqoPerfumes is not configured for production. Add these Vercel "
            "Environment Variables and redeploy: " + ", ".join(missing)
        )

from myshop.wsgi import application  # noqa: E402

# Vercel discovers the WSGI callable named app.
app = application
