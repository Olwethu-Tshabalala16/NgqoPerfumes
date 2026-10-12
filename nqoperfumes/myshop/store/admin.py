import logging

from django.contrib import admin, messages

from .catalogue import publish_catalogue
from .models import Product

logger = logging.getLogger(__name__)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "is_in_stock", "created_at")
    list_filter = ("stock", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    def _publish_catalogue(self, request):
        try:
            url = publish_catalogue()
        except Exception:
            logger.exception("Product saved, but publishing the Supabase JSON catalogue failed.")
            self.message_user(
                request,
                "The product was saved, but the Supabase JSON catalogue could not be updated. "
                "Check the Supabase Storage environment variables and server logs.",
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                f"Supabase product catalogue updated: {url}",
                level=messages.SUCCESS,
            )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._publish_catalogue(request)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self._publish_catalogue(request)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        self._publish_catalogue(request)
