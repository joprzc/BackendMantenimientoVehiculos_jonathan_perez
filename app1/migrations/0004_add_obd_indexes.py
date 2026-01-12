from django.db import migrations, models


# crear un migracion personalizada para optimizar consultas OBDII añadiendo indices
class Migration(migrations.Migration):

    # esta migracion se aplica despues de la migracion 0003_mantenimiento_vehiculo
    dependencies = [
        # Ajusta esto según tu última migración
        (
            "app1",
            "0003_mantenimiento_vehiculo",
        ),
    ]

    # operaciones de la migracion
    operations = [
        # primier indice
        migrations.AddIndex(
            model_name="odbdata",
            index=models.Index(
                fields=["vehicle_code", "timestamp"], name="idx_vehicle_time"
            ),
        ),
    ]
