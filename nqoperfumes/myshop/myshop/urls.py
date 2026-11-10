from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from store import seo

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("robots.txt", seo.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo.sitemap_xml, name="sitemap_xml"),
    path("admin/", admin.site.urls),
    path("api/", include("store.urls")),
]
