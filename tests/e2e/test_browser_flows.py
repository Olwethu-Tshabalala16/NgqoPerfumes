import re
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright

from store.catalogue import build_catalogue
from store.models import Product


class StorefrontBrowserTests(StaticLiveServerTestCase):
    """Exercise the real storefront and Django admin in an isolated test DB."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(headless=True)
        except Exception:
            cls.playwright.stop()
            super().tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
        finally:
            cls.playwright.stop()
            super().tearDownClass()

    def setUp(self):
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()

    def test_storefront_falls_back_after_publish_failure_and_recovers(self):
        product = Product.objects.create(
            name="Amber Oud",
            description="A warm woody fragrance.",
            price=Decimal("249.99"),
            stock=3,
            image="products/missing-image.jpg",
        )
        publication = {"available": False, "payload": None}

        def serve_frontend_config(route):
            route.fulfill(
                status=200,
                content_type="application/javascript",
                body=(
                    "window.NGQO_CONFIG = {"
                    " CATALOGUE_JSON_URL: '/__tests__/catalogue.json',"
                    " API_BASE_URL: ''"
                    "};"
                ),
            )

        def serve_published_catalogue(route):
            if not publication["available"]:
                route.fulfill(
                    status=503,
                    content_type="application/json",
                    body='{"detail":"temporary storage outage"}',
                )
                return

            route.fulfill(status=200, json=publication["payload"])

        self.page.route("**/static/config.js", serve_frontend_config)
        self.page.route("**/__tests__/catalogue.json*", serve_published_catalogue)
        self.page.route(
            "**/products/missing-image.jpg",
            lambda route: route.fulfill(status=404),
        )

        self.page.goto(f"{self.live_server_url}/")

        card = self.page.locator(f'.product-card[data-product-id="{product.pk}"]')
        expect(card).to_be_visible()
        expect(card.locator(".image-placeholder")).to_be_visible(timeout=10_000)
        expect(card.locator("img.product-photo")).to_have_count(0)

        search = self.page.locator("#product-search")
        search.fill("not in the catalogue")
        expect(self.page.locator(".empty-state")).to_contain_text("No matching fragrances")
        search.fill("amber")
        expect(card).to_be_visible()

        # A later database revision and successful publication must replace
        # the API fallback without requiring a page reload.
        product.stock = 0
        product.description = "Updated after the storage outage."
        product.save()
        publication["payload"] = build_catalogue()
        publication["available"] = True

        self.page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")

        expect(card.locator(".product-description")).to_have_text(
            "Updated after the storage outage.",
            timeout=10_000,
        )
        expect(card.locator(".stock-status")).to_have_text("Out of stock")

    def test_admin_login_password_toggle_and_authentication(self):
        password = "browser-test-password-123"
        get_user_model().objects.create_superuser(
            username="browser-admin",
            email="browser-admin@example.test",
            password=password,
        )

        self.page.goto(f"{self.live_server_url}/admin/login/")

        password_input = self.page.locator("#id_password")
        toggle = self.page.get_by_role("button", name="Show password")
        expect(toggle).to_be_visible()

        password_input.fill(password)
        toggle.click()
        expect(password_input).to_have_attribute("type", "text")
        expect(self.page.get_by_role("button", name="Hide password")).to_be_visible()

        self.page.get_by_role("button", name="Hide password").click()
        expect(password_input).to_have_attribute("type", "password")

        self.page.locator("#id_username").fill("browser-admin")
        self.page.locator('input[type="submit"]').click()

        self.page.wait_for_url(re.compile(r".*/admin/$"))
        expect(self.page.locator(".nqo-brand-name")).to_contain_text("Ngqo Perfumes")
