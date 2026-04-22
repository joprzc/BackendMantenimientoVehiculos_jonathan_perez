import re
from django import forms
from datetime import date
from .models import Mantenimiento, Vehiculo, normalizar_placa


# usar ModelForms
class MantenimientoForm(forms.ModelForm):
    class Meta:  # clase interna recomendado
        model = Mantenimiento
        # fields = ["vehiculo", "fecha", "descripcion", "estado"]
        # fields = "__all__"
        fields = [
            "vehiculo",
            "descripcion",
            "fecha",
            "nombre_mecanico",
            "telefono_mecanico",
        ]

        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "nombre_mecanico": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del mecánico",
                }
            ),
            "telefono_mecanico": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "593999999999",
                }
            ),
        }

    def clean_telefono_mecanico(self):
        telefono = self.cleaned_data.get("telefono_mecanico", "")
        if not telefono:
            return telefono  # Permitir campo vacío

        telefono = telefono.strip().replace(" ", "").replace("-", "")
        if not telefono.startswith("+"):
            raise forms.ValidationError(
                "El teléfono debe incluir código de país. Ejemplo: +593999999999"
            )
        return telefono


# marcas de vehiculos en ecuador
MARCAS_ECUADOR = [
    ("", "Seleccione una marca"),
    ("Chevrolet", "Chevrolet"),
    ("Kia", "Kia"),
    ("Hyundai", "Hyundai"),
    ("Toyota", "Toyota"),
    ("Nissan", "Nissan"),
    ("Suzuki", "Suzuki"),
    ("Mazda", "Mazda"),
    ("Ford", "Ford"),
    ("Volkswagen", "Volkswagen"),
    ("Renault", "Renault"),
    ("Chery", "Chery"),
    ("Great Wall", "Great Wall"),
    ("JAC", "JAC"),
    ("DFSK", "DFSK"),
    ("BMW", "BMW"),
    ("Mercedes-Benz", "Mercedes-Benz"),
    ("Audi", "Audi"),
    ("Mitsubishi", "Mitsubishi"),
    ("Honda", "Honda"),
]

# estructura de modelos por marca
MODELOS_POR_MARCA = {
    "Chevrolet": ["Aveo", "Sail", "Onix", "D-Max", "Spark"],
    "Kia": ["Rio", "Sportage", "Picanto", "Cerato"],
    "Hyundai": ["Accent", "Tucson", "Elantra", "Santa Fe"],
    "Toyota": ["Corolla", "Hilux", "Fortuner", "Yaris"],
    "Nissan": ["Versa", "Sentra", "Frontier", "X-Trail"],
    "Suzuki": ["Swift", "Vitara", "Alto"],
    "Mazda": ["Mazda 2", "Mazda 3", "CX-5"],
    "Ford": ["Fiesta", "Explorer", "Ranger"],
    "Volkswagen": ["Gol", "Jetta", "Amarok"],
    "Renault": ["Logan", "Sandero", "Duster"],
    "Chery": ["Tiggo 2", "Tiggo 4"],
    "Great Wall": ["Wingle", "Haval H2"],
    "JAC": ["S2", "S3", "T6"],
    "DFSK": ["Glory 560", "K01"],
    "BMW": ["X1", "X3", "Serie 3"],
    "Mercedes-Benz": ["Clase C", "GLA"],
    "Audi": ["A3", "Q5"],
    "Mitsubishi": ["L200", "Outlander"],
    "Honda": ["Civic", "CR-V"],
}


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
        self.fields["placa"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "PCB-5514",
                "maxlength": 8,
                "autocapitalize": "characters",
                "autocomplete": "off",
            }
        )

        marca_actual = None
        if self.is_bound:
            marca_actual = self.data.get("marca")
        elif self.instance and self.instance.pk:
            marca_actual = self.instance.marca

        modelos = MODELOS_POR_MARCA.get(marca_actual, [])
        self.fields["modelo"].choices = [
            ("", "Seleccione un modelo"),
            *[(modelo, modelo) for modelo in modelos],
        ]

    def clean_placa(self):
        placa = normalizar_placa(self.cleaned_data.get("placa", ""))
        if not re.fullmatch(r"[A-Z]{3}-\d{4}", placa or ""):
            raise forms.ValidationError(
                "La placa debe tener el formato ABC-1234."
            )
        return placa

    # elegir marca de una lista predefinida
    marca = forms.ChoiceField(
        choices=MARCAS_ECUADOR,
        required=True,
        label="Marca",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    modelo = forms.ChoiceField(
        choices=[("", "Seleccione un modelo")],
        required=True,
        label="Modelo",
        widget=forms.Select(attrs={"class": "form-select"}),
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
        widgets = {}


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
