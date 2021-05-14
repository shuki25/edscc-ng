# Generated by Django 3.2.2 on 2021-05-08 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commander', '0002_alter_activitycounter_squadron'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activitycounter',
            name='bodies_found',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='bounties_claimed',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='cg_participated',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='crimes_committed',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='efficiency_achieved',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='market_buy',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='market_sell',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='mining_refined',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='missions_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='saa_scan_completed',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='stolen_goods',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='activitycounter',
            name='systems_scanned',
            field=models.IntegerField(default=0),
        ),
    ]