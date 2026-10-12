from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("store.urls")),
    path("admin-2fa/", include("django_admin_2fa_plus.urls")),
]
