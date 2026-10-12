import json
from decimal import Decimal
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product


class ProductApiTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Amber Oud",
            description="A warm woody fragrance.",
            price=Decimal("249.99"),
            stock=4,
        )

    def test_product_list_returns_public_product_data(self):
        response = self.client.get(reverse("store:product_list_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0],
            {
                "id": self.product.pk,
                "name": "Amber Oud",
                "description": "A warm woody fragrance.",
                "price": "249.99",
                "stock": 4,
                "is_in_stock": True,
                "image_url": None,
            },
        )

    def test_product_list_is_read_only(self):
        response = self.client.post(reverse("store:product_list_api"), data={})
        self.assertEqual(response.status_code, 405)

    def test_health_check_reports_ok(self):
        response = self.client.get(reverse("store:health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_empty_catalogue_returns_empty_results(self):
        Product.objects.all().delete()
        response = self.client.get(reverse("store:product_list_api"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "results": []})


class CataloguePublishingTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Amber Oud",
            description="A warm woody fragrance.",
            price=Decimal("249.99"),
            stock=4,
        )

    def test_catalogue_snapshot_contains_product_details_and_image_reference(self):
        from .catalogue import build_catalogue

        payload = build_catalogue()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(len(payload["products"]), 1)
        self.assertEqual(
            payload["products"][0],
            {
                "id": self.product.pk,
                "name": "Amber Oud",
                "description": "A warm woody fragrance.",
                "price": "249.99",
                "stock": 4,
                "is_in_stock": True,
                "image_url": None,
                "created_at": self.product.created_at.isoformat(),
                "updated_at": self.product.updated_at.isoformat(),
            },
        )

    @override_settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_STORAGE_ENDPOINT="https://example.storage.supabase.co/storage/v1/s3",
        SUPABASE_STORAGE_ACCESS_KEY_ID="test-access-key",
        SUPABASE_STORAGE_SECRET_ACCESS_KEY="test-secret-key",
    )
    def test_publish_writes_json_to_fixed_supabase_object_key(self):
        from .catalogue import CATALOGUE_OBJECT_KEY, publish_catalogue

        with patch("store.catalogue.SupabaseS3Storage") as storage_class:
            storage = storage_class.return_value
            storage.url.return_value = "https://example.supabase.co/catalogue/products.json"

            result = publish_catalogue()

        storage_class.assert_called_once_with(file_overwrite=True)
        storage.save.assert_called_once()
        key, content_file = storage.save.call_args.args
        self.assertEqual(key, CATALOGUE_OBJECT_KEY)
        self.assertIsInstance(content_file, ContentFile)
        saved_json = json.loads(content_file.read().decode("utf-8"))
        self.assertEqual(saved_json["count"], 1)
        self.assertEqual(saved_json["products"][0]["name"], "Amber Oud")
        self.assertEqual(result, "https://example.supabase.co/catalogue/products.json")

    @override_settings(
        SUPABASE_URL="",
        SUPABASE_STORAGE_ENDPOINT="",
        SUPABASE_STORAGE_ACCESS_KEY_ID="",
        SUPABASE_STORAGE_SECRET_ACCESS_KEY="",
    )
    def test_publish_fails_clearly_when_supabase_storage_is_not_configured(self):
        from django.core.exceptions import ImproperlyConfigured
        from .catalogue import publish_catalogue

        with self.assertRaises(ImproperlyConfigured):
            publish_catalogue()
