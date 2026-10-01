from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "is_in_stock", "created_at")
    list_filter = ("stock", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
