import re
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from store.catalogue import build_catalogue
from store.models import Product


@pytest.mark.django_db(transaction=True)
def test_storefront_falls_back_after_publish_failure_and_recovers(page, live_server):
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

    page.route("**/static/config.js", serve_frontend_config)
    page.route("**/__tests__/catalogue.json*", serve_published_catalogue)
    page.route(
        "**/products/missing-image.jpg",
        lambda route: route.fulfill(status=404),
    )

    page.goto(f"{live_server.url}/")

    card = page.locator(f'.product-card[data-product-id="{product.pk}"]')
    expect(card).to_be_visible()
    expect(card.locator(".image-placeholder")).to_be_visible(timeout=10_000)
    expect(card.locator("img.product-photo")).to_have_count(0)

    search = page.locator("#product-search")
    search.fill("not in the catalogue")
    expect(page.locator(".empty-state")).to_contain_text("No matching fragrances")
    search.fill("amber")
    expect(card).to_be_visible()

    # A later database revision and successful publication must replace the
    # API fallback with the newly published snapshot without a page reload.
    product.stock = 0
    product.description = "Updated after the storage outage."
    product.save()
    publication["payload"] = build_catalogue()
    publication["available"] = True

    page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")

    expect(card.locator(".product-description")).to_have_text(
        "Updated after the storage outage.",
        timeout=10_000,
    )
    expect(card.locator(".stock-status")).to_have_text("Out of stock")


@pytest.mark.django_db(transaction=True)
def test_admin_login_password_toggle_and_authentication(page, live_server):
    password = "browser-test-password-123"
    get_user_model().objects.create_superuser(
        username="browser-admin",
        email="browser-admin@example.test",
        password=password,
    )

    page.goto(f"{live_server.url}/admin/login/")

    password_input = page.locator("#id_password")
    toggle = page.get_by_role("button", name="Show password")
    expect(toggle).to_be_visible()

    password_input.fill(password)
    toggle.click()
    expect(password_input).to_have_attribute("type", "text")
    expect(page.get_by_role("button", name="Hide password")).to_be_visible()

    page.get_by_role("button", name="Hide password").click()
    expect(password_input).to_have_attribute("type", "password")

    page.locator("#id_username").fill("browser-admin")
    page.locator('input[type="submit"]').click()

    expect(page).to_have_url(re.compile(r"/admin/$"))
    expect(page.locator(".nqo-brand-name")).to_contain_text("Ngqo Perfumes")
