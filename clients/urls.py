from django.urls import path

from . import views

urlpatterns = [
    path("add_client", views.add_client, name="add_client"),
    path("all_clients", views.all_clients, name="all_clients"),
]