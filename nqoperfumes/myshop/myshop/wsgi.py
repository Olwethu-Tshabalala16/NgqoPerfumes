"""
WSGI config for myshop project.

Vercel's native Django runtime loads this callable directly. Add the Django
project directory to Python's import path because manage.py lives one level
above the myshop package inside nqoperfumes/myshop/.
"""

import os
import sys
from pathlib import Path

DJANGO_PROJECT = Path(__file__).resolve().parent.parent
if str(DJANGO_PROJECT) not in sys.path:
    sys.path.insert(0, str(DJANGO_PROJECT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
