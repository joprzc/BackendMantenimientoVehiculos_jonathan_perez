from datetime import timedelta

from django.db.models import Max, Min
from django.utils import timezone

from app1.models import obddata, RecomendacionMantenimiento, Vehiculo

# constantes alineadas con choices del modelo
ESTADO_PENDIENTE = "pendiente"
ESTADO_ATENDIDO = "atendido"
SEVERIDAD_INFO = "info"
SEVERIDAD_WARNING = "warning"
SEVERIDAD_CRITICAL = "critical"


def _get_obd_queryset_for_vehicle(vehiculo: Vehiculo):
    """
    Prioriza datos ligados por FK; si no hay, usa vehicle_code = placa.
    """
    qs = obddata.objects.filter(vehiculo=vehiculo)
    if qs.exists():
        return qs
    if vehiculo.placa:
        return obddata.objects.filter(vehicle_code__iexact=vehiculo.placa)
    return obddata.objects.none()


def _obtener_registros_recientes(vehiculo, max_registros=500, ventana_horas=24):
    """
    Limita por ventana temporal y cantidad máxima.
    """
    desde = timezone.now() - timedelta(hours=ventana_horas)
    return (
        _get_obd_queryset_for_vehicle(vehiculo)
        .filter(timestamp__gte=desde)
        .order_by("-timestamp")[:max_registros]
    )


def _crear_recomendacion_unica(vehiculo, codigo, titulo, mensaje, severidad):
    """
    Evita duplicados pendientes por código.
    """
    existe = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo, codigo=codigo, estado=ESTADO_PENDIENTE
    ).exists()
    if existe:
        return None

    return RecomendacionMantenimiento.objects.create(
        vehiculo=vehiculo,
        codigo=codigo,
        titulo=titulo,
        mensaje=mensaje,
        severidad=severidad,
        estado=ESTADO_PENDIENTE,
    )


# ---------------------------------------------------------
# evaluar rpm
# ---------------------------------------------------------
def _evaluar_alertas_rpm(registros):
    """
    evalua patrones de RPM sobre los registros recientes y devuelve recomendaciones en formato dict.
    """
    recomendaciones = []

    # convertimos queryset a lista para poder recorrerlo varias veces
    # data = list(registros.order_by("-timestamp"))
    data = list(registros)

    if not data:
        return recomendaciones

    rpms_validas = [r.engine_rpm for r in data if r.engine_rpm is not None]
    if not rpms_validas:
        return recomendaciones

    max_rpm = max(rpms_validas)
    min_rpm = min(rpms_validas)

    # ---------------------------------------------
    # 1. ralenti inestable
    # ---------------------------------------------
    registros_ralenti = [
        r
        for r in data
        if r.engine_rpm is not None
        and r.vehicle_speed_kph is not None
        and r.vehicle_speed_kph <= 3
        and 500 <= r.engine_rpm <= 1200
    ]
    if len(registros_ralenti) >= 5:
        rpms_ralenti = [r.engine_rpm for r in registros_ralenti]
        variacion_ralenti = max(rpms_ralenti) - min(rpms_ralenti)

        if variacion_ralenti > 300:
            recomendaciones.append(
                {
                    "codigo": "RPM_RALENTI_INESTABLE",
                    "titulo": "Ralenti inestable detectado",
                    "mensaje": (
                        f"Se detectó una variación de {variacion_ralenti:.1f} RPM "
                        "con el vehículo detenido. Revisar admisión, cuerpo de aceleración y sistema de encendido."
                    ),
                    "severidad": SEVERIDAD_WARNING,
                }
            )

    # ---------------------------------------------
    # 2. RPM altas sostenidas
    # ---------------------------------------------
    ultimos_altos = [r.engine_rpm for r in data[:10] if r.engine_rpm is not None]
    if len(ultimos_altos) >= 5:
        promedio_ultimos_altos = sum(ultimos_altos) / len(ultimos_altos)
        if promedio_ultimos_altos > 3000:
            recomendaciones.append(
                {
                    "codigo": "RPM_ALTAS_SOSTENIDAS",
                    "titulo": "RPM altas sostenidas",
                    "mensaje": (
                        f"Se registró un promedio reciente de {promedio_ultimos_altos:.1f} RPM. "
                        "El uso prolongado a altas revoluciones puede acelerar el desgaste del motor. "
                    ),
                    "severidad": SEVERIDAD_WARNING,
                }
            )

    # ---------------------------------------------
    # 3. zona critica de RPM
    # ---------------------------------------------
    if max_rpm > 4500:
        recomendaciones.append(
            {
                "codigo": "RPM_ZONA_CRITICA",
                "titulo": "RPM en zona crítica",
                "mensaje": (
                    f"Se detectó un valor máximo de {max_rpm:.1f} RPM. "
                    "Reducir exigencia del motor y verificar condiciones de operación."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # ---------------------------------------------
    # 4. picos brucos de RPM
    # ---------------------------------------------
    picos_bruscos = 0
    for i in range(len(data) - 1):
        actual = data[i].engine_rpm
        siguiente = data[i + 1].engine_rpm

        if actual is None or siguiente is None:
            continue

        if abs(actual - siguiente) > 1500:
            picos_bruscos += 1

    if picos_bruscos >= 2:
        recomendaciones.append(
            {
                "codigo": "RPM_PICOS_BRUSCOS",
                "titulo": "Picos bruscos de RPM",
                "mensaje": (
                    f"Se detectaron {picos_bruscos} cambios bruscos de revoluciones. "
                    "Revisar aceleración, transmisión o comportamiento anormal del motor."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    # -------------------------------------------------
    # 5. RPM BAJAS CON EL VEHÍCULO EN MOVIMIENTO
    # -------------------------------------------------
    registros_baja_carga = [
        r
        for r in data
        if r.engine_rpm is not None
        and r.vehicle_speed_kph is not None
        and r.vehicle_speed_kph > 20
        and r.engine_rpm < 1200
    ]

    if len(registros_baja_carga) >= 3:
        recomendaciones.append(
            {
                "codigo": "RPM_BAJAS_EN_MOVIMIENTO",
                "titulo": "RPM bajas con el vehículo en movimiento",
                "mensaje": (
                    "Se detectaron revoluciones bajas mientras el vehículo estaba en movimiento. "
                    "Esto puede indicar esfuerzo excesivo del motor o uso inadecuado de la marcha."
                ),
                "severidad": SEVERIDAD_INFO,
            }
        )

    return recomendaciones


# ----------------------------------------------------------
# evaluar temperatura del motor (engine_temp_c)
# ----------------------------------------------------------
def _evaluar_alertas_temperatura(registros):
    """
    Evalúa engine_temp_c y devuelve recomendaciones de mantenimiento."""
    recomendaciones = []
    data = list(registros)

    if not data:
        return recomendaciones

    # filtrar y extraer datos (comprension de listas)
    temps_validas = [r.engine_temp_c for r in data if r.engine_temp_c is not None]

    if not temps_validas:
        return recomendaciones

    max_temp = max(temps_validas)

    # 1. Temperatura critica inmediata
    if max_temp >= 115:
        recomendaciones.append(
            {
                "codigo": "TEMP_CRITICA",
                "titulo": "Temperatura crítica del motor",
                "mensaje": (
                    f"Se detectó una temperatura máxima de {max_temp:.1f} °C. "
                    "Se recomienda detener el vehículo y revisar urgentemente el sistema de refrigeración."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # 2. Temperatura alta sostenida
    ultimas_temps = [r.engine_temp_c for r in data[:10] if r.engine_temp_c is not None]

    if len(ultimas_temps) >= 5:
        promedio_temp = sum(ultimas_temps) / len(ultimas_temps)

        if promedio_temp >= 105 and max_temp < 115:
            recomendaciones.append(
                {
                    "codigo": "TEMP_ALTA_SOSTENIDA",
                    "titulo": "Temperatura elevada del motor",
                    "mensaje": (
                        f"Se registró un promedio reciente de {promedio_temp:.1f} °C. "
                        "Revisar nivel de refrigerante, radiador, termostato y ventilador."
                    ),
                    "severidad": SEVERIDAD_WARNING,
                }
            )

    # 3. Registros frecuentes con temperatura alta
    registros_altos = [
        r for r in data if r.engine_temp_c is not None and 105 <= r.engine_temp_c < 115
    ]

    if len(registros_altos) >= 3 and max_temp < 115:
        recomendaciones.append(
            {
                "codigo": "TEMP_ALTA_FRECUENTE",
                "titulo": "Temperatura alta frecuente",
                "mensaje": (
                    f"Se detectaron {len(registros_altos)} registros con temperatura elevada. "
                    "Se recomienda revisar el sistema de enfriamiento para prevenir sobrecalentamiento."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )
    return recomendaciones


# ----------------------------------------------------------
# evaluar bateria (battery_voltage_v)
# ----------------------------------------------------------
def _evaluar_alertas_bateria(registros):
    """
    Evalúa battery_voltage_v y devuelve recomendaciones de mantenimiento.
    """
    recomendaciones = []
    data = list(registros)

    if not data:
        return recomendaciones

    voltajes_validos = [
        r.battery_voltage_v for r in data if r.battery_voltage_v is not None
    ]

    if not voltajes_validos:
        return recomendaciones

    max_voltaje = max(voltajes_validos)
    min_voltaje = min(voltajes_validos)

    registros_motor_encendido = [
        r
        for r in data
        if r.engine_rpm is not None
        and r.engine_rpm > 500
        and r.battery_voltage_v is not None
    ]

    # 1. Batería crítica con motor encendido
    criticos = [r for r in registros_motor_encendido if r.battery_voltage_v < 12.5]

    if len(criticos) >= 1:
        recomendaciones.append(
            {
                "codigo": "BATERIA_CRITICA",
                "titulo": "Voltaje crítico de batería",
                "mensaje": (
                    f"Se detectó un voltaje mínimo de {min_voltaje:.1f} V con el motor encendido. "
                    "El vehículo podría estar funcionando solo con la energía de la batería. "
                    "Revisar alternador, batería, bornes y sistema de carga."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # 2. Carga insuficiente
    bajos = [r for r in registros_motor_encendido if 12.5 <= r.battery_voltage_v < 13.2]

    if len(bajos) >= 3:
        recomendaciones.append(
            {
                "codigo": "BATERIA_CARGA_INSUFICIENTE",
                "titulo": "Carga insuficiente del sistema eléctrico",
                "mensaje": (
                    f"Se detectaron {len(bajos)} registros con voltaje menor a 13.2 V. "
                    "Esto puede indicar fallas en el alternador, correa floja o batería descargándose."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    # 3. Sobrecarga eléctrica
    sobrecargas = [r for r in registros_motor_encendido if r.battery_voltage_v > 15.0]

    if len(sobrecargas) >= 1:
        recomendaciones.append(
            {
                "codigo": "BATERIA_SOBRECARGA",
                "titulo": "Sobrecarga del sistema eléctrico",
                "mensaje": (
                    f"Se detectó un voltaje máximo de {max_voltaje:.1f} V. "
                    "Puede existir una falla en el regulador de voltaje o alternador, "
                    "lo cual puede dañar sensores, ECU o batería."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # 4. Voltaje inestable
    variaciones_bruscas = 0

    for i in range(len(data) - 1):
        actual = data[i].battery_voltage_v
        siguiente = data[i + 1].battery_voltage_v

        if actual is None or siguiente is None:
            continue

        if abs(actual - siguiente) > 1.0:
            variaciones_bruscas += 1

    if variaciones_bruscas >= 2:
        recomendaciones.append(
            {
                "codigo": "BATERIA_VOLTAJE_INESTABLE",
                "titulo": "Voltaje de batería inestable",
                "mensaje": (
                    f"Se detectaron {variaciones_bruscas} variaciones bruscas de voltaje. "
                    "Revisar bornes, cableado, alternador o posibles falsos contactos."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    return recomendaciones


# ----------------------------------------------------------
# evaluar combustible (fuel_level_percent)
# ----------------------------------------------------------
def _evaluar_alertas_combustible(registros):
    recomendaciones = []
    data = list(registros)

    if not data:
        return recomendaciones

    # comprension de listas para extraer niveles de combustible válidos
    niveles_validos = [
        r.fuel_level_percent for r in data if r.fuel_level_percent is not None
    ]

    if not niveles_validos:
        return recomendaciones

    min_fuel = min(niveles_validos)

    # 1. Combustible crítico
    criticos = [
        r
        for r in data
        if r.fuel_level_percent is not None and r.fuel_level_percent <= 10
    ]

    if len(criticos) >= 2:
        recomendaciones.append(
            {
                "codigo": "COMBUSTIBLE_CRITICO",
                "titulo": "Nivel crítico de combustible",
                "mensaje": (
                    f"Se detectó un nivel mínimo de combustible de {min_fuel:.1f}%. "
                    "El vehículo se encuentra en reserva. Se recomienda abastecer inmediatamente."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # 2. Combustible bajo
    bajos = [
        r
        for r in data
        if r.fuel_level_percent is not None and 10 < r.fuel_level_percent <= 20
    ]

    if len(bajos) >= 3:
        recomendaciones.append(
            {
                "codigo": "COMBUSTIBLE_BAJO",
                "titulo": "Nivel bajo de combustible",
                "mensaje": (
                    f"Se detectaron {len(bajos)} registros con combustible bajo. "
                    "Se recomienda abastecer pronto para evitar interrupciones durante el recorrido."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    # 3. Posible falla del sensor
    cambios_bruscos = 0

    for i in range(len(data) - 1):
        actual = data[i].fuel_level_percent
        siguiente = data[i + 1].fuel_level_percent

        if actual is None or siguiente is None:
            continue

        if abs(actual - siguiente) > 25:
            cambios_bruscos += 1

    if cambios_bruscos >= 2:
        recomendaciones.append(
            {
                "codigo": "COMBUSTIBLE_SENSOR_INESTABLE",
                "titulo": "Lectura inestable del combustible",
                "mensaje": (
                    f"Se detectaron {cambios_bruscos} variaciones bruscas en el nivel de combustible. "
                    "Revisar aforador, flotador, cableado o sensor del tanque."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    return recomendaciones


def _evaluar_registros(registros):
    """
    Devuelve una lista de dicts con recomendaciones basadas en las métricas.
    """
    recomendaciones = []

    min_oil = registros.aggregate(Min("oil_pressure_psi"))["oil_pressure_psi__min"]
    if min_oil is not None and min_oil < 30:
        recomendaciones.append(
            {
                "codigo": "ACEITE_BAJO",
                "titulo": "Presión de aceite baja",
                "mensaje": (
                    f"Presión mínima registrada: {min_oil:.1f} psi. "
                    "Verificar nivel/calidad de aceite y posibles fugas."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # if registros.filter(engine_failure_imminent=True).exists():
    if any(r.engine_failure_imminent for r in registros):
        recomendaciones.append(
            {
                "codigo": "FALLO_INMINENTE",
                "titulo": "Alerta de fallo inminente",
                "mensaje": (
                    "El módulo OBD reportó un posible fallo inminente. "
                    "Realizar diagnóstico completo del motor."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    # alertas por RPM
    recomendaciones.extend(_evaluar_alertas_rpm(registros))

    # alertas por temperatura del motor
    recomendaciones.extend(_evaluar_alertas_temperatura(registros))

    # alertas por batería
    recomendaciones.extend(_evaluar_alertas_bateria(registros))

    # alertas por combustible
    recomendaciones.extend(_evaluar_alertas_combustible(registros))

    return recomendaciones


def analizar_vehiculo(vehiculo, max_registros=500, ventana_horas=24):
    """
    Devuelve recomendaciones (no guarda). Útil para mostrar en dashboard.
    """
    registros = _obtener_registros_recientes(
        vehiculo, max_registros=max_registros, ventana_horas=ventana_horas
    )
    if not registros.exists():
        return []
    return _evaluar_registros(registros)


def analizar_vehiculo_y_guardar(vehiculo, max_registros=500, ventana_horas=24):
    """
    Genera y guarda recomendaciones nuevas. Devuelve solo las recién creadas.
    """
    registros = _obtener_registros_recientes(
        vehiculo, max_registros=max_registros, ventana_horas=ventana_horas
    )
    if not registros.exists():
        return []

    nuevas = []
    for rec in _evaluar_registros(registros):
        creada = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo=rec["codigo"],
            titulo=rec["titulo"],
            mensaje=rec["mensaje"],
            severidad=rec["severidad"],
        )
        if creada:
            nuevas.append(creada)
    return nuevas
