"""Build the Vercel static frontend and collect Django admin assets."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "nqoperfumes" / "myshop"
FRONTEND_CONFIG = ROOT / "frontend" / "config.js"

supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip() or "product-images"
catalogue_url = (
    f"{supabase_url}/storage/v1/object/public/{bucket}/catalogue/products.json"
    if supabase_url
    else ""
)

# Production uses same-origin Vercel rewrites. Local development uses runserver.
api_base_url = "" if os.getenv("VERCEL") else "http://127.0.0.1:8000"
FRONTEND_CONFIG.write_text(
    "/* Generated during deployment by scripts/build_vercel.py. */\n"
    "window.NQO_CONFIG = {\n"
    f"  CATALOGUE_JSON_URL: {catalogue_url!r},\n"
    f"  API_BASE_URL: {api_base_url!r}\n"
    "};\n",
    encoding="utf-8",
)

subprocess.run(
    [sys.executable, "manage.py", "collectstatic", "--noinput"],
    cwd=BACKEND,
    check=True,
)

# Vercel serves files from the configured output directory, not Django's
# STATIC_ROOT. Copy collected admin assets into the frontend output so that
# /static/admin/... URLs work without invoking a Python function for each asset.
STATIC_OUTPUT = ROOT / "frontend" / "static"
if STATIC_OUTPUT.exists():
    shutil.rmtree(STATIC_OUTPUT)
shutil.copytree(BACKEND / "staticfiles", STATIC_OUTPUT)
