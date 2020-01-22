# Generated by Django 2.2.5 on 2019-09-17 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jepostulepipeline', '0010_jobapplication_candidate_peam_access_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobapplicationevent',
            name='name',
            field=models.CharField(choices=[('sent', "Envoyé à l'employeur"), ('confirmed', 'Confirmation envoyée au candidat'), ('forwarded-to-memo', 'Candidature transférée à Memo'), ('forwarded-to-ami', "Candidature transférée à l'AMI"), ('answered', 'Réponse envoyée au candidat')], db_index=True, max_length=32),
        ),
    ]