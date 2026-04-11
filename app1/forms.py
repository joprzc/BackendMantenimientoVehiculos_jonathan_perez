from django import forms
from datetime import date
from .models import Mantenimiento, Vehiculo


# usar ModelForms
class MantenimientoForm(forms.ModelForm):
    class Meta:  # clase interna recomendado
        model = Mantenimiento
        # fields = ["vehiculo", "fecha", "descripcion", "estado"]
        fields = "__all__"


# formulario para vehiculo
class VehiculoForm(forms.ModelForm):
    anio = forms.TypedChoiceField(
        choices=[],
        coerce=int,
        empty_value=None,
        label="Año",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        anio_actual = date.today().year
        anio_minimo = 1980
        self.fields["anio"].choices = [
            (anio, anio) for anio in range(anio_actual + 1, anio_minimo - 1, -1)
        ]
        self.fields["anio"].widget.attrs.update(
            {
                "class": "form-select-sm",
                "style": "max-width: 150px;",
            }
        )

    class Meta:
        model = Vehiculo
        # fields = ["anio", "marca", "modelo", "placa", "imagen"]
        # fields = "__all__"
        exclude = [
            "usuario",
            "obd_code",
        ]  # no queremos que el usuario edite estos campos

        labels = {
            "anio": "Año",
        }


class WhatsappMaintenanceForm(forms.Form):
    phone = forms.CharField(label="WhatsApp", max_length=20)
    message = forms.CharField(label="Mensaje", widget=forms.Textarea, max_length=1000)

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "")
        if not phone.startswith("+") or not phone[1:].isdigit():
            raise forms.ValidationError(
                "Número de teléfono inválido. Debe comenzar con '+' seguido de dígitos."
            )
        return phone
