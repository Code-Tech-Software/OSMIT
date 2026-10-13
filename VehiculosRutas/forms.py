from django import forms

from ProductoTerminado.models import Vehiculo, Ruta, Cliente, ClienteDiasVisita
from datetime import date, timedelta
from django.forms import inlineformset_factory
from django.utils import timezone
from django.forms.models import BaseInlineFormSet


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
    def __init__(self, *args, **kwargs):
        super(RutaForm, self).__init__(*args, **kwargs)
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(estado=True)


#--------------------------------------------CLientes#


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'nombre_negocio', 'giro', 'tipo_exhibidor', 'direccion',
            'localidad', 'colonia', 'telefono', 'limite_credito',
            'saldo_adeudo', 'porcentaje_descuento', 'imagen',
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
            'limite_credito': forms.NumberInput(attrs={ 'class': 'form-control','step': '0.1','min': '0','placeholder': '0.00'}),
            'saldo_adeudo': forms.NumberInput(attrs={'class': 'form-control','step': '0.1','min': '0','placeholder': '0.00'}),
            'porcentaje_descuento': forms.NumberInput(attrs={'class': 'form-control','step': '1','min': '0','max': '100','placeholder': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.fields['ruta'].queryset = Ruta.objects.filter(estado=True)

#DIAS DE VISITA



class ClienteDiasVisitaForm(forms.ModelForm):

    semana_referencia = forms.ChoiceField(
        required=False,
        label='Semana de referencia',
        choices=(),
        widget=forms.Select(
            attrs={
                'class': 'form-control semana-referencia'
            }
        )
    )

    class Meta:
        model = ClienteDiasVisita

        fields = [
            'dia_semana',
            'orden',
            'frecuencia_semanas',
            'semana_referencia'
        ]

        widgets = {
            'dia_semana': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'orden': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0'
                }
            ),
            'frecuencia_semanas': forms.Select(
                attrs={
                    'class': 'form-control frecuencia-semanas'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        semanas = self.generar_semanas()

        referencia = (
            self.instance.semana_referencia
            if self.instance.pk
            else None
        )

        if referencia and referencia.isoformat() not in dict(semanas):
            semanas.append((
                referencia.isoformat(),
                self.etiqueta_semana(referencia)
            ))

        self.fields['semana_referencia'].choices = [
            ('', 'Seleccionar semana')
        ] + semanas

        if referencia:
            self.initial['semana_referencia'] = referencia.isoformat()

    @staticmethod
    def inicio_semana(fecha):
        return fecha - timedelta(
            days=(fecha.weekday() - 2) % 7
        )

    @staticmethod
    def etiqueta_semana(inicio):
        fin = inicio + timedelta(days=6)

        meses = [
            'ene', 'feb', 'mar', 'abr',
            'may', 'jun', 'jul', 'ago',
            'sep', 'oct', 'nov', 'dic'
        ]

        return (
            f"{inicio.day} {meses[inicio.month - 1]} {inicio.year}"
            f" - {fin.day} {meses[fin.month - 1]} {fin.year}"
        )

    @classmethod
    def generar_semanas(cls):
        actual = cls.inicio_semana(timezone.localdate())

        return [
            (
                inicio.isoformat(),
                cls.etiqueta_semana(inicio)
            )
            for i in range(-12, 27)
            for inicio in [
                actual + timedelta(weeks=i)
            ]
        ]

    def clean(self):
        cleaned_data = super().clean()

        frecuencia = cleaned_data.get('frecuencia_semanas')
        semana = cleaned_data.get('semana_referencia')
        orden = cleaned_data.get('orden')

        if orden is not None and orden < 0:
            self.add_error(
                'orden',
                'El orden no puede ser negativo.'
            )

        if frecuencia == 2:

            if not semana:
                self.add_error(
                    'semana_referencia',
                    'Selecciona una semana de referencia.'
                )

            else:
                referencia = date.fromisoformat(semana)

                if referencia.weekday() != 2:
                    self.add_error(
                        'semana_referencia',
                        'La semana debe comenzar en miércoles.'
                    )

                cleaned_data['semana_referencia'] = referencia

        else:
            cleaned_data['semana_referencia'] = None

        return cleaned_data


class BaseClienteDiasVisitaFormSet(BaseInlineFormSet):

    @staticmethod
    def hay_conflicto(datos_a, datos_b):
        """
        Determina si dos visitas con el mismo día y orden
        coinciden en alguna semana operativa.
        """

        if datos_a['dia'] != datos_b['dia']:
            return False

        if datos_a['orden'] != datos_b['orden']:
            return False

        frecuencia_a = datos_a['frecuencia']
        frecuencia_b = datos_b['frecuencia']

        referencia_a = datos_a['referencia']
        referencia_b = datos_b['referencia']

        # Una visita semanal coincide con cualquier semana.
        if frecuencia_a == 1 or frecuencia_b == 1:
            return True

        # Dos visitas quincenales.
        if referencia_a and referencia_b:

            semana_a = ClienteDiasVisitaForm.inicio_semana(
                referencia_a
            )

            semana_b = ClienteDiasVisitaForm.inicio_semana(
                referencia_b
            )

            diferencia = (semana_a - semana_b).days // 7

            return diferencia % 2 == 0

        # Si falta referencia, no permitir la coincidencia.
        return True

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        ruta = self.instance.ruta

        if not ruta:
            return

        # ==========================================
        # RECOPILAR VISITAS DEL FORMULARIO
        # ==========================================

        visitas_actuales = []
        ids_editados = set()

        for form in self.forms:

            if form.instance.pk:
                ids_editados.add(form.instance.pk)

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get('DELETE'):
                continue

            datos = form.cleaned_data

            dia = datos.get('dia_semana')
            orden = datos.get('orden')
            frecuencia = datos.get('frecuencia_semanas')
            referencia = datos.get('semana_referencia')

            if dia is None or orden is None:
                continue

            visitas_actuales.append({
                'form': form,
                'dia': dia,
                'orden': orden,
                'frecuencia': frecuencia,
                'referencia': referencia,
                'nombre': self.instance.nombre
            })

        # ==========================================
        # BUSCAR VISITAS EXISTENTES EN LA RUTA
        # ==========================================

        existentes = (
            ClienteDiasVisita.objects
            .filter(
                cliente__ruta=ruta,
                cliente__estado=True
            )
            .select_related('cliente')
        )

        # Excluir solamente los registros que forman
        # parte de esta edición, no todo el cliente.
        if ids_editados:
            existentes = existentes.exclude(
                pk__in=ids_editados
            )

        visitas_existentes = [
            {
                'dia': visita.dia_semana,
                'orden': visita.orden,
                'frecuencia': visita.frecuencia_semanas,
                'referencia': visita.semana_referencia,
                'nombre': visita.cliente.nombre
            }
            for visita in existentes
        ]

        errores = []

        # ==========================================
        # COMPARAR CONTRA LA BASE DE DATOS
        # ==========================================

        for actual in visitas_actuales:

            for existente in visitas_existentes:

                if self.hay_conflicto(actual, existente):

                    mensaje = (
                        f"El orden {actual['orden']} "
                        f"ya está ocupado el día "
                        f"{actual['dia']} por el cliente "
                        f"{existente['nombre']}."
                    )

                    actual['form'].add_error(
                        'orden',
                        mensaje
                    )

                    errores.append(mensaje)
                    break

        # ==========================================
        # COMPARAR DENTRO DEL MISMO FORMULARIO
        # ==========================================

        for i, actual in enumerate(visitas_actuales):

            for otro in visitas_actuales[i + 1:]:

                if self.hay_conflicto(actual, otro):

                    mensaje = (
                        f"El orden {actual['orden']} "
                        f"está repetido para el día "
                        f"{actual['dia']} "
                        f"dentro de este cliente."
                    )

                    otro['form'].add_error(
                        'orden',
                        mensaje
                    )

                    errores.append(mensaje)

        # ==========================================
        # IMPEDIR GUARDADO SI EXISTEN CONFLICTOS
        # ==========================================

        if errores:
            raise forms.ValidationError(
                'No se puede guardar el cliente porque '
                'existen órdenes de visita duplicados. '
                'Revisa los campos marcados.'
            )


ClienteDiasVisitaFormSet = inlineformset_factory(
    Cliente,
    ClienteDiasVisita,
    form=ClienteDiasVisitaForm,
    formset=BaseClienteDiasVisitaFormSet,
    extra=0,
    can_delete=True
)
