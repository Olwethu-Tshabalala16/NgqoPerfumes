import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone
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

    def test_catalogue_version_changes_when_products_change(self):
        url = reverse("store:product_catalogue_version_api")
        first_response = self.client.get(url)

        self.assertEqual(first_response.status_code, 200)
        self.assertIn("no-store", first_response["Cache-Control"])
        first_version = first_response.json()["version"]

        Product.objects.create(
            name="Rose Musk",
            price=Decimal("199.00"),
            stock=2,
        )
        created_version = self.client.get(url).json()["version"]
        self.assertNotEqual(first_version, created_version)

        Product.objects.filter(pk=self.product.pk).update(
            updated_at=timezone.now() + timedelta(seconds=2)
        )
        updated_version = self.client.get(url).json()["version"]
        self.assertNotEqual(created_version, updated_version)

        self.product.delete()
        deleted_version = self.client.get(url).json()["version"]
        self.assertNotEqual(updated_version, deleted_version)

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
        self.assertEqual(
            payload["revision"],
            self.client.get(reverse("store:product_catalogue_version_api")).json()["version"],
        )
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
    def test_publish_writes_json_to_fixed_supabase_object_key_without_stale_cache(self):
        from .catalogue import CATALOGUE_OBJECT_KEY, publish_catalogue

        with patch("store.catalogue.SupabaseS3Storage") as storage_class:
            storage = storage_class.return_value
            storage.url.return_value = "https://example.supabase.co/catalogue/products.json"

            result = publish_catalogue()

        storage_class.assert_called_once_with(file_overwrite=True)
        storage.save.assert_called_once()
        self.assertEqual(
            storage.object_parameters,
            {
                "CacheControl": "no-store, no-cache, max-age=0, must-revalidate",
                "ContentType": "application/json",
            },
        )
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


class ProductImageCleanupTests(TestCase):
    def test_deleting_product_removes_its_unreferenced_image(self):
        product = Product.objects.create(
            name="Image to remove",
            price=Decimal("100.00"),
            image="products/orphan.jpg",
        )
        image_storage = Product._meta.get_field("image").storage

        with patch.object(image_storage, "delete") as delete_image:
            with self.captureOnCommitCallbacks(execute=True):
                product.delete()

        delete_image.assert_called_once_with("products/orphan.jpg")

    def test_shared_image_is_removed_only_after_last_product_is_deleted(self):
        first = Product.objects.create(
            name="First product",
            price=Decimal("100.00"),
            image="products/shared.jpg",
        )
        second = Product.objects.create(
            name="Second product",
            price=Decimal("120.00"),
            image="products/shared.jpg",
        )
        image_storage = Product._meta.get_field("image").storage

        with patch.object(image_storage, "delete") as delete_image:
            with self.captureOnCommitCallbacks(execute=True):
                first.delete()
                delete_image.assert_not_called()
                second.delete()

        delete_image.assert_called_once_with("products/shared.jpg")

    def test_replacing_product_image_removes_old_unreferenced_image_after_commit(self):
        product = Product.objects.create(
            name="Image replacement",
            price=Decimal("100.00"),
            image="products/old.jpg",
        )
        image_storage = Product._meta.get_field("image").storage

        with patch.object(image_storage, "delete") as delete_image:
            with self.captureOnCommitCallbacks(execute=True):
                product.image = "products/new.jpg"
                product.save()

        delete_image.assert_called_once_with("products/old.jpg")

    def test_replacing_image_keeps_old_image_when_another_product_references_it(self):
        first = Product.objects.create(
            name="First product",
            price=Decimal("100.00"),
            image="products/shared-old.jpg",
        )
        Product.objects.create(
            name="Second product",
            price=Decimal("120.00"),
            image="products/shared-old.jpg",
        )
        image_storage = Product._meta.get_field("image").storage

        with patch.object(image_storage, "delete") as delete_image:
            with self.captureOnCommitCallbacks(execute=True):
                first.image = "products/replacement.jpg"
                first.save()

        delete_image.assert_not_called()

    def test_saving_without_changing_image_does_not_delete_it(self):
        product = Product.objects.create(
            name="Unchanged image",
            price=Decimal("100.00"),
            image="products/keep.jpg",
        )
        image_storage = Product._meta.get_field("image").storage

        with patch.object(image_storage, "delete") as delete_image:
            with self.captureOnCommitCallbacks(execute=True):
                product.name = "Updated name"
                product.save()

        delete_image.assert_not_called()


class SupabaseStorageTests(TestCase):
    def test_product_upload_names_are_unique_without_checking_remote_object(self):
        from .storage import SupabaseS3Storage

        storage = SupabaseS3Storage(file_overwrite=False)
        with patch.object(storage, "exists") as exists:
            first_name = storage.get_available_name("products/amber.jpg")
            second_name = storage.get_available_name("products/amber.jpg")

        self.assertTrue(first_name.startswith("products/"))
        self.assertTrue(first_name.endswith("_amber.jpg"))
        self.assertNotEqual(first_name, second_name)
        exists.assert_not_called()

    def test_overwrite_storage_keeps_fixed_catalogue_object_name(self):
        from .storage import SupabaseS3Storage

        storage = SupabaseS3Storage(file_overwrite=True)

        self.assertEqual(
            storage.get_available_name("catalogue/products.json"),
            "catalogue/products.json",
        )


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
        self.assertContains(response, "Ngqo Perfumes")
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
