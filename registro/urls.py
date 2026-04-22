"""
URL configuration for registro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from app1 import views


# from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("admin/", admin.site.urls),
    # path("app1/", include("app1.urls")),
    path("", include("app1.urls")),
    path("signup/", views.SignupPage, name="signup"),
    path("login/", views.LoginPage, name="login"),
    path("inicio/", views.InicioPage, name="inicio"),
    path("logout/", views.LogoutPage, name="logout"),
    path("agenda/", views.agenda, name="agenda"),
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
    path(
        "agenda/notificar/<int:id>/",
        views.mantenimiento_send_notification,
        name="mantenimiento_send_notification",
    ),
    # Rutas para vehículos
    path("vehiculos/nuevo/", views.vehiculo_create, name="vehiculo_create"),
    path("vehiculos/editar/<int:id>/", views.vehiculo_edit, name="vehiculo_edit"),
    path("vehiculos/eliminar/<int:id>/", views.vehiculo_delete, name="vehiculo_delete"),
    path(
        "myvehiculo/vehiculoindex/<int:id>/",
        views.vehiculo_index,
        name="vehiculo_index",
    ),
]

# configuracion de archivos multimedia
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static[
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
