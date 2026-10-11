from decimal import Decimal

from django.test import TestCase
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
