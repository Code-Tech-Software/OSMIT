# Generated by Django 5.1.7 on 2025-05-04 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProductoTerminado', '0013_alter_concentradopedidos_estado_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corteinventariopterminado',
            name='observaciones',
            field=models.TextField(blank=True, null=True),
        ),
    ]
