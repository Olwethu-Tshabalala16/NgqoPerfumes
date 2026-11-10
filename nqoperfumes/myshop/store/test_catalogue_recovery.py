from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from .models import Product


class CataloguePublishingRecoveryTests(TestCase):
    @override_settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_STORAGE_ENDPOINT="https://example.storage.supabase.co/storage/v1/s3",
        SUPABASE_STORAGE_ACCESS_KEY_ID="test-access-key",
        SUPABASE_STORAGE_SECRET_ACCESS_KEY="test-secret-key",
    )
    def test_failed_publish_does_not_return_a_url_and_a_later_retry_recovers(self):
        from .catalogue import publish_catalogue

        Product.objects.create(
            name="Recovery Fragrance",
            description="A product used by the publication retry test.",
            price=Decimal("199.00"),
            stock=2,
        )

        with patch("store.catalogue.SupabaseS3Storage") as storage_class:
            storage = storage_class.return_value
            storage.url.return_value = (
                "https://example.supabase.co/catalogue/products.json"
            )
            storage.save.side_effect = [
                OSError("Supabase Storage is temporarily unavailable"),
                "catalogue/products.json",
            ]

            with self.assertRaisesRegex(OSError, "temporarily unavailable"):
                publish_catalogue()

            recovered_url = publish_catalogue()

        self.assertEqual(
            recovered_url,
            "https://example.supabase.co/catalogue/products.json",
        )
        self.assertEqual(storage.save.call_count, 2)
        self.assertEqual(storage.url.call_count, 1)
