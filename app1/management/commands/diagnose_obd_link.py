from django.core.management.base import BaseCommand
from app1.models import obddata, Vehiculo
from collections import Counter


# Comando personalizado para diagnosticar problemas comunes en la conexión OBD-II
class Command(BaseCommand):
    help = "Diagnostica la relacion entre OBDData y Vehiculo"

    def handle(self, *args, **options):
        total_obd = obddata.objects.count()
        total_vehiculos = Vehiculo.objects.count()
        vinculados = obddata.objects.filter(vehiculo__isnull=False).count()
        huerfanos = obddata.objects.filter(vehiculo__isnull=True).count()

        self.stdout.write(self.style.SUCCESS("=== Resumen general ==="))
        self.stdout.write(f"Vehiculos registrados: {total_vehiculos}")
        self.stdout.write(f"Registros OBD-II totales: {total_obd}")
        self.stdout.write(f"OBD vinculados a vehiculos: {vinculados}")
        self.stdout.write(f"OBD sin vehiculo (huérfanos): {huerfanos}")

        codes = []
        if total_obd == 0:
            self.stdout.write(
                self.style.WARNING("No hay registros OBD-II en la base de datos.")
            )
            return

            self.stdout.write("\n=== VEHICLE_CODE DETECTADOS ===")

            codes = (
                obddata.objects.exclude(vehicle_code__isnull=True)
                .exclude(vehicle_code__exact="")
                .values_list("vehicle_code", flat=True)
            )

        counter = Counter(codes)
        for code, count in counter.most_common(10):
            existe = Vehiculo.objects.filter(placa=code).exists()
            status = " (EXISTE)" if existe else " (NO EXISTE)"
            self.stdout.write(f"{code} -> {count} registros ->{status}")

        self.stdout.write(self.style.SUCCESS("\nDiagnóstico completado."))
