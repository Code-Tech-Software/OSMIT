from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,PasswordChangeForm
from .models import Usuario, TurnoUsuario, Rol, Turno
from django.utils import timezone

class RegistroForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',

        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',

        })
    )
    telefono = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',

        })
    )
    direccion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,

        })
    )
    foto = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
             'class': 'form-control',
                'accept': 'image/*'
        })
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.filter(estado=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'telefono', 'rol', 'direccion', 'foto']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'foto']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }



class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['nombre', 'descripcion','estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'off'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }



class TurnoUsuarioForm(forms.ModelForm):
    class Meta:
        model = TurnoUsuario
        fields = ['usuario', 'turno', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione un usuario'
            }),
            'turno': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione un turno'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo turnos activos
        self.fields['turno'].queryset = Turno.objects.filter(estado=True)



class TurnoUsuarioFormEditar(forms.ModelForm):
    class Meta:
        model = TurnoUsuario
        fields = ['usuario', 'turno', 'fecha_inicio', 'fecha_fin','estado']
        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione un usuario'
            }),
            'turno': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione un turno'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                local_fecha_inicio = timezone.localtime(self.instance.fecha_inicio)
                self.initial['fecha_inicio'] = local_fecha_inicio.strftime('%Y-%m-%dT%H:%M')
            if self.instance.fecha_fin:
                local_fecha_fin = timezone.localtime(self.instance.fecha_fin)
                self.initial['fecha_fin'] = local_fecha_fin.strftime('%Y-%m-%dT%H:%M')

        # Filtrar solo turnos activos
        self.fields['turno'].queryset = Turno.objects.filter(estado=True)


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)

        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            #'placeholder': 'Contraseña actual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            #'placeholder': 'Nueva contraseña'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            #'placeholder': 'Confirmar la nueva contraseña'
        })
