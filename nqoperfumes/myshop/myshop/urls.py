from django.contrib import admin
from django.urls import include, path

from store import seo, views

urlpatterns = [
    path("", views.homepage, name="home"),
    path("products/<int:pk>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("robots.txt", seo.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo.sitemap_xml, name="sitemap_xml"),
    path("admin/", admin.site.urls),
    path("api/", include("store.urls")),
]
