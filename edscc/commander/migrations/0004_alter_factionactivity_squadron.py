# Generated by Django 3.2.2 on 2021-05-08 02:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0001_initial'),
        ('commander', '0003_auto_20210508_0054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factionactivity',
            name='squadron',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='squadron.squadron'),
        ),
    ]
