# forms.py
from django import forms
from .models import MiniBodega

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