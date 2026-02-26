# app1/management/commands/collect_obd.py
import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from app1.services.obd_ingest import insert_obd_row


class Command(BaseCommand):
    help = (
        "Genera lecturas OBD simuladas y las guarda en la tabla obd_data (modo demo)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--vehicle", default="DEMO-000", help="vehicle_code demo")
        parser.add_argument("--n", type=int, default=1, help="cantidad de lecturas")

    def handle(self, *args, **opts):
        vehicle_code = opts["vehicle"]
        n = opts["n"]

        for _ in range(n):
            payload = {
                "timestamp": timezone.now(),
                "vehicle_code": vehicle_code,
                "engine_rpm": round(random.uniform(700, 3200), 2),
                "vehicle_speed_kph": round(random.uniform(0, 110), 2),
                "engine_temp_c": round(random.uniform(70, 105), 2),
                "oil_pressure_psi": round(random.uniform(18, 65), 2),
                "battery_voltage_v": round(random.uniform(12.0, 14.6), 2),
                "fuel_level_percent": round(random.uniform(5, 95), 2),
                "engine_failure_imminent": False,
            }
            insert_obd_row(payload)

        self.stdout.write(
            self.style.SUCCESS(f"OK: Insertadas {n} lecturas demo para {vehicle_code}")
        )
