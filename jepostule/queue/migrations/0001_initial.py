# Generated by Django 2.1.2 on 2018-10-19 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DelayedMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('topic', models.CharField(db_index=True, max_length=64)),
                ('value', models.BinaryField(blank=True, null=True)),
                ('until', models.DateTimeField(db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FailedMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('topic', models.CharField(db_index=True, max_length=64)),
                ('value', models.BinaryField(blank=True, null=True)),
                ('status', models.CharField(choices=[('new', 'New'), ('archived', 'Archived')], db_index=True, default='new', max_length=32)),
                ('exception', models.CharField(blank=True, max_length=64)),
                ('traceback', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
