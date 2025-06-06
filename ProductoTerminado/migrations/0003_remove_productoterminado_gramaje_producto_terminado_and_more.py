# Generated by Django 5.1.7 on 2025-03-24 18:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProductoTerminado', '0002_cliente_imagen_alter_gramajeproductoterminado_imagen_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productoterminado',
            name='gramaje_producto_terminado',
        ),
        migrations.RemoveField(
            model_name='productoterminado',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='productoterminado',
            name='stock_min',
        ),
        migrations.CreateModel(
            name='InventarioProductoTerminado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock', models.DecimalField(decimal_places=2, max_digits=10)),
                ('gramaje', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ProductoTerminado.gramajeproductoterminado')),
                ('producto_terminado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ProductoTerminado.productoterminado')),
            ],
        ),
    ]
