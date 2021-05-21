# Generated by Django 3.2.2 on 2021-05-20 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0003_auto_20210508_0311'),
    ]

    operations = [
        migrations.AddField(
            model_name='squadron',
            name='primary_language',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French'), ('de', 'German'), ('pt', 'Portuguese'), ('ru', 'Russian'), ('es', 'Spanish')], default='en', max_length=2),
        ),
    ]