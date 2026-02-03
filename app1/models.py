from encodings.punycode import T
from operator import index
from django import db
from django.db import models

import app1


# modelo estructura de tabla para vehiculos
class Vehiculo(models.Model):

    anio = models.IntegerField()
    # marca = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    placa = models.CharField(max_length=10)
    # necesario para RF22
    tipo_comsbustible = models.CharField(max_length=20, default="Gasolina")
    imagen = models.ImageField(upload_to="vehiculos/", blank=True, null=True)

    # anotacions de tipo para evitar errores de pylance
    mantenimientos: models.Manager["Mantenimiento"]
    id: int  # El id siempre es un entero en Django por defecto

    @property
    def tipo_combustible(self):
        # alias limpio para usar en servicios
        return self.tipo_comsbustible

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
class obddata(models.Model):
    # relacion FK con vehiculo
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        related_name="obd_records",
        null=True,
        blank=True,
    )

    vehicle_code = models.CharField(max_length=20, db_index=True)
    # vehicle_code = models.CharField(max_length=20)
    timestamp = models.DateTimeField(db_index=True)
    # timestamp = models.DateTimeField()

    engine_rpm = models.FloatField(null=True, blank=True)
    engine_temp_c = models.FloatField(null=True, blank=True)
    fuel_level_percent = models.FloatField(null=True, blank=True)
    battery_voltage_v = models.FloatField(null=True, blank=True)
    engine_failure_imminent = models.BooleanField(null=True, blank=True)

    vehicle_speed_kph = models.FloatField(null=True, blank=True)

    coolant_temp_c = models.FloatField(null=True, blank=True)

    # oil_pressure_psi = models.FloatField(null=True, blank=True)

    # nuevos campos
    # oil_pressure_psi = models.FloatField(null=True, blank=True)

    # obtener meta datos
    class Meta:
        # db_table = "vehicle_telemetry"
        db_table = "obd_data"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(
                fields=["vehicle_code", "timestamp"],
                name="idx_vehicle_time",
            ),
        ]

    # validaciones de dominio
    def is_valid_record(self):

        if (
            self.engine_rpm == 0
            and self.vehicle_speed_kph is not None
            and self.vehicle_speed_kph > 0
        ):
            return False

        if self.engine_temp_c is not None and not (-20 <= self.engine_temp_c <= 150):
            return False

        return True


# Guardar recomendaciones en base de datos
# paso 1
class RecomendacionMantenimiento(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("atendido", "Atendido"),
    ]

    SEVERIDAD_CHOICES = [
        ("info", "Informativo"),
        ("warning", "Advertencia"),
        ("critical", "Crítico"),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, related_name="recomendaciones"
    )

    codigo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()

    severidad = models.CharField(max_length=10, choices=SEVERIDAD_CHOICES)

    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES, default="pendiente"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehiculo} - {self.codigo} ({self.severidad})"


# paso 2: migrar
# python manage.py makemigrations app1
# python manage.py migrate app1
