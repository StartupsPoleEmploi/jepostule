# Generated by Django 2.2 on 2019-05-27 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jepostulepipeline', '0007_auto_20190516_1103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobapplicationevent',
            name='name',
            field=models.CharField(choices=[('sent', "Envoyé à l'employeur"), ('confirmed', 'Confirmation envoyée au candidat'), ('forwarded-to-memo', 'Candidature transférée à Memo'), ('answered', 'Réponse envoyée au candidat')], db_index=True, max_length=32),
        ),
    ]
