# Generated by Django 3.2.2 on 2021-06-22 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commander', '0012_activitycounter_donations'),
    ]

    operations = [
        migrations.AddField(
            model_name='crimetype',
            name='category',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
