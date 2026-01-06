from django.urls import path

from . import views

urlpatterns = [
    path("add_vehicle", views.add_vehicle, name="add_vehicle"),
    path("all_vehicles", views.all_vehicles, name="all_vehicles"),
    path("track/<int:veh_id>", views.track_view, name="vehicles_track"),
    path("location/<int:veh_id>", views.current_view, name="current_view"),
    path("track", views.track_view, name="vehicles_track_all"),
]