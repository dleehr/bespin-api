# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-13 14:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0009_auto_20161212_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='vm_project_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
