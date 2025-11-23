from django.shortcuts import render,HttpResponse,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url='login')  # evita que ingresemos directamente a la pagina inicio
def InicioPage(request):
    return render(request,'inicio.html')

def SignupPage(request):
    if request.method == 'POST':    # revisa si el formulario fue enviado
        # datos a obtener/enviados desde el formulario
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')
        # validar que la contraseña coincida
        if pass1!=pass2:
            return HttpResponse("Tu contraseña y la confirmación de contraseña no coinciden.")
        else:
             
            my_user=User.objects.create_user(uname,email,pass1)
            my_user.save()
            return redirect('login')
        # return HttpResponse("Usuario ha sido creado exitosamente")
        
        # print(uname, email,pass1,pass2)    
    print("Tu contraseña y la confirmación de contraseña no coinciden.")
    return render(request,'signup.html')    # muestra la pagina signup.html

def LoginPage(request):
    if request.method=='POST':  # verifico si el formulario fue enviado
        # lee los valores enviados desde el formulario
        username=request.POST.get('username')
        pass1=request.POST.get('pass')        
        # print(username,pass1)
        user=authenticate(request,username=username,password=pass1)
        if user is not None:
            login(request,user)
            return redirect('inicio')
        else:
            return HttpResponse("Usuario o clave es incorrecto")
    return render (request,'login.html')

def LogoutPage(request):
    logout(request)
    return redirect('login')
