# evita sobrecargar models
from datetime import datetime, timedelta
from django.db.models import Avg
from app1.models import obddata


# horas de motor acumuladas
# Logica: si el motor esta encendido(engine_rpm > 0), el tiempo entre registros cuenta.
def calcular_horas_motor(vehiculo):
    registros = obddata.objects.filter(
        vehiculo=vehiculo,
        engine_rpm__gt=0,
    ).order_by("timestamp")

    total_segundos = 0
    anterior = None

    for r in registros:
        if anterior:
            delta = (r.timestamp - anterior).total_seconds()
            # considerar solo si el delta es razonable (ej. menos de 5 min)
            if delta < 300:
                total_segundos += delta
        # anterior = r.timestamp
        anterior = r.timestamp

    return round(total_segundos / 3600, 2)  # horas con 2 decimales


# kilometros estimados
# Logica: velocidad promedio * tiempo
def calcular_kilometros_estimados(vehiculo):
    registros = obddata.objects.filter(
        vehiculo=vehiculo, vehicle_speed_kph__gt=0
    ).order_by("timestamp")

    km = 0
    anterior = None

    for r in registros:
        if anterior:
            delta_horas = (r.timestamp - anterior.timestamp).total_seconds() / 3600
            # considerar solo si el delta es razonable (ej. menos de 0.1 min)
            if delta_horas < 0.1:
                km += r.vehicle_speed_kph * delta_horas
        anterior = r

    return round(km, 2)  # kilómetros con 2 decimales


# Tiempo en condiciones críticas
# RPM altas (>3000)
def tiempo_rpm_alta(vehiculo, umbral=3000):
    # registros = obddata.objects.filter(
    #     vehiculo=vehiculo, engine_rpm__gte=umbral
    # ).order_by("timestamp")
    registros = obddata.objects.filter(vehiculo=vehiculo).order_by("timestamp")

    # return _calcular_tiempo(registros)
    total = 0
    anterior = None

    for r in registros:
        if anterior is not None:
            delta = (r.timestamp - anterior.timestamp).total_seconds()
            # tolera huecos (por defecto: 6 horas)
            if (
                0 < delta <= 21600
                and anterior.engine_rpm is not None
                and anterior.engine_rpm >= umbral
            ):
                total += delta
        anterior = r

    return round(total / 60, 1)


# temperatura motor (>100C)
def tiempo_temperatura_critica(vehiculo, umbral=100):
    # registros = obddata.objects.filter(
    #     vehiculo=vehiculo, engine_temp_c__gte=umbral
    # ).order_by("timestamp")
    registros = obddata.objects.filter(vehiculo=vehiculo).order_by("timestamp")

    return _calcular_tiempo(registros)

    total = 0
    anterior = None

    for r in registros:
        if anterior is not None:
            delta = (r.timestamp - anterior.timestamp).total_seconds()
            if (
                0 < delta <= 21600
                and anterior.engine_temp_c is not None
                and anterior.engine_temp_c >= umbral
            ):
                total += delta
        anterior = r


# Función reutilizable para calcular tiempo entre registros(minutos)
def _calcular_tiempo(registros, max_delta_seg: int = 21600):

    # suma deltas en segundos
    total = 0
    anterior = None

    for r in registros:
        if anterior is not None:
            delta = (r.timestamp - anterior.timestamp).total_seconds()
            # considerar solo si el delta es razonable (ej. menos de 5 min)
            # if delta < 200:
            #     total += delta
            # tolerancia mayor tiempo(por defecto 6 horas)
            if 0 < delta <= max_delta_seg:
                total += delta

        anterior = r

    return round(total / 60, 1)  # minutos


# Promedios móviles (agregados simples)
def promedios_obd(vehiculo):
    return obddata.objects.filter(vehiculo=vehiculo).aggregate(
        temp_prom=Avg("engine_temp_c"),
        rpm_prom=Avg("engine_rpm"),
        velocidad_prom=Avg("vehicle_speed_kph"),
        presion_aceite_prom=Avg("oil_pressure_psi"),
    )
