"""Deployment configuration checks for the Vercel runtime."""

import os

from django.http import JsonResponse


class RequireVercelConfigurationMiddleware:
    """Return a clear 503 when required production settings are missing.

    Do not raise during Django startup: Vercel imports the WSGI application
    during its build/collectstatic phase as well as at runtime. Checking here
    keeps builds possible while preventing production requests from silently
    using the local development secret or ephemeral SQLite database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_vercel = any(
            os.getenv(name)
            for name in ("VERCEL", "VERCEL_URL", "VERCEL_ENV")
        )
        if is_vercel:
            missing = [
                name
                for name in ("DJANGO_SECRET_KEY", "DATABASE_URL")
                if not os.getenv(name, "").strip()
            ]
            if missing:
                return JsonResponse(
                    {
                        "status": "configuration_error",
                        "message": (
                            "NgqoPerfumes is deployed, but required production "
                            "environment variables are missing."
                        ),
                        "missing_environment_variables": missing,
                    },
                    status=503,
                )

        return self.get_response(request)
