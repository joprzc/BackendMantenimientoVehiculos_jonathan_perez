from ast import If
from operator import ge
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Mantenimiento, Vehiculo, obddata, RecomendacionMantenimiento
from .forms import MantenimientoForm, VehiculoForm, MODELOS_POR_MARCA
from django.views.decorators.http import require_POST  # bloquea metodos no permitidos
from django.contrib import messages  # para mensajes flash
from django.utils.dateparse import parse_date
from datetime import date, timedelta
from django.db.models import Avg, Count
from django.db.models.functions import TruncHour
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# vistas del dashboard de OBD-II
from app1.models import obddata, Vehiculo, RecomendacionMantenimiento
from app1.services.obd_metrics import (
    calcular_horas_motor,
    calcular_kilometros_estimados,
    tiempo_rpm_alta,
    tiempo_temperatura_critica,
)
from app1.services.maintenance_analyzer import analizar_vehiculo_y_guardar

# graficas adminLTE
from app1.services.obd_chart_service import get_obd_chart_data

# graficas echart
from app1.services.dashboard_gauge_service import get_vehicle_gauge_data

# from app1.services.obd_gauge_service import get_gauge_data

# whatsapp
from urllib.parse import quote
from app1.forms import WhatsappMaintenanceForm
from .services.whatsapp_service import send_whatsapp

# PDF report
from app1.services.report_service import generar_pdf_recomendaciones
from django.template.loader import get_template
from xhtml2pdf import pisa


# Create your views here.
# @api_view(["GET"])
# @permission_classes([AllowAny])
@login_required(
    login_url="login"
)  # evita que ingresemos directamente a la pagina inicio
def InicioPage(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # listar vehiculos
    # vehiculos = Vehiculo.objects.all()
    vehiculos = Vehiculo.objects.filter(usuario=request.user)
    form = VehiculoForm()

    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            # form.save()
            vehiculo = form.save(commit=False)
            vehiculo.usuario = request.user  # asigna el usuario actual al vehículo
            vehiculo.save()
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

        # temporal
        print("DEBUG username:", username)
        print("DEBUG pass enviada:", bool(pass1))

        # print(username,pass1)
        user = authenticate(request, username=username, password=pass1)
        print("DEBUG user autenticado:", user)

        if user is not None:
            login(request, user)
            return redirect("inicio")
        else:
            messages.error(request, "Usuario o clave es incorrecto")
            # return redirect("login")
            return render(request, "login.html")

    return render(request, "login.html")


def LogoutPage(request):
    logout(request)
    return redirect("login")


# CRUD
# agenda de mantenimiento
# listar
def agenda(request):
    mantenimientos = Mantenimiento.objects.select_related("vehiculo").all()
    # return render(
    #     request,
    #     "agenda.html",
    #     {
    #         "mantenimientos": mantenimientos,
    #     },
    # )
    return render(request, "myvehiculo/agenda.html", {"mantenimientos": mantenimientos})


# crear
@login_required(login_url="login")
def mantenimiento_create(request):
    next_url = request.GET.get("next") or request.POST.get("next") or reverse("agenda")

    if request.method == "POST":
        form = MantenimientoForm(request.POST)

        if form.is_valid():
            mantenimiento = form.save()
            messages.success(request, "Mantenimiento creado exitosamente.")

            # redirect_url = request.POST.get("next") or reverse(
            #     "vehiculo_index", args=[mantenimiento.vehiculo.id]
            # )

            return redirect(redirect_url)

    else:
        form = MantenimientoForm()

        vehiculo_id = request.GET.get("vehiculo_id")
        if vehiculo_id:
            form.fields["vehiculo"].initial = vehiculo_id

    return render(
        request,
        "mantenimiento_form.html",
        {
            "form": form,
            "cancel_url": next_url,
            "next": next_url,
        },
    )


# editar
def mantenimiento_edit(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    form = MantenimientoForm(request.POST or None, instance=mantenimiento)
    if form.is_valid():
        form.save()
        messages.success(request, "Mantenimiento actualizado exitosamente.")
        # return redirect("vehiculo_index", id=form.cleaned_data["vehiculo"].id)
        return redirect("vehiculo_index", id=mantenimiento.vehiculo.id)
    return render(request, "mantenimiento_form.html", {"form": form})


# eliminar
@require_POST  # solo permite metodo POST
def mantenimiento_delete(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    vehiculo_id = mantenimiento.vehiculo.id
    mantenimiento.delete()
    messages.success(request, "Mantenimiento eliminado exitosamente.")
    return redirect("vehiculo_index", id=vehiculo_id)


# Notificar mantenimiento por email
@login_required(login_url="login")
@require_POST
def mantenimiento_send_notification(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    # vehiculo = mantenimiento.vehiculo

    # destinatario = request.user.email
    # destinatario = mantenimiento.vehiculo.usuario.email
    destinatario = ""
    if mantenimiento.vehiculo.usuario:
        destinatario = mantenimiento.vehiculo.usuario.email

    if not destinatario:
        messages.error(
            request,
            "Tu usuario no tiene un correo registrado. Actualiza tu email para enviar notificaciones.",
        )
        # return redirect("vehiculo_index", id=vehiculo.id)
        return redirect("vehiculo_index", id=mantenimiento.vehiculo.id)

    asunto = f"Recordatorio de mantenimiento - {Vehiculo}"
    mensaje = (
        "Se ha generado una notificación de mantenimiento para el siguiente vehículo:\n\n"
        f"Vehículo: {Vehiculo}\n"
        f"Fecha: {mantenimiento.fecha}\n"
        f"Descripción: {mantenimiento.descripcion}\n"
        f"Estado: {mantenimiento.estado}\n"
    )

    remitente = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    try:
        send_mail(
            # subject=asunto,
            # message=mensaje,
            # from_email=remitente,
            # recipient_list=[destinatario],
            # fail_silently=False,
            subject="Recordatorio de mantenimiento",
            # message=f"Tienes un mantenimiento programado:\n\n{mantenimiento.descripcion}\nFecha: {mantenimiento.fecha}",
            message=(
                f"Tienes un mantenimiento programado.\n\n"
                f"Vehículo: {mantenimiento.vehiculo}\n"
                f"Descripción: {mantenimiento.descripcion}\n"
                f"Fecha: {mantenimiento.fecha}"
            ),
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            # recipient_list=["jonathan.przc@gmail.com"],  # prueba contigo mismo
            recipient_list=[destinatario],
            fail_silently=False,
        )
        print("EMAIL ENVIADO OK")
        print("DEBUG destinatario:", destinatario)
        # messages.success(
        #     request, f"Notificación enviada correctamente a {destinatario}."
        # )
    except Exception as e:
        print("ERROR EMAIL:", e)
        messages.error(request, f"No se pudo enviar el correo: {e}")

    # return redirect("vehiculo_index", id=vehiculo.id)
    return redirect("vehiculo_index", id=mantenimiento.vehiculo.id)


# notificaciones a whatsapp
def mantenimiento_notify_whatsapp(request, mantenimiento_id):
    mantenimiento = get_object_or_404(Mantenimiento, id=mantenimiento_id)

    telefono = (mantenimiento.telefono_mecanico or "").strip()

    if not telefono:
        messages.error(request, "Este mantenimiento no tiene teléfono del mecánico.")
        return redirect(request.META.get("HTTP_REFERER", "mantenimiento_list"))
    telefono_limpio = telefono.replace(" ", "").replace("+", "")

    mensaje = (
        f"Hola {mantenimiento.nombre_mecanico or 'mecanico'}, "
        f"se ha agendado el mantenimiento del vehículo {mantenimiento.vehiculo.placa}. "
        f"Detalle: {mantenimiento.descripcion}."
        f"Fecha programada: {mantenimiento.fecha.strftime('%d/%m/%Y')}."
    )

    whatsapp_url = f"https://wa.me/{telefono_limpio}?text={quote(mensaje)}"
    return redirect(whatsapp_url)


# VAHICULOS
# pagina principal de vehiculo
@login_required(login_url="login")
def vehiculo_index(request, id):
    # vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo = get_object_or_404(
        Vehiculo.objects.prefetch_related("mantenimientos"), pk=id, usuario=request.user
    )

    # calcular metricas OBD-II
    horas_motor = calcular_horas_motor(vehiculo)
    km_estimados = calcular_kilometros_estimados(vehiculo)
    rpm_alta_min = tiempo_rpm_alta(vehiculo, umbral=3000)
    temp_critica_min = tiempo_temperatura_critica(vehiculo, umbral=100)

    # Contexto base
    context = {
        "vehiculo": vehiculo,
        "mantenimientos": vehiculo.mantenimientos.all(),
        "mantenimiento_form": MantenimientoForm(initial={"vehiculo": vehiculo}),
        "horas_motor": horas_motor,
        "km_estimados": km_estimados,
        "rpm_alta_min": rpm_alta_min,
        "temp_critica_min": temp_critica_min,
    }

    # mismo contexto para _dashboard_content.html
    context.update(build_dashboard_context(vehiculo))
    context["obd_code"] = getattr(vehiculo, "obd_code", None) or vehiculo.placa
    # context["obd_code"] = vehiculo.obd_code or vehiculo.placa
    # context["selected_obd_port"] = request.session.get("obd_port")

    return render(request, "myvehiculo/vehiculoindex.html", context)


# vista whatsapp
@login_required(login_url="login")
@require_POST
def vehiculo_notify_whatsapp(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, usuario=request.user)
    # if request.method != "POST":
    #     return HttpResponseNotAllowed(["POST"])

    form = WhatsappMaintenanceForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Corrige el número o el mensaje de WhatsApp.")
        return redirect("vehiculo_index", id=vehiculo_id)

    to_number = form.cleaned_data["phone"]
    message = form.cleaned_data["message"]
    ok, detail = send_whatsapp(to_number, message)
    if ok:
        messages.success(request, "Notificación enviada")
    else:
        messages.error(request, f"No se envió: {detail}")
    return redirect("vehiculo_index", id=vehiculo_id)


# crear vista vehiculo
def vehiculo_create(request):
    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            # form.save()
            vehiculo = form.save(commit=False)
            vehiculo.usuario = request.user  # asigna el usuario actual al vehículo
            vehiculo.save()
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
            "MODELOS_POR_MARCA": MODELOS_POR_MARCA,
        },
    )


# editar vista vehiculo


def vehiculo_edit(request, id):
    # vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo = get_object_or_404(Vehiculo, id=id, usuario=request.user)
    if request.method == "POST":
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            # form.save()
            vehiculo_editado = form.save(commit=False)
            vehiculo_editado.usuario = request.user  # asegura que el usuario no cambie
            vehiculo_editado.save()
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
            "MODELOS_POR_MARCA": MODELOS_POR_MARCA,
        },
    )


# eliminar vista vehiculo
@require_POST
def vehiculo_delete(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo.delete()
    messages.success(request, "Vehículo eliminado exitosamente.")
    return redirect("inicio")


# graficas echarts
# @login_required
@login_required(login_url="login")
def api_vehicle_gauges(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    data = get_vehicle_gauge_data(vehiculo)
    return JsonResponse(data)


# vista de graficos OBD-II
def obd_charts_view(request):
    vehiculos = Vehiculo.objects.all().order_by("placa")

    # Rango por defecto: última semana hasta hoy
    today = date.today()
    default_end = today
    default_start = today - timedelta(days=7)

    return render(
        request,
        "myvehiculo/obd_charts.html",
        {
            "vehiculos": vehiculos,
            "default_start_str": default_start.isoformat(),
            "default_end_str": default_end.isoformat(),
        },
    )


# graficos adminLTE
def obd_chart_data(request):
    vehiculo_id = request.GET.get("vehiculo")
    fecha_inicio = request.GET.get("desde")
    fecha_fin = request.GET.get("hasta")

    data = get_obd_chart_data(vehiculo_id, fecha_inicio, fecha_fin)
    return JsonResponse(data)


# leer filtros
def _get_filters(request):
    # vehiculo_id = request.GET.get("vehiculo_id")
    vehiculo_id = (
        request.GET.get("vehiculo_id")
        or request.GET.get("vehiculo")
        or request.GET.get("vehiculoId")
    )
    fi = parse_date(request.GET.get("fecha_inicio") or "")
    ff = parse_date(request.GET.get("fecha_fin") or "")

    # Rango por defecto: última semana hasta hoy si no se envían fechas
    if not fi and not ff:
        ff = date.today()
        fi = ff - timedelta(days=30)
    else:
        # Evita traer registros futuros si llega una fecha_fin posterior a hoy
        today = date.today()
        if ff and ff > today:
            ff = today

    # Base queryset
    qs = obddata.objects.all()

    # Filtro por vehículo: primero por FK, y si no hay datos, por vehicle_code (placa)
    if vehiculo_id:
        qs_fk = qs.filter(vehiculo_id=vehiculo_id)

        if qs_fk.exists():
            qs = qs_fk
        else:
            # Fallback: muchos datasets OBD vienen solo con vehicle_code
            vehiculo = Vehiculo.objects.filter(pk=vehiculo_id).only("placa").first()
            if vehiculo and vehiculo.placa:
                qs = qs.filter(vehicle_code=vehiculo.placa)
            else:
                qs = qs.none()

    # Filtros por fecha (aplican al queryset ya seleccionado)
    if fi:
        qs = qs.filter(timestamp__date__gte=fi)  # mayor o igual que
    if ff:
        qs = qs.filter(timestamp__date__lte=ff)  # menor o igual que

    # si el rango filtrado quedo vacío, mostrar ultimos 200 registros
    if not qs.exists():
        base = obddata.objects.all()
        if vehiculo_id:
            base_fk = base.filter(vehiculo_id=vehiculo_id)
            if base_fk.exists():
                base = base_fk
            else:
                vehiculo = Vehiculo.objects.filter(pk=vehiculo_id).only("placa").first()
                if vehiculo and vehiculo.placa:
                    base = base.filter(vehicle_code=vehiculo.placa)
        qs = base.order_by("-timestamp")[:200]

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


@login_required(login_url="login")
# API endpoint para datos de gráficos OBD-II
# engine_rpm
def api_rpm_promedio(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "engine_rpm")
    return JsonResponse({"labels": labels, "values": values})


# @login_required(login_url="login")
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


@login_required(login_url="login")
# vehicle_speed_kph
def api_velocidad_promedio(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "vehicle_speed_kph")
    return JsonResponse({"labels": labels, "values": values})


# @login_required(login_url="login")
# coolant_temp_c
def api_temp_refrigerante(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "coolant_temp_c")
    return JsonResponse({"labels": labels, "values": values})


# @login_required(login_url="login")
# oil_pressure_psi
def api_presion_aceite(request):
    qs = _get_filters(request)
    labels, values = _serie_promedio(qs, "oil_pressure_psi")
    return JsonResponse({"labels": labels, "values": values})


@login_required(login_url="login")
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
    context = {"vehiculo": vehiculo}
    context.update(build_dashboard_context(vehiculo))

    return render(request, "myvehiculo/_dashboard_content.html", context)


# funcion Helper para renderizar el dashboard
def build_dashboard_context(vehiculo):
    """
    Arma el contexto de métricas OBD + recomendaciones para un vehículo.
    Se reutiliza en:
      - vehiculo_dashboard (URL /dashboard/)
      - vehiculoindex.html (pestaña Dashboard)
    """
    # OBD vinculados por FK
    qs_fk = obddata.objects.filter(vehiculo=vehiculo)

    # OBD por vehicle_code (placa)
    qs_code = obddata.objects.filter(vehicle_code=vehiculo.placa)

    # Usa el mejor queryset disponible
    qs = qs_fk if qs_fk.exists() else qs_code

    obd_count = qs.count()
    last_obd = qs.order_by("-timestamp").first()

    # Métricas OBD-II (no guardan nada, solo calculan en base al histórico)
    horas_motor = calcular_horas_motor(vehiculo)
    km_estimados = calcular_kilometros_estimados(vehiculo)
    rpm_alta_min = tiempo_rpm_alta(vehiculo, umbral=3000)
    temp_critica_min = tiempo_temperatura_critica(vehiculo, umbral=115)

    # Recomendaciones persistentes asociadas al vehículo
    # Mientras tanto, consideramos "pendiente" todo lo que NO está Atendida
    # rec_atendidas = vehiculo.recomendaciones.filter(estado="Atendida").order_by(
    #     "-fecha_creacion"
    # )[:10]
    # rec_pendientes = vehiculo.recomendaciones.exclude(estado="Atendida").order_by(
    #     "-fecha_creacion"
    # )
    rec_pendientes = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo,
        estado="pendiente",
    ).order_by("-fecha_creacion")
    rec_atendidas = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo,
        estado="atendido",
    ).order_by("-fecha_creacion")[:10]

    return {
        "obd_count": obd_count,
        "last_obd": last_obd,
        "horas_motor": horas_motor,
        "km_estimados": km_estimados,
        "rpm_alta_min": rpm_alta_min,
        "temp_critica_min": temp_critica_min,
        "rec_pendientes": rec_pendientes,
        "rec_atendidas": rec_atendidas,
    }


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
        # return redirect("vehiculo_dashboard", vehiculo_id=vehiculo.id)
    return redirect("vehiculo_index", id=vehiculo.id)


# reportes PDF
def reporte_recomendaciones_pdf(request, vehiculo_id):

    vehiculo = Vehiculo.objects.get(id=vehiculo_id)

    recomendaciones = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo
    ).order_by("-fecha_creacion")

    pdf = generar_pdf_recomendaciones(vehiculo, recomendaciones)

    response = HttpResponse(pdf, content_type="application/pdf")

    filename = f"reporte_{vehiculo.placa}.pdf"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


# vistas del pdf
def reporte_recomendaciones_pdf(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)

    recomendaciones = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo
    ).order_by("-fecha_creacion")

    total_recomendaciones = recomendaciones.count()
    pendientes = recomendaciones.filter(estado="pendiente").count()
    atendidas = recomendaciones.filter(estado="atendido").count()
    criticas = recomendaciones.filter(severidad="critica").count()

    template = get_template("reportes/reporte_recomendaciones_pdf.html")

    context = {
        "vehiculo": vehiculo,
        "recomendaciones": recomendaciones,
        "total_recomendaciones": total_recomendaciones,
        "pendientes": pendientes,
        "atendidas": atendidas,
        "criticas": criticas,
    }

    html = template.render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="reporte_recomendaciones_{vehiculo.placa}.pdf"'
    )

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error al generar el PDF", status=500)

    return response
