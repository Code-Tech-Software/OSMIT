# Generated by Django 5.1.7 on 2025-06-22 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProductoGranel', '0006_alter_proveedor_correo_alter_proveedor_direccion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedidoproduccion',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en_produccion', 'En Producción'), ('finalizado', 'Finalizado'), ('rechazado', 'Rechazado')], default='pendiente', max_length=20),
        ),
    ]
