import re
import threading
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import expect, sync_playwright

from store.catalogue import build_catalogue
from store.models import Product


@override_settings(
    STORAGES={
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class StorefrontBrowserTests(StaticLiveServerTestCase):
    """Exercise the storefront and Django admin in an isolated test database."""

    def run_browser_action(self, action):
        """Run Playwright in its own thread so Django's ORM stays synchronous."""
        result = {"error": None}

        def browser_worker():
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    try:
                        action(browser.new_page())
                    finally:
                        browser.close()
            except BaseException as error:
                result["error"] = error

        thread = threading.Thread(target=browser_worker, daemon=True)
        thread.start()
        return thread, result

    def finish_browser_action(self, thread, result, timeout=45):
        thread.join(timeout=timeout)
        self.assertFalse(thread.is_alive(), "The Playwright browser flow timed out.")
        if result["error"] is not None:
            raise result["error"]

    def test_storefront_falls_back_after_publish_failure_and_recovers(self):
        product = Product.objects.create(
            name="Amber Oud",
            description="A warm woody scent.",
            price=Decimal("249.99"),
            stock=3,
            image="products/missing-image.jpg",
        )
        publication = {"available": False, "payload": None}
        initial_catalogue_ready = threading.Event()
        allow_recovery = threading.Event()

        def browser_flow(page):
            try:
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

                page.route("**/static/config.js", serve_frontend_config)
                page.route("**/__tests__/catalogue.json*", serve_published_catalogue)
                page.route(
                    "**/products/missing-image.jpg",
                    lambda route: route.fulfill(status=404),
                )

                page.goto(f"{self.live_server_url}/")

                card = page.locator(f'.product-card[data-product-id="{product.pk}"]')
                expect(card).to_be_visible()
                expect(page.locator("#catalogue-status")).to_have_text("1 product in the collection.")
                expect(page.locator("#catalogue-status")).not_to_contain_text("Loading")
                expect(card.locator(".image-placeholder")).to_be_visible(timeout=10_000)
                expect(card.locator("img.product-photo")).to_have_count(0)

                search = page.locator("#product-search")
                search.fill("not in the catalogue")
                expect(page.locator(".empty-state")).to_contain_text("No matching products")
                search.fill("amber")
                expect(card).to_be_visible()

                initial_catalogue_ready.set()
                if not allow_recovery.wait(timeout=30):
                    raise TimeoutError("The test did not release the catalogue recovery phase.")

                page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
                expect(card.locator(".product-description")).to_have_text(
                    "Updated after the storage outage.",
                    timeout=10_000,
                )
                expect(card.locator(".stock-status")).to_have_text("Out of stock")
            finally:
                initial_catalogue_ready.set()

        thread, result = self.run_browser_action(browser_flow)
        self.assertTrue(
            initial_catalogue_ready.wait(timeout=30),
            "The browser did not load the API fallback in time.",
        )
        if result["error"] is not None:
            allow_recovery.set()
            self.finish_browser_action(thread, result)
            return

        # Database access stays on the Django test thread, not Playwright's
        # event-loop thread. The browser waits until this revision is published.
        product.stock = 0
        product.description = "Updated after the storage outage."
        product.save()
        publication["payload"] = build_catalogue()
        publication["available"] = True
        allow_recovery.set()

        self.finish_browser_action(thread, result)

    def test_admin_login_password_toggle_and_authentication(self):
        password = "browser-test-password-123"
        get_user_model().objects.create_superuser(
            username="browser-admin",
            email="browser-admin@example.test",
            password=password,
        )

        def browser_flow(page):
            failed_requests = []
            page.on(
                "requestfailed",
                lambda request: failed_requests.append({
                    "url": request.url,
                    "failure": request.failure,
                }),
            )
            page.goto(f"{self.live_server_url}/admin/login/")

            password_input = page.locator("#id_password")
            toggle = page.get_by_role("button", name="Show password")
            if toggle.count() == 0:
                diagnostics = page.evaluate("""() => ({
                    bodyClass: document.body.className,
                    passwordFields: [...document.querySelectorAll('input')].map((input) => ({
                        id: input.id,
                        name: input.name,
                        type: input.type,
                        parent: input.parentElement?.outerHTML
                    })),
                    passwordScripts: [...document.scripts]
                        .map((script) => script.src)
                        .filter((src) => src.includes('password-toggle')),
                    readyState: document.readyState
                })""")
                raise AssertionError(
                    "Admin password toggle missing. "
                    f"DOM={diagnostics!r}; failedRequests={failed_requests!r}"
                )
            expect(toggle).to_be_visible()

            password_input.fill(password)
            toggle.click()
            expect(password_input).to_have_attribute("type", "text")
            expect(page.get_by_role("button", name="Hide password")).to_be_visible()

            page.get_by_role("button", name="Hide password").click()
            expect(password_input).to_have_attribute("type", "password")

            page.locator("#id_username").fill("browser-admin")
            page.locator('input[type="submit"]').click()

            page.wait_for_url(re.compile(r".*/admin/$"))
            expect(page.locator(".nqo-brand-name")).to_contain_text("Ngqo Enterprises")

        thread, result = self.run_browser_action(browser_flow)
        self.finish_browser_action(thread, result)
