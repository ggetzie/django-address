# Generated by Django 2.0 on 2017-12-11 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0013_auto_20171210_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='raw',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
