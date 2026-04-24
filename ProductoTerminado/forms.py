from django import forms

from ProductoGranel.models import CategoriaProducto
from .models import ProductoTerminado, PresentacionProductoTerminado, ProductoVariacion
from django import forms
from .models import SalidaPTerminado
from django import forms
from django.forms.models import BaseInlineFormSet

from django import forms
from django.forms.models import BaseInlineFormSet
from django import forms
from .models import ProductoVariacion


class ProductoTerminadoForm(forms.ModelForm):
    class Meta:
        model = ProductoTerminado
        fields = ['nombre', 'categoria_producto', 'imagen', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'categoria_producto': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria_producto'].queryset = CategoriaProducto.objects.filter(estado=True)



class ProductoVariacionForm(forms.ModelForm):
    class Meta:
        model = ProductoVariacion
        # ELIMINADO 'producto' porque es manejado por el inlineformset_factory
        fields = [
            'presentacion',
            'codigo_barras',
            'costo',
            'precio',
            'stock',
            'stock_min'
        ]
        widgets = {
            'presentacion': forms.Select(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 750123456789'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_min': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['presentacion'].queryset = PresentacionProductoTerminado.objects.filter(estado=True)


class ProductoVariacionBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        presentaciones_registradas = []
        codigos_registrados = []

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            presentacion = form.cleaned_data.get('presentacion')
            codigo_barras = form.cleaned_data.get('codigo_barras')

            # 1. Validar que la presentación no se repita en este mismo producto
            if presentacion:
                if presentacion in presentaciones_registradas:
                    raise forms.ValidationError(
                        f"Has duplicado la presentación: {presentacion}. "
                        "Cada variación debe tener una presentación única."
                    )
                presentaciones_registradas.append(presentacion)

            # 2. Validar que no envíen el mismo código de barras en dos variaciones distintas al mismo tiempo
            if codigo_barras:
                if codigo_barras in codigos_registrados:
                    raise forms.ValidationError(
                        f"El código de barras '{codigo_barras}' está duplicado en las variaciones que intentas guardar."
                    )
                codigos_registrados.append(codigo_barras)


class EntradaForm(forms.Form):
    nota = forms.CharField(widget=forms.Textarea, required=False, label="Nota de la entrada")






































# ---------------------------


class SalidaForm(forms.ModelForm):
    class Meta:
        model = SalidaPTerminado
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




# ProductoTerminado/forms.py
from django import forms



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


