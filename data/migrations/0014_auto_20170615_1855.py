# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-06-15 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0013_auto_20170614_1750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobanswerset',
            name='user_job_order_json',
            field=models.TextField(default=b'{}', help_text='JSON containing the portion of the job order specified by user', null=True),
        ),
    ]