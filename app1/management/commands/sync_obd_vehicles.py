# crear vehiculos segun obd vehicle_code
# crear vehiculos segun obd vehicle_code
from django.core.management.base import BaseCommand
from django.db import transaction
from app1.models import Vehiculo, obddata


class Command(BaseCommand):
    help = "Crea Vehiculos faltantes según obd_data.vehicle_code y vincula obddata.vehiculo"

    def handle(self, *args, **kwargs):
        existing = set(Vehiculo.objects.values_list("placa", flat=True))
        codes = list(obddata.objects.values_list("vehicle_code", flat=True).distinct())
        created = 0
        linked = 0

        with transaction.atomic():
            for code in codes:
                if not code:
                    continue
                if code not in existing:
                    # Vehiculo.objects.create(
                    #     placa=code,
                    #     anio=2020,  # valor por defecto
                    #     marca="Desconocida",  # valor por defecto
                    #     modelo="N/D",
                    #     tipo_combustible="Gasolina",
                    # )
                    vehiculo, created = Vehiculo.objects.get_or_create(
                        placa=vehicle_code,
                        defaults={
                            "marca": marca,
                            "modelo": modelo,
                        },
                    )

            # vincular placas huerfanas
            linked = (
                obddata.objects.filter(vehiculo__isnull=True)
                .filter(vehicle_code__in=existing)
                .update(
                    vehiculo_id=Vehiculo.objects.filter(
                        placa=models.OuterRef("vehicle_code")
                    ).values("id")[:1]
                )
            )
        self.stdout.write(self.style.SUCCESS(f"Vehiculos creados: {created}"))
        self.stdout.write(self.style.SUCCESS(f"Registros OBD vinculados: {linked}"))


# crear vehiculos segun obd vehicle_code
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import OuterRef, Subquery

from app1.models import Vehiculo, obddata


class Command(BaseCommand):
    help = "Crea Vehiculos faltantes según obd_data.vehicle_code y vincula obddata.vehiculo"

    def handle(self, *args, **kwargs):
        # placas ya existentes
        existing = set(Vehiculo.objects.values_list("placa", flat=True))

        # vehicle_code únicos en obddata
        codes = list(
            obddata.objects.values_list("vehicle_code", flat=True)
            .exclude(vehicle_code__isnull=True)
            .exclude(vehicle_code="")
            .distinct()
        )

        created_count = 0

        with transaction.atomic():
            # 1) crear vehículos faltantes (idempotente)
            for code in codes:
                # Si ya está en memoria, no consultamos DB
                if code in existing:
                    continue

                vehiculo, created = Vehiculo.objects.get_or_create(
                    placa=code,
                    defaults={
                        "anio": 2020,  # valor por defecto
                        "marca": "Desconocida",
                        "modelo": "N/D",
                        # "tipo_combustible": "Gasolina",
                    },
                )

                if created:
                    created_count += 1
                    existing.add(code)  # importante para no recrear en el mismo loop

            # 2) vincular registros OBD huérfanos a su vehículo por placa/vehicle_code
            vehiculo_id_sq = Subquery(
                Vehiculo.objects.filter(placa=OuterRef("vehicle_code")).values("id")[:1]
            )

            linked_count = (
                obddata.objects.filter(vehiculo__isnull=True)
                .filter(vehicle_code__in=existing)
                .update(vehiculo_id=vehiculo_id_sq)
            )

        self.stdout.write(self.style.SUCCESS(f"Vehiculos creados: {created_count}"))
        self.stdout.write(
            self.style.SUCCESS(f"Registros OBD vinculados: {linked_count}")
        )
