import os
from urllib.parse import quote

from django.conf import settings
from django.utils.crypto import get_random_string
from storages.backends.s3 import S3Storage
from storages.utils import clean_name, get_available_overwrite_name


class SupabaseS3Storage(S3Storage):
    """Django storage backend for Supabase Storage's S3-compatible API."""

    def get_available_name(self, name, max_length=None):
        name = clean_name(name)
        if self.file_overwrite:
            return super().get_available_name(name, max_length)

        directory, filename = os.path.split(name)
        file_root, file_ext = os.path.splitext(filename)
        unique_filename = f"{get_random_string(16)}_{file_root}{file_ext}"
        unique_name = os.path.join(directory, unique_filename)
        return get_available_overwrite_name(unique_name, max_length)

    def url(self, name, parameters=None, expire=None, http_method=None):
        if not name:
            return ""

        base_url = settings.SUPABASE_PUBLIC_STORAGE_URL.rstrip("/")
        return f"{base_url}/{quote(name, safe='/')}"
