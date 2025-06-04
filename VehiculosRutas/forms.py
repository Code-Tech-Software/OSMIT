from django import forms

from ProductoTerminado.models import Vehiculo, Ruta, Cliente, ClienteDiasVisita, VentaCliente, DetalleVentaCliente


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['marca', 'color', 'placa', 'kilometraje', 'ultimo_servicio', 'observaciones', 'imagen', 'estado']
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control'}),
            'ultimo_servicio': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input' }),
        }

    def __init__(self, *args, **kwargs):
        super(VehiculoForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.ultimo_servicio:
            self.fields['ultimo_servicio'].initial = self.instance.ultimo_servicio.strftime('%Y-%m-%d')




class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['nombre', 'descripcion', 'vehiculo', 'usuario', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la ruta'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'estado':  forms.CheckboxInput(attrs={'class': 'form-check-input' }),
        }



#--------------------------------------------CLientes#


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'nombre_negocio', 'giro', 'tipo_exhibidor', 'direccion',
            'localidad', 'colonia', 'telefono', 'credito', 'imagen',
            'observaciones', 'ruta', 'estado'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Nombre de la cliente'}),
            'nombre_negocio': forms.TextInput(attrs={'class': 'form-control'}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_exhibidor': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'colonia': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



#DIAS DE VISITA

class ClienteDiasVisitaForm(forms.Form):
    dias = forms.MultipleChoiceField(
        choices=ClienteDiasVisita.DIAS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Días de visita"
    )

#--------------------------------------------------------------------------DE AQUI PARA ABAJO SE VA A HACER UN DESMADRE
