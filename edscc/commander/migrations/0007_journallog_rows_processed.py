# Generated by Django 3.2.2 on 2021-05-09 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commander', '0006_journallog_parser_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='journallog',
            name='rows_processed',
            field=models.IntegerField(null=True),
        ),
    ]
