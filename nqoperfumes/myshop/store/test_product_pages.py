from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class PublicProductPageTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Arthur Ford")
        self.product = Product.objects.create(
            name="Amber Oud",
            category=category,
            description="A warm woody fragrance.",
            price=Decimal("249.99"),
            stock=4,
        )
        self.product_url = reverse(
            "product_detail",
            kwargs={"pk": self.product.pk, "slug": "amber-oud"},
        )

    def test_homepage_contains_product_details_in_initial_html(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amber Oud")
        self.assertContains(response, "A warm woody fragrance.")
        self.assertContains(response, self.product_url)
        self.assertContains(response, 'id="initial-catalogue-data"')
        self.assertIn("s-maxage=60", response["Cache-Control"])

    def test_product_has_its_own_addressable_detail_page(self):
        response = self.client.get(self.product_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amber Oud")
        self.assertContains(response, "Arthur Ford")
        self.assertContains(response, "A warm woody fragrance.")
        self.assertContains(response, "R 249.99")

    def test_product_page_uses_public_cache_headers(self):
        response = self.client.get(self.product_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("s-maxage=60", response["Cache-Control"])

    def test_homepage_is_not_shared_cached_when_theme_cookie_is_present(self):
        response = self.client.get(reverse("home"), HTTP_COOKIE="theme=dark")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
