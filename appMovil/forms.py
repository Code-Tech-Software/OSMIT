# forms.py
from pyclbr import Class

from django import forms
from .models import Dispositivo, MiniBodega

class MiniBodegaForm(forms.ModelForm):
    class Meta:
        model = MiniBodega
        fields = ['ruta', 'fecha', 'usuario', 'vehiculo', 'estado']
        widgets = {
            'ruta': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }


from django import forms
from .models import Usuario
class FiltroVentasForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Fecha inicial'
        })
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Fecha final'
        })
    )

    repartidor = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(
            rol__nombre='Repartidor',
            rol__estado=True,
            is_active=True
        ),
        required=False,
        empty_label="Todos los repartidores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CargarCSVForm(forms.Form):
    archivo_csv = forms.FileField(
        label="Selecciona tu archivo CSV de clientes",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

from django import forms
# Asegúrate de importar el modelo Usuario desde donde lo tengas definido
from .models import Usuario

class FiltroDevolucionesForm(forms.Form):

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control d-inline-block w-auto'
        }),
        label='Desde'
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control d-inline-block w-auto'
        }),
        label='Hasta'
    )

    repartidor = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(
            rol__nombre='Repartidor',
            rol__estado=True,
            is_active=True
        ),
        required=False,
        empty_label="Todos los repartidores",
        widget=forms.Select(
            attrs={'class': 'form-select d-inline-block w-auto'}
        )
    )


class DispositivoForm(forms.ModelForm):
    class Meta:
        model = Dispositivo
        fields = [
            "codigo",
            "repartidor",
            "activo",
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej. OSMIT-001",
            }),
            "repartidor": forms.Select(attrs={
                "class": "form-select",
            }),
            "activo": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }