from django import db
from django.db import models

import app1


# modelo estructura de tabla para vehiculos
class Vehiculo(models.Model):

    anio = models.IntegerField()
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    placa = models.CharField(max_length=10)
    imagen = models.ImageField(upload_to="vehiculos/", blank=True, null=True)

    # anotacions de tipo para evitar errores de pylance
    mantenimientos: models.Manager["Mantenimiento"]
    id: int  # El id siempre es un entero en Django por defecto

    # define como se veran las filas
    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.placa}"


# modelo estructura de tabla para agendar mantenimientos
class Mantenimiento(models.Model):

    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, related_name="mantenimientos"
    )

    fecha = models.DateField()
    descripcion = models.CharField(max_length=150)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("Pendiente", "Pendiente"),
            ("Programado", "Programado"),
            ("Realizado", "Realizado"),
        ],
    )

    # define como se veran las filas
    def __str__(self):
        return f"{self.fecha} - {self.descripcion} - {self.estado}"


# BASE DE DATOS ODBII
class ODBData(models.Model):
    vehicle_code = models.CharField(max_length=20, db_index=True)
    timestamp = models.DateTimeField(db_index=True)

    engine_rpm = models.FloatField(null=True, blank=True)
    vehicle_speed_kph = models.FloatField(null=True, blank=True)

    engine_temp_c = models.FloatField(null=True, blank=True)
    coolant_temp_c = models.FloatField(null=True, blank=True)

    oil_pressure_psi = models.FloatField(null=True, blank=True)

    # obtener meta datos
    class Meta:
        db_table = "vehicle_telemetry"
        ordering = ["-timestamp"]
