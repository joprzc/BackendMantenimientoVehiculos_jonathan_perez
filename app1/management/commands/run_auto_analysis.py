from django.core.management.base import BaseCommand
from django.utils import timezone

from app1.models import Vehiculo
from app1.services.maintenance_analyzer import analizar_vehiculo_y_guardar


# comando para ejecutar análisis automático (ej. cada 24h)
class Command(BaseCommand):
    help = (
        "Ejecuta análisis automático y guarda nuevas recomendaciones de mantenimiento."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--vehiculo_id",
            type=int,
            default=None,
            help="ID del vehículo (opcional). Si no se envia, analiza todos los vehículos.",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=None,
            help="Limita el número de vehículos a procesar (util para pruebas).",
        )

    def handle(self, *args, **options):
        vehiculo_id = options.get("vehiculo_id")
        limite = options.get("limite")

        qs = Vehiculo.objects.all().order_by("id")
        if vehiculo_id:
            qs = qs.filter(id=vehiculo_id)

        if limite:
            qs = qs[:limite]

        total_vehiculos = qs.count()
        total_guardados = 0

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando análisis. Vehículos: {total_vehiculos}"
            )
        )

        for v in qs:
            try:
                guardadas = analizar_vehiculo_y_guardar(v)
                n = len(guardadas) if guardadas else 0
                total_guardados += n

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Vehículo {v.id} ({getattr(v, 'placa', '-')}) -> nuevas: {n}"
                    )
                )
            except Exception as e:
                # no rompe el lote por un vehiculo con error
                self.stdout.write(
                    self.style.ERROR(
                        f"ERROR Vehículo {v.id} ({getattr(v, 'placa', '-')}) -> {e}"
                    )
                )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Fin. Total recomendaciones guardadas: {total_guardados}"
            )
        )
