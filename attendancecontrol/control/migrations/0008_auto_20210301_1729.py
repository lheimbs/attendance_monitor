# Generated by Django 3.1.7 on 2021-03-01 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0007_auto_20210301_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesstoken',
            name='token',
            field=models.CharField(editable=False, max_length=11, verbose_name='Access Token'),
        ),
    ]