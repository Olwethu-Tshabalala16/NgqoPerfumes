"""Publish the admin-managed product catalogue as a durable JSON object in Supabase Storage."""

import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db.models import Count, Max
from django.utils import timezone

from .models import Product
from .storage import SupabaseS3Storage

CATALOGUE_OBJECT_KEY = "catalogue/products.json"


def get_catalogue_revision():
    """Return the database revision shared by the API and published snapshot."""
    summary = Product.objects.aggregate(
        count=Count("pk"),
        latest_updated_at=Max("updated_at"),
        latest_id=Max("pk"),
    )
    latest_updated_at = summary["latest_updated_at"]
    return ":".join(
        (
            str(summary["count"]),
            str(summary["latest_id"] or 0),
            latest_updated_at.isoformat() if latest_updated_at else "empty",
        )
    )


def build_catalogue():
    """Build a snapshot whose revision matches the products included in it."""
    for _attempt in range(3):
        revision_before = get_catalogue_revision()
        products = list(Product.objects.all().order_by("-created_at", "-pk"))
        results = []

        for product in products:
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

        revision_after = get_catalogue_revision()
        if revision_before == revision_after:
            return {
                "version": 1,
                "revision": revision_after,
                "updated_at": timezone.now().isoformat(),
                "count": len(results),
                "products": results,
            }

    raise RuntimeError("The product catalogue changed repeatedly while a snapshot was being built.")


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
    storage = SupabaseS3Storage(file_overwrite=True)
    storage.object_parameters = {
        "CacheControl": "no-store, no-cache, max-age=0, must-revalidate",
        "ContentType": "application/json",
    }
    storage.save(CATALOGUE_OBJECT_KEY, ContentFile(payload))
    return storage.url(CATALOGUE_OBJECT_KEY)
