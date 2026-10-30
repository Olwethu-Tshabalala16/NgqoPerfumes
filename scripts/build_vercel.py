"""Build the Vercel static frontend and collect Django admin assets.

This build deliberately does not require production database credentials:
Vercel build environments can be configured separately from runtime
environments, and collectstatic does not need a live database.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "nqoperfumes" / "myshop"
FRONTEND = ROOT / "frontend"
FRONTEND_CONFIG = FRONTEND / "config.js"
STATIC_SOURCE = BACKEND / "staticfiles"
STATIC_OUTPUT = FRONTEND / "static"


def main():
    if not (FRONTEND / "index.html").is_file():
        raise SystemExit(
            "Vercel build failed: frontend/index.html is missing. "
            "Check the repository root and frontend output directory."
        )

    supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images").strip()
    bucket = bucket or "product-images"

    catalogue_url = ""
    if supabase_url:
        catalogue_url = (
            f"{supabase_url}/storage/v1/object/public/"
            f"{bucket}/catalogue/products.json"
        )

    # Same-origin API rewrites are used in production. Local development keeps
    # its explicit localhost backend URL.
    config = {
        "CATALOGUE_JSON_URL": catalogue_url,
        "API_BASE_URL": "" if os.getenv("VERCEL") else "http://127.0.0.1:8000",
    }
    FRONTEND_CONFIG.write_text(
        "/* Generated during deployment by scripts/build_vercel.py. */\n"
        "window.NQO_CONFIG = "
        + json.dumps(config, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )

    # Mark this process as a build so Django settings do not demand runtime
    # secrets or a production database merely to run collectstatic.
    build_env = os.environ.copy()
    build_env["NQO_BUILD"] = "1"

    subprocess.run(
        [
            sys.executable,
            "manage.py",
            "collectstatic",
            "--noinput",
            "--clear",
        ],
        cwd=BACKEND,
        env=build_env,
        check=True,
    )

    if not STATIC_SOURCE.is_dir():
        raise SystemExit(
            "Vercel build failed: Django did not create the staticfiles directory."
        )

    # Vercel's output directory is frontend/, so Django Admin assets must be
    # copied there rather than left inside the backend project.
    if STATIC_OUTPUT.exists():
        shutil.rmtree(STATIC_OUTPUT)
    shutil.copytree(STATIC_SOURCE, STATIC_OUTPUT)

    print("NqoPerfumes Vercel build completed.")
    print(f"Static frontend output: {FRONTEND}")
    print(f"Django static assets copied: {STATIC_OUTPUT}")


if __name__ == "__main__":
    main()
