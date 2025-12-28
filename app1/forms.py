from django import forms
from .models import Mantenimiento, Vehiculo

# usar ModelForms
class MantenimientoForm(forms.ModelForm):
    class Meta: # clase interna recomendado
        model = Mantenimiento
        fields = ['fecha', 'descripcion', 'estado']

# formulario para vehiculo
class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['anio', 'marca', 'modelo', 'placa', 'imagen']