# Generated by Django 3.2.2 on 2021-06-18 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commander', '0011_alter_earninghistory_earned_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitycounter',
            name='donations',
            field=models.IntegerField(default=0),
        ),
    ]
