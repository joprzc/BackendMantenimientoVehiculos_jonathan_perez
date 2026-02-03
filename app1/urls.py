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
    # Ruta para el índice del vehículo
    path("obd/charts/", views.obd_charts_view, name="obd_charts"),
    # APIs para gráficas (AdminLTE + Chart.js)
    path("api/obd/rpm/", views.api_rpm_promedio, name="api_rpm_promedio"),
    path("api/obd/temp/", views.api_temp_motor, name="api_temp_motor"),
    path(
        "api/obd/vehspeed/", views.api_velocidad_promedio, name="api_velocidad_promedio"
    ),
    path("api/obd/coolant/", views.api_temp_refrigerante, name="api_temp_refrigerante"),
    path("api/obd/oilpressure/", views.api_presion_aceite, name="api_presion_aceite"),
    path("api/obd/alerts/", views.api_alerts, name="api_alerts"),
    # API agregada (si la usas)
    path("api/obd/charts/", views.obd_chart_data, name="obd_chart_data"),
    path(
        "vehiculo/<int:vehiculo_id>/dashboard/",
        views.vehiculo_dashboard,
        name="vehiculo_dashboard",
    ),
    path(
        "vehiculo/<int:vehiculo_id>/analizar/",
        views.analizar_vehiculo_action,
        name="analizar_vehiculo_action",
    ),
]
