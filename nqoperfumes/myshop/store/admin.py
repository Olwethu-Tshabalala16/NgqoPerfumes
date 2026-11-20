import logging

from django.contrib import admin, messages
from django.http import JsonResponse
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from .catalogue import publish_catalogue
from .models import Category, Product

logger = logging.getLogger(__name__)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

    def _publish_catalogue(self, request):
        try:
            url = publish_catalogue()
        except Exception:
            logger.exception("Category saved, but publishing the Supabase JSON catalogue failed.")
            self.message_user(
                request,
                "The category was saved, but the Supabase JSON catalogue could not be updated.",
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_form_template = "admin/store/product/change_form.html"
    list_display = ("name", "category", "price", "stock", "is_in_stock", "created_at")
    list_filter = ("category", "stock", "created_at")
    search_fields = ("name", "description", "category__name")
    readonly_fields = ("created_at", "updated_at")

    class Media:
        js = ("admin/category-admin.js",)

    def get_urls(self):
        custom_urls = [
            path(
                "add-category/",
                self.admin_site.admin_view(self.add_category_view),
                name="store_product_add_category",
            ),
        ]
        return custom_urls + super().get_urls()

    @require_POST
    def add_category_view(self, request):
        category_admin = self.admin_site._registry[Category]
        if not category_admin.has_add_permission(request):
            return JsonResponse({"error": "You do not have permission to add categories."}, status=403)

        name = request.POST.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Enter a category name."}, status=400)
        if len(name) > 100:
            return JsonResponse({"error": "Category names must be 100 characters or fewer."}, status=400)

        category, created = Category.objects.get_or_create(name=name)
        if created:
            try:
                publish_catalogue()
            except Exception:
                logger.exception("Category created, but the Supabase JSON catalogue could not be refreshed.")
        return JsonResponse(
            {"id": category.pk, "name": category.name, "created": created},
            status=201 if created else 200,
        )

    def render_change_form(self, request, context, *args, **kwargs):
        context["add_category_url"] = reverse("admin:store_product_add_category")
        return super().render_change_form(request, context, *args, **kwargs)

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
