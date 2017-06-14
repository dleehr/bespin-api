# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-24 19:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_ddsusercredential_dds_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobquestion',
            name='data_type',
            field=models.CharField(choices=[('string', 'String'), ('int', 'Integer'), ('File', 'File'), ('Directory', 'Directory'), ('double', 'Double')], help_text='Determines how answer is formatted in CWL input json.', max_length=30),
        ),
    ]