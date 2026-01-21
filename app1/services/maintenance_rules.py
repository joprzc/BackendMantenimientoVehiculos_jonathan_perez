# 1 Estructura base del motor de reglas
from app1.services.obd_metrics import (
    calcular_horas_motor,
    tiempo_rpm_alta,
    tiempo_temperatura_critica,
    promedios_obd,
)


# 2 Estructura estándar de una recomendación
def _recomendacion(codigo, titulo, descripcion, nivel):
    return {
        "codigo": codigo,
        "titulo": titulo,
        "descripcion": descripcion,
        "nivel": nivel,  # info | warning | critical
    }


# REGLA 1 — Cambio de aceite
# Conocimiento mecánico: Altas RPM, temperaturas elevadas y muchas horas de motor
def regla_cambio_aceite(vehiculo):
    horas = calcular_horas_motor(vehiculo)
    rpm_alta_min = tiempo_rpm_alta(vehiculo)
    temp_crit_min = tiempo_temperatura_critica(vehiculo)

    if horas >= 250 and rpm_alta_min > 30 and temp_crit_min > 10:
        return _recomendacion(
            "ACEITE_01",
            "Cambio de aceite recomendado",
            "Uso severo del motor detectado(RPM y temperatura elevada).",
            "warning",
        )
    return None


# REGLA 2 — Batería
# SUPONGO que tengo battery_voltage
# def regla_bateria(vehiculo):
#     proms = promedios_obd(vehiculo)

#     voltaje_bajo = proms.get("voltage_prom")

#     if voltaje and voltaje < 12.2:
#         return _recomendacion(
#             "BATT_01",
#             "Advertencia de batería",
#             "Voltaje promedio bajo. Posble bateria en mal estado.",
#             "Warning",
#         )
#     return None


# REGLA 3 — Sistema de refrigeración
def regla_refrigeracion(vehiculo):
    temp_crit_min = tiempo_temperatura_critica(vehiculo, umbral=105)

    if temp_crit_min > 5:
        return _recomendacion(
            "REFRIG_01",
            "Revisión del sistema de refrigeración",
            "Temperatura del motor elevada de forma frecuente.",
            "critical",
        )
    return None


# REGLA 4 — Combustible / Inyectores
# Regla empirica tecnica simple (sin ML)
def regla_inyectores(vehiculo):
    proms = promedios_obd(vehiculo)

    rpm_prom = proms.get("rpm_prom")
    velocidad_prom = proms.get("velocidad_prom")

    if rpm_prom and velocidad_prom:
        if rpm_prom > 3000 and velocidad_prom < 40:
            return _recomendacion(
                "FUEL_01",
                "Posible problema de inyecion",
                "RPM elevadas con baja velocidad promedio.",
                "info",
            )
    return None


# 3 Motor central de evaluación
def evaluar_mantenimiento(vehiculo):

    reglas = [
        regla_cambio_aceite,
        # regla_bateria,
        regla_refrigeracion,
        regla_inyectores,
    ]

    recomendaciones = []

    for regla in reglas:
        resultado = regla(vehiculo)
        if resultado:
            recomendaciones.append(resultado)

    return recomendaciones


# 4 intrucciones para probar el motor de forma correcta
# python manage.py shell
# from app1.services.maintenance_rules import evaluar_mantenimiento
# vehiculo = Vehiculo.objects.first()
# evaluar_mantenimiento(vehiculo)
