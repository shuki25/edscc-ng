# Generated by Django 3.2.2 on 2021-06-03 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_langcode_galnetnews_lang_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='galnetnews',
            name='image',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
