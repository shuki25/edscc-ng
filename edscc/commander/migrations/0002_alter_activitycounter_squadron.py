# Generated by Django 3.2.2 on 2021-05-08 00:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0001_initial'),
        ('commander', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activitycounter',
            name='squadron',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='squadron.squadron'),
        ),
    ]
