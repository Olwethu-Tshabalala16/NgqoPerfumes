from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("products/", views.product_list_api, name="product_list_api"),
    path("health/", views.health_check, name="health_check"),
]
