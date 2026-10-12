"""Publish the admin-managed product catalogue as a durable JSON object in Supabase Storage."""

import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Product
from .storage import SupabaseS3Storage

CATALOGUE_OBJECT_KEY = "catalogue/products.json"


def build_catalogue():
    """Build a portable JSON snapshot of all products and their public image URLs."""
    results = []
    for product in Product.objects.all().order_by("-created_at", "-pk"):
        image_url = product.image.url if product.image else None
        results.append(
            {
                "id": product.pk,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "stock": product.stock,
                "is_in_stock": product.is_in_stock(),
                "image_url": image_url,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
            }
        )

    return {
        "version": 1,
        "updated_at": timezone.now().isoformat(),
        "count": len(results),
        "products": results,
    }


def publish_catalogue():
    """Overwrite the single persistent JSON catalogue object in Supabase Storage."""
    required_settings = (
        settings.SUPABASE_URL,
        settings.SUPABASE_STORAGE_ENDPOINT,
        settings.SUPABASE_STORAGE_ACCESS_KEY_ID,
        settings.SUPABASE_STORAGE_SECRET_ACCESS_KEY,
    )
    if not all(required_settings):
        raise ImproperlyConfigured(
            "Supabase Storage is not configured. Set SUPABASE_URL, "
            "SUPABASE_STORAGE_ENDPOINT, SUPABASE_STORAGE_ACCESS_KEY_ID, "
            "and SUPABASE_STORAGE_SECRET_ACCESS_KEY before publishing the catalogue."
        )

    payload = json.dumps(build_catalogue(), ensure_ascii=False, indent=2).encode("utf-8")
    # Override only for this fixed object key; product images retain unique filenames.
    storage = SupabaseS3Storage(file_overwrite=True)
    storage.save(CATALOGUE_OBJECT_KEY, ContentFile(payload))
    return storage.url(CATALOGUE_OBJECT_KEY)
