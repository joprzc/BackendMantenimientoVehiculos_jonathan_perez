from django.urls import path
from . import views

urlpatterns = [
    # Rutas para mantenimientos
    path("agenda/nuevo/", views.mantenimiento_create, name="mantenimiento_create"),
    path(
        "agenda/editar/<int:id>/", views.mantenimiento_edit, name="mantenimiento_edit"
    ),
    path(
        "agenda/eliminar/<int:id>/",
        views.mantenimiento_delete,
        name="mantenimiento_delete",
    ),
    # Rutas para vehículos
    path("vehiculos/nuevo/", views.vehiculo_create, name="vehiculo_create"),
    path("vehiculos/editar/<int:id>/", views.vehiculo_edit, name="vehiculo_edit"),
    path("vehiculos/eliminar/<int:id>/", views.vehiculo_delete, name="vehiculo_delete"),
]
