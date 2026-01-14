from django.core.management.base import BaseCommand
from app1.models import obddata


# Depurar datos
class Command(BaseCommand):
    help = "Depura y normaliza datos ODB-II"

    def handle(self, *args, **options):
        self.clean_inconsistent_rpm()
        self.clean_temperature_ranges()

    def clean_inconsistent_rpm(self):
        qs = obddata.objects.filter(engine_rpm=0, vehicle_speed_kph__gt=0)
        count = qs.count()
        qs.delete()

        self.stdout.write(
            self.style.WARNING(f"Eliminados {count} registros con RPM=0 y velocidad>0")
        )

    def clean_temperature_ranges(self):
        qs = obddata.objects.filter(engine_temp_c__lt=-20) | obddata.objects.filter(
            engine_temp_c__gt=150
        )

        count = qs.count()
        qs.delete()

        self.stdout.write(
            self.style.WARNING(
                f"Eliminados {count} registros con temperaturas de motor fuera de rango"
            )
        )

    # unificar unidades si es necesario
    def normalize_speed_units(self):
        qs = obddata.objects.filter(vehicle_speed_kph__gt=300)

        for record in qs:
            if record.vehicle_speed_kph is not None:
                record.vehicle_speed_kph = (
                    # convertir mph a kph
                    record.vehicle_speed_kph
                    * 1.60934
                )
                record.save()
