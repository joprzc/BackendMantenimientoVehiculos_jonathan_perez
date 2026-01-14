from django.core.management.base import BaseCommand
from app1.models import obddata, Vehiculo


class Command(BaseCommand):
    help = "Relaciona datos OBD con vehículos según el vehicle_code"

    def handle(self, *args, **kwargs):
        # Contadores para estadísticas
        linked = 0
        not_found = 0

        for record in obddata.objects.filter(vehiculo__isnull=True):
            try:
                vehiculo = Vehiculo.objects.get(placa=record.vehicle_code)
                record.vehiculo = vehiculo
                record.save()
                linked += 1
            except Vehiculo.DoesNotExist:
                not_found += 1

        self.stdout.write(self.style.SUCCESS(f"Registros vinculados: {linked}"))
        self.stdout.write(self.style.WARNING(f"Sin vehiculo asociado: {not_found}"))
