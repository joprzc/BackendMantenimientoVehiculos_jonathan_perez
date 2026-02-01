from django.core.management.base import BaseCommand
from app1.models import obddata, Vehiculo
import re


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

    def norm(s: str) -> str:
        if not s:
            return ""
        s = s.strip().upper()
        s = re.sub(r"[^A-Z0-9]", "", s)  # quita espacios y guiones
        return s

        # diccionario de placas
        placas = {norm(v.placa): v for v in Vehiculo.objects.all()}

        # al vincular
        code = norm(record.vehicle_code)
        vehiculo = placas.get(code)
        if vehiculo:
            record.vehiculo = vehiculo
            record.save(update_fields=["vehiculo"])
            linked += 1
        else:
            not_found += 1
