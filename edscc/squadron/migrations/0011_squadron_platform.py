# Generated by Django 3.2.2 on 2021-06-07 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0010_auto_20210607_0204'),
    ]

    operations = [
        migrations.AddField(
            model_name='squadron',
            name='platform',
            field=models.CharField(choices=[('PC', 'PC'), ('PS4', 'Playstation'), ('XBOX', 'XBox')], default='PC', max_length=4),
        ),
    ]
