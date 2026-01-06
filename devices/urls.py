from django.urls import path

from . import views

urlpatterns = [
    path("add_device", views.add_device, name="add_device"),
    path("all_devices", views.all_devices, name="all_devices"),
    path("sapi_v1_write/", views.sapi_v1_write, name="sapi_v1_write"),
    path("assign_device/", views.assign_device, name="assign_device"),
]