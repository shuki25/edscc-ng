# Generated by Django 3.2.2 on 2021-06-04 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0006_auto_20210604_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='squadronroster',
            name='has_account',
            field=models.BooleanField(default=False),
        ),
    ]
