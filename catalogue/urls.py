from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/login/", views.dashboard_login, name="dashboard_login"),
    path("dashboard/logout/", views.dashboard_logout, name="dashboard_logout"),
    path("dashboard/", views.dashboard_home, name="dashboard"),
    path("dashboard/products/", views.dashboard_products, name="dashboard_products"),
    path("dashboard/products/add/", views.dashboard_product_add, name="dashboard_product_add"),
    path("dashboard/products/<int:pk>/delete/", views.dashboard_product_delete, name="dashboard_product_delete"),
    path("", views.home, name="index"),
    path("category/<slug:category_slug>/", views.category_detail, name="category_detail"),
    path("models/<int:pk>/", views.model_detail, name="model_detail"),
    path("products/<int:pk>/", views.legacy_product_detail, name="product_detail"),
    path("export/", views.export_excel, name="export_excel"),
    path("manifest.json", views.manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service_worker"),
]