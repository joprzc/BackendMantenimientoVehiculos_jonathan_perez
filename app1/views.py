from ast import If
from operator import ge
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Mantenimiento, Vehiculo, obddata
from .forms import MantenimientoForm, VehiculoForm
from django.views.decorators.http import require_POST  # bloquea metodos no permitidos
from django.contrib import messages  # para mensajes flash
from django.utils.dateparse import parse_date
from django.db.models import Avg, Count
from django.db.models.functions import TruncHour

# vistas del dashboard de OBD-II
from app1.models import obddata
from app1.models import Vehiculo, RecomendacionMantenimiento
from app1.services.obd_metrics import (
    calcular_horas_motor,
    calcular_kilometros_estimados,
    tiempo_rpm_alta,
    tiempo_temperatura_critica,
)
from app1.services.maintenance_analyzer import analizar_vehiculo_y_guardar


# Create your views here.
@login_required(
    login_url="login"
)  # evita que ingresemos directamente a la pagina inicio
def InicioPage(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # listar vehiculos
    vehiculos = Vehiculo.objects.all()
    form = VehiculoForm()

    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("inicio")

    return render(request, "inicio.html", {"vehiculos": vehiculos, "form": form})


def SignupPage(request):
    if request.method == "POST":  # revisa si el formulario fue enviado
        # datos a obtener/enviados desde el formulario
        uname = request.POST.get("username")
        email = request.POST.get("email")
        pass1 = request.POST.get("password1")
        pass2 = request.POST.get("password2")
        # validar que la contraseña coincida
        if pass1 != pass2:
            return HttpResponse(
                "Tu contraseña y la confirmación de contraseña no coinciden."
            )
        else:

            my_user = User.objects.create_user(uname, email, pass1)
            my_user.save()
            return redirect("login")
        # return HttpResponse("Usuario ha sido creado exitosamente")

        # print(uname, email,pass1,pass2)
    print("Tu contraseña y la confirmación de contraseña no coinciden.")
    return render(request, "signup.html")  # muestra la pagina signup.html


def LoginPage(request):
    if request.method == "POST":  # verifico si el formulario fue enviado
        # lee los valores enviados desde el formulario
        username = request.POST.get("username")
        pass1 = request.POST.get("pass")
        # print(username,pass1)
        user = authenticate(request, username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect("inicio")
        else:
            messages.error(request, "Usuario o clave es incorrecto")
            return redirect("login")

    return render(request, "login.html")


def LogoutPage(request):
    logout(request)
    return redirect("login")


# CRUD
# agenda de mantenimiento
# listar
def agenda(request):
    mantenimientos = Mantenimiento.objects.select_related("vehiculo").all()
    return render(
        request,
        "agenda.html",
        {
            "mantenimientos": mantenimientos,
        },
    )


# crear
def mantenimiento_create(request):
    if request.method == "POST":
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mantenimiento creado exitosamente.")
            # return redirect("agenda")
            return redirect("vehiculo_index", id=form.cleaned_data["vehiculo"].id)
    else:
        form = MantenimientoForm()

    return render(
        request,
        "mantenimiento_form.html",
        {
            "form": form,
        },
    )


# editar
def mantenimiento_edit(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    form = MantenimientoForm(request.POST or None, instance=mantenimiento)
    if form.is_valid():
        form.save()
        messages.success(request, "Mantenimiento actualizado exitosamente.")
        return redirect("vehiculo_index", id=form.cleaned_data["vehiculo"].id)
    return render(request, "mantenimiento_form.html", {"form": form})


# eliminar
@require_POST  # solo permite metodo POST
def mantenimiento_delete(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    vehiculo_id = mantenimiento.vehiculo.id
    mantenimiento.delete()
    messages.success(request, "Mantenimiento eliminado exitosamente.")
    return redirect("vehiculo_index", id=vehiculo_id)


# VAHICULOS


# pagina principal de vehiculo
def vehiculo_index(request, id):
    # vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo = get_object_or_404(
        Vehiculo.objects.prefetch_related("mantenimientos"), id=id
    )
    # calcular metricas OBD-II
    horas_motor = calcular_horas_motor(vehiculo)
    km_estimados = calcular_kilometros_estimados(vehiculo)
    rpm_alta_min = tiempo_rpm_alta(vehiculo, umbral=3000)
    temp_critica_min = tiempo_temperatura_critica(vehiculo, umbral=110)

    return render(
        request,
        "myvehiculo/vehiculoindex.html",
        {
            "vehiculo": vehiculo,
            "mantenimientos": vehiculo.mantenimientos.all(),
            "horas_motor": horas_motor,
            "km_estimados": km_estimados,
            "rpm_alta_min": rpm_alta_min,
            "temp_critica_min": temp_critica_min,
        },
    )


# crear vista vehiculo
def vehiculo_create(request):
    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo creado exitosamente.")
            return redirect("inicio")
    else:
        form = VehiculoForm()

    return render(
        request,
        "vehiculo_form_modal.html",
        {
            "form": form,
            "modo": "crear",
        },
    )


# editar vista vehiculo


def vehiculo_edit(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado exitosamente.")
            return redirect("vehiculo_index", id=vehiculo.pk)  # Primary Key
    else:

        form = VehiculoForm(instance=vehiculo)

    print("POST RECIBIDO en vehiculo_edit")
    print(request.POST)

    return render(
        request,
        "vehiculo_form_modal.html",
        {
            "form": form,
            "vehiculo": vehiculo,
            "modo": "editar",
        },
    )


# eliminar vista vehiculo
@require_POST
def vehiculo_delete(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo.delete()
    messages.success(request, "Vehículo eliminado exitosamente.")
    return redirect("inicio")


# vista de graficos OBD-II
def obd_charts_view(request):
    vehiculos = Vehiculo.objects.all().order_by("placa")
    return render(request, "myvehiculo/obd_charts.html", {"vehiculos": vehiculos})


# leer filtros
def _get_filters(request):
    vehiculo_id = request.GET.get("vehiculo_id")
    fi = parse_date(request.GET.get("fecha_inicio") or "")
    ff = parse_date(request.GET.get("fecha_fin") or "")

    qs = obddata.objects.all()

    if vehiculo_id:
        qs = qs.filter(vehiculo_id=vehiculo_id)

    if fi:
        qs = qs.filter(timestamp__date__gte=fi)  # mayor o igual que
    if ff:
        qs = qs.filter(timestamp__date__lte=ff)  # menor o igual que
    return qs


# Endpoint: serie temporal generica por promedio
def _serie_promedio(qs, field_name):
    data = (
        qs.annotate(t=TruncHour("timestamp"))
        .values("t")
        .annotate(valor=Avg(field_name))
        .order_by("t")
    )
    labels = [d["t"].strftime("%Y-%m-%d %H:%M") for d in data if d["t"]]
    values = [float(d["valor"]) if d["valor"] is not None else None for d in data]
    return labels, values


# API endpoint para datos de gráficos OBD-II
# engine_rpm
def api_rpm_promedio(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "engine_rpm")
    return JsonResponse({"labels": labels, "values": values})


# engine_temp_c
def api_temp_motor(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "engine_temp_c")
    return JsonResponse({"labels": labels, "values": values})


# vehicle_code(No grafico)
def api_vehicle_codes(request):
    qs = _get_filters(request)
    data = qs.values("vehicle_code").annotate(count=Count("id")).order_by("-count")
    codes = [d["vehicle_code"] for d in data]
    counts = [d["count"] for d in data]
    return JsonResponse({"codes": codes, "counts": counts})


# timestamp(revisar no grafico)
def api_registros_por_hora(request):
    qs = _get_filters(request)
    data = (
        qs.annotate(hour=TruncHour("timestamp"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )
    labels = [d["hour"].strftime("%Y-%m-%d %H:%M") for d in data if d["hour"]]
    values = [d["count"] for d in data]
    return JsonResponse({"labels": labels, "values": values})


# vehicle_speed_kph
def api_velocidad_promedio(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "vehicle_speed_kph")
    return JsonResponse({"labels": labels, "values": values})


# coolant_temp_c
def api_temp_refrigerante(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "coolant_temp_c")
    return JsonResponse({"labels": labels, "values": values})


# oil_pressure_psi
def api_presion_aceite(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "oil_pressure_psi")
    return JsonResponse({"labels": labels, "values": values})


# alertas
def api_alerts(request):
    qs = _get_filters(request).filter(engine_failure_imminent=True)
    data = (
        qs.annotate(t=TruncHour("timestamp"))
        .values("t")
        .annotate(total=Count("id"))
        .order_by("t")
    )
    labels = [d["t"].strftime("%Y-%m-%d %H:%M") for d in data if d["t"]]
    values = [int(d["total"]) for d in data]
    return JsonResponse({"labels": labels, "values": values})


# Dashboard por vehiculo
def vehiculo_dashboard(request, vehiculo_id):
    # vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    # obd vinculados por FK
    qs_fk = obddata.objects.filter(vehiculo=vehiculo)

    # obd por vehicle_code
    qs_code = obddata.objects.filter(vehicle_code=vehiculo.placa)

    # Usa el mejor queryset disponible
    qs = qs_fk if qs_fk.exists() else qs_code

    obd_count = qs.count()
    last_obd = qs.order_by("-timestamp").first()

    # Metricas(no guardan nada, solo calculan)
    # horas_motor = calcular_horas_motor(vehiculo)
    horas_motor = 0
    # km_estimados = calcular_kilometros_estimados(vehiculo)
    km_estimados = 0
    # rpm_alta_min = tiempo_rpm_alta(vehiculo, umbral=4000)
    rpm_alta_min = 0
    # temp_critica_min = tiempo_temperatura_critica(vehiculo, umbral=110)
    temp_critica_min = 0

    # recomendaciones persistentes
    rec_pendientes = []
    rec_atendidas = []
    # rec_pendientes = vehiculo.recomendaciones.filter(estado="Pendiente").order_by(
    #     "-fecha_creacion"
    # )
    # rec_atendidas = vehiculo.recomendaciones.filter(estado="Atendida").order_by(
    #     "-fecha_creacion"
    # )[:10]

    # context = {
    #     "vehiculo": vehiculo,
    #     "horas_motor": horas_motor,
    #     "km_estimados": km_estimados,
    #     "rpm_alta_min": rpm_alta_min,
    #     "temp_critica_min": temp_critica_min,
    #     "rec_pendientes": rec_pendientes,
    #     "rec_atendidas": rec_atendidas,
    # }
    context = {
        "vehiculo": vehiculo,
        "obd_count": obd_count,
        "last_obd": last_obd,
        "horas_motor": horas_motor,
        "km_estimados": km_estimados,
        "rpm_alta_min": rpm_alta_min,
        "temp_critica_min": temp_critica_min,
        "rec_pendientes": rec_pendientes,
        "rec_atendidas": rec_atendidas,
    }

    # mostrar contador y ultimo dato
    # obd_count = obddata.objects.filter(vehiculo=vehiculo).count()
    # last_obd = obddata.objects.filter(vehiculo=vehiculo).order_by("-timestamp").first()

    return render(request, "myvehiculo/_dashboard_content.html", context)


# “Analizar ahora” (ejecuta reglas y guarda)
def analizar_vehiculo_action(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)

    guardadas = analizar_vehiculo_y_guardar(vehiculo)

    if guardadas:
        messages.success(
            request,
            f"Análisis completado. Nuevas recomendaciones guardadas: {len(guardadas)}",
        )
    else:
        messages.info(
            request, "Análisis completado. No se generaron nuevas recomendaciones."
        )
    return redirect("vehiculo_dashboard", vehiculo_id=vehiculo.id)
