# Generated by Django 3.2.2 on 2021-06-23 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('squadron', '0019_leaderboard'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaderboard',
            name='platform',
            field=models.CharField(db_index=True, default='PC', max_length=4),
            preserve_default=False,
        ),
    ]
