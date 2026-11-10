from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .catalogue import get_catalogue_revision
from .models import Product


@require_GET
def product_list_api(request):
    """Return the public product catalogue as a stable JSON API response."""
    products = Product.objects.all().order_by("-created_at", "-pk")
    results = []

    for product in products:
        image_url = product.image.url if product.image else None
        if image_url and not image_url.startswith(("http://", "https://")):
            image_url = request.build_absolute_uri(image_url)

        results.append(
            {
                "id": product.pk,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "stock": product.stock,
                "is_in_stock": product.is_in_stock(),
                "image_url": image_url,
            }
        )

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
