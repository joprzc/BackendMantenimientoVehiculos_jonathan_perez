from django.utils import timezone
from rest_framework import serializers


class OBDIngestSerializer(serializers.Serializer):
    vehicle_code = serializers.CharField(max_length=64)

    # sino hay timestamp, usamos "now"
    timestamp = serializers.DateTimeField(required=False)

    engine_rpm = serializers.FloatField(required=False, allow_null=True)
    vehicle_speed_kph = serializers.FloatField(required=False, allow_null=True)
    engine_temp_c = serializers.FloatField(required=False, allow_null=True)
    oil_pressure_psi = serializers.FloatField(required=False, allow_null=True)
    battery_voltage_v = serializers.FloatField(required=False, allow_null=True)
    fuel_level_percent = serializers.FloatField(required=False, allow_null=True)
    engine_failure_imminent = serializers.BooleanField(required=False, allow_null=True)

    def validate(self, attrs):
        # default timestamp
        if "timestamp" not in attrs:
            attrs["timestamp"] = timezone.now()

        # obliga a que venga al menos 1 métrica (además del vehículo)
        metric_keys = [
            "engine_rpm",
            "vehicle_speed_kph",
            "engine_temp_c",
            "oil_pressure_psi",
            "battery_voltage_v",
            "fuel_level_percent",
            "engine_failure_imminent",
        ]
        if not any(k in attrs for k in metric_keys):
            raise serializers.ValidationError(
                "Debe incluir al menos una métrica OBD además de vehicle_code."
            )

        return attrs
