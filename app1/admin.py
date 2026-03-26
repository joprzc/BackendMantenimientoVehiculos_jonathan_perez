from django.contrib import admin
from django.conf import settings
from .models import Vehiculo, Mantenimiento

# Register your models here.
# admin.site.register(Vehiculo)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("id", "marca", "modelo", "placa", "usuario")


# @admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ("id", "vehiculo", "fecha", "descripcion")
