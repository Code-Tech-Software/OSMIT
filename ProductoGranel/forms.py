from django import forms
from .models import ProductoGranel, CategoriaProducto, Proveedor


# "----------------------------------------------------------------------ENTADA"
class ProductoGranelForm(forms.ModelForm):
    class Meta:
        model = ProductoGranel
        fields = [
            'nombre',
            'categoria_producto',
            'stock',
            'stock_min',
            'unidad_medida',
            'costo',
            'tiempo_caducidad',
            'imagen',
            'proveedor',
            'estado',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'categoria_producto': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'stock_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: kg, lts, etc.'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'tiempo_caducidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'En días', 'min': 0}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductoGranelForm, self).__init__(*args, **kwargs)
        # Filtrar solo categorías con estado=True
        self.fields['categoria_producto'].queryset = CategoriaProducto.objects.filter(estado=True)
        # Filtrar solo proveedores con estado=True
        self.fields['proveedor'].queryset = Proveedor.objects.filter(estado=True)


# ----------------------------------------------------------SALIDA

from django import forms
from .models import SalidaGranel, DetalleSalidaGranel

DESTINO_CHOICES = [
    ('Produccion', 'Producción'),
    ('Venta', 'Venta'),
    ('Maestro', 'Maestro'),
    ('Mitsu', 'Mitsu'),
    ('Otros', 'Otros'),
]


class SalidaGranelForm(forms.ModelForm):
    destino = forms.ChoiceField(choices=DESTINO_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    nota = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}),
        required=False)

    class Meta:
        model = SalidaGranel
        fields = ['destino', 'nota']


class DetalleSalidaGranelForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0,
                                  widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(DetalleSalidaGranelForm, self).__init__(*args, **kwargs)
        self.fields['producto'].queryset = ProductoGranel.objects.filter(estado=True)


# -----------------------------------PEDIDO

from django import forms
from .models import PedidoProduccion


class PedidoProduccionForm(forms.ModelForm):
    class Meta:
        model = PedidoProduccion
        fields = ['nota']

        # Se asume que el estado queda por defecto en "pendiente" y el usuario se asigna en la vista.
        widgets = {
            'nota': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}),
        }


# ------------------DEVOLUCIONES#
from django import forms
from .models import DevolucionGranel


class DevolucionGranelForm(forms.ModelForm):
    class Meta:
        model = DevolucionGranel
        fields = ['nota']
        widgets = {
            'nota': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}),
        }


# ----------------------------CORTEEEE
from django import forms
from .models import CorteInventarioGranel


class CorteInventarioForm(forms.ModelForm):
    class Meta:
        model = CorteInventarioGranel
        fields = ['observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# -----------------------------------------CATEGORIAS DE PRODUCTOS

class CategoriaProductoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ['nombre', 'descripcion', 'imagen', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre de la categoría'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingrese una descripción'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ------------------------------------------------PROVEEDORES DE PRODUCTOS

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'correo', 'direccion', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre del proveedor'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el número de teléfono'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Ingrese el correo electrónico' }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ingrese la dirección'
            }),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
