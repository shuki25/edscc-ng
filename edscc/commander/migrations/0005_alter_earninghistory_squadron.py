# Generated by Django 3.2.2 on 2021-05-08 18:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0003_auto_20210508_0311'),
        ('commander', '0004_alter_factionactivity_squadron'),
    ]

    operations = [
        migrations.AlterField(
            model_name='earninghistory',
            name='squadron',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='squadron.squadron'),
        ),
    ]