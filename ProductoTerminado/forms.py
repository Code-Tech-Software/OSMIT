from django import forms

from ProductoGranel.models import CategoriaProducto
from .models import ProductoTerminado, PresentacionProductoTerminado, GramajeProductoTerminado


class ProductoTerminadoForm(forms.ModelForm):
    class Meta:
        model = ProductoTerminado
        fields = [
            'nombre', 'costo', 'precio', 'categoria_producto', 'stock', 'stock_min',
            'presentacion_producto_terminado', 'gramaje_producto_terminado', 'imagen', 'estado'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'categoria_producto': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'stock_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'presentacion_producto_terminado': forms.Select(attrs={'class': 'form-control'}),
            'gramaje_producto_terminado': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductoTerminadoForm, self).__init__(*args, **kwargs)
        self.fields['categoria_producto'].queryset = CategoriaProducto.objects.filter(estado=True)
        self.fields['presentacion_producto_terminado'].queryset = PresentacionProductoTerminado.objects.filter(estado=True)
        self.fields['gramaje_producto_terminado'].queryset = GramajeProductoTerminado.objects.filter(estado=True)


# Formulario para registrar entradas generales.
# Se utilizará un campo para la nota y luego se procesan de forma dinámica los productos.
class EntradaForm(forms.Form):
    nota = forms.CharField(widget=forms.Textarea, required=False, label="Nota de la entrada")


from django import forms
from .models import SalidaPTerminado


class SalidaForm(forms.ModelForm):
    class Meta:
        model = SalidaPTerminado
        # Excluimos fecha_salida y usuario porque se asignan en la vista
        fields = ['ruta', 'destino', 'nota']

        widgets = {

            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'destino': forms.Select(attrs={'class': 'form-control'}),
            'nota': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles adicionales (opcional)...'
            }),
        }


# ---------------------------

# ProductoTerminado/forms.py
from django import forms
from .models import CorteInventarioPTerminado


class CorteInventarioPTerminadoForm(forms.ModelForm):
    class Meta:
        model = CorteInventarioPTerminado
        fields = ['observaciones']
        widgets = {

            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# Presentacion de producto terminado


class PresentacionProductoTerminadoForm(forms.ModelForm):
    class Meta:
        model = PresentacionProductoTerminado
        fields = ['nombre', 'descripcion', 'imagen', 'estado']
        widgets = {
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre de la presentación'}),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingrese una descripción'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GramajeProductoTerminadoForm(forms.ModelForm):
    class Meta:
        model = GramajeProductoTerminado
        fields = ['nombre', 'imagen', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre del gramaje'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
