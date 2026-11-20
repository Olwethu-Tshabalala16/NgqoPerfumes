"""Public catalogue pages and lightweight JSON endpoints."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from .catalogue import get_catalogue_revision
from .models import Product


def product_slug(name):
    return slugify(name) or "product"


def product_public_url(product):
    return reverse("product_detail", kwargs={"pk": product.pk, "slug": product_slug(product.name)})


def serialize_product(request, product):
    image_url = product.image.url if product.image else None
    if image_url and not image_url.startswith(("http://", "https://")):
        image_url = request.build_absolute_uri(image_url)
    return {
        "id": product.pk,
        "name": product.name,
        "category": product.category.name if product.category else None,
        "description": product.description,
        "price": str(product.price),
        "stock": product.stock,
        "is_in_stock": product.is_in_stock(),
        "image_url": image_url,
        "url": product_public_url(product),
    }


def apply_public_page_cache(response, request):
    # The home template can reflect a visitor's theme cookie.
    if request.COOKIES:
        response["Cache-Control"] = "private, no-store"
    else:
        response["Cache-Control"] = "public, max-age=0, s-maxage=60, stale-while-revalidate=120"
    return response


@require_GET
def homepage(request):
    """Render all products in the initial HTML response."""
    products = list(Product.objects.select_related("category").all().order_by("-created_at", "-pk"))
    product_data = [serialize_product(request, product) for product in products]
    response = render(request, "index.html", {
        "products": products,
        "initial_catalogue": {
            "revision": get_catalogue_revision(),
            "count": len(product_data),
            "products": product_data,
        },
    })
    return apply_public_page_cache(response, request)


@require_GET
def product_detail(request, pk, slug):
    """Serve an independently addressable product detail page."""
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    response = render(request, "product_detail.html", {
        "product": product,
        "product_data": serialize_product(request, product),
        "product_url": product_public_url(product),
    })
    return apply_public_page_cache(response, request)


@require_GET
def product_list_api(request):
    """Return the public product catalogue as a stable JSON API response."""
    products = Product.objects.select_related("category").all().order_by("-created_at", "-pk")
    results = [serialize_product(request, product) for product in products]
    return JsonResponse({"count": len(results), "results": results})


@require_GET
def product_catalogue_version_api(request):
    """Return the same revision embedded in the published catalogue."""
    response = JsonResponse({"version": get_catalogue_revision()})
    response["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
    return response


@require_GET
def health_check(request):
    """Expose a lightweight endpoint for deployment and uptime checks."""
    return JsonResponse({"status": "ok"})
