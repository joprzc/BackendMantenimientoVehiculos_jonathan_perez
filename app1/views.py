from ast import If
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Mantenimiento, Vehiculo
from .forms import MantenimientoForm, VehiculoForm
from django.views.decorators.http import require_POST  # bloquea metodos no permitidos
from django.contrib import messages  # para mensajes flash


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
    mantenimento = Mantenimiento.objects.all()
    return render(request, "agenda.html", {"mantenimento": mantenimento})


# crear
def mantenimiento_create(request):
    form = MantenimientoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Mantenimiento creado exitosamente.")
        return redirect("agenda")  # redirigir a la vista agenda
    # Carga el template mantenimiento_form.html
    return render(request, "mantenimiento_form.html", {"form": form})


# editar
def mantenimiento_edit(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    form = MantenimientoForm(request.POST or None, instance=mantenimiento)
    if form.is_valid():
        form.save()
        messages.success(request, "Mantenimiento actualizado exitosamente.")
        return redirect("agenda")
    return render(request, "mantenimiento_form.html", {"form": form})


# eliminar
@require_POST  # solo permite metodo POST
def mantenimiento_delete(request, id):
    mantenimiento = get_object_or_404(Mantenimiento, id=id)
    mantenimiento.delete()
    return redirect("agenda")


# VAHICULOS


# pagina principal de vehiculo
def vehiculo_index(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    return render(request, "myvehiculo/vehiculoindex.html", {"vehiculo": vehiculo})


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
