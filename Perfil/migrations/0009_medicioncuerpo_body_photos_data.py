# Generated by Django 5.2.1 on 2025-06-04 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perfil', '0008_remove_usuario_estatura_remove_usuario_peso_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicioncuerpo',
            name='body_photos_data',
            field=models.TextField(blank=True, help_text='JSON array of base64 image data for body photos', null=True),
        ),
    ]
