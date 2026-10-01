from urllib.parse import quote

from django.conf import settings
from storages.backends.s3 import S3Storage


class SupabaseS3Storage(S3Storage):
    """Django storage backend for Supabase Storage's S3-compatible API."""

    def url(self, name, parameters=None, expire=None, http_method=None):
        if not name:
            return ""

        base_url = settings.SUPABASE_PUBLIC_STORAGE_URL.rstrip("/")
        return f"{base_url}/{quote(name, safe='/')}"
