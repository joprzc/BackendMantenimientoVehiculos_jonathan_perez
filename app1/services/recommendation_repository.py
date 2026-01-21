# paso 3 Crear servicio para persistir recomendaciones
from app1.models import RecomendacionMantenimiento


# Función para guardar recomendaciones
def guardar_recomendacion(vehiculo, recomendaciones):
    """Guarda recomendaciones evitando duplicados activos."""
    guardadas = []

    for rec in recomendaciones:
        # verificar si ya existe una recomendación activa similar
        existe = RecomendacionMantenimiento.objects.filter(
            vehiculo=vehiculo, codigo=rec["codigo"], estado="pendiente"
        ).exists()

        if not existe:
            r = RecomendacionMantenimiento.objects.create(
                vehiculo=vehiculo,
                codigo=rec["codigo"],
                titulo=rec["titulo"],
                mensaje=rec["descripcion"],
                severidad=rec["nivel"],
            )
            guardadas.append(r)

    return guardadas
