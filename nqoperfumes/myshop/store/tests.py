import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
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



class AdminDashboardTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="nqo-admin",
            email="admin@example.com",
            password="test-only-password-123",
        )
        self.client.force_login(self.admin_user)

    def test_admin_dashboard_renders(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nqo Perfumes")
        self.assertContains(response, 'data-theme-toggle')
        self.assertRegex(response.content.decode(), r"/static/theme(?:\.[a-zA-Z0-9]+)?\.js")


class VercelDeploymentTests(TestCase):
    def test_homepage_serves_catalogue_html(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ngqo Perfumes")
        self.assertContains(response, "/static/styles.css")
        self.assertContains(response, 'data-theme-toggle')
        self.assertContains(response, '/static/theme.js')

    def test_theme_cookie_selects_theme_for_first_page_render(self):
        self.client.cookies["theme"] = "dark"

        response = self.client.get("/")

        self.assertContains(response, '<html lang="en" data-theme="dark">', html=False)

    def test_locked_owner_theme_overrides_visitor_choice(self):
        import os

        with patch.dict(
            os.environ,
            {"SITE_THEME": "dark", "SITE_THEME_LOCK": "1"},
        ):
            self.client.cookies["theme"] = "light"
            response = self.client.get("/")

        self.assertContains(response, 'data-theme="dark"', html=False)
        self.assertContains(response, 'data-theme-locked="true" disabled', html=False)

    def test_vercel_reports_missing_runtime_configuration_as_503(self):
        import os

        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "VERCEL": "1",
                "DJANGO_SECRET_KEY": "",
                "DATABASE_URL": "",
            },
        ):
            response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["missing_environment_variables"],
            ["DJANGO_SECRET_KEY", "DATABASE_URL"],
        )

    def test_vercel_request_passes_when_required_configuration_exists(self):
        import os

        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "VERCEL": "1",
                "DJANGO_SECRET_KEY": "test-secret-key",
                "DATABASE_URL": (
                    "postgresql://test:test@localhost:5432/testdb"
                ),
            },
        ):
            response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
    def test_wsgi_configuration_uses_importable_repository_root_shim(self):
        from django.conf import settings
        import vercel_wsgi

        self.assertEqual(settings.WSGI_APPLICATION, "vercel_wsgi.application")
        self.assertTrue(callable(vercel_wsgi.application))
