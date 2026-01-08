from django.db import models


# modelo estructura de tabla para agendar mantenimientos
class Mantenimiento(models.Model):

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


# modelo estructura de tabla para vehiculos
class Vehiculo(models.Model):

    anio = models.IntegerField()
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    placa = models.CharField(max_length=10)
    imagen = models.ImageField(upload_to="vehiculos/", blank=True, null=True)

    # define como se veran las filas
    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.placa}"
