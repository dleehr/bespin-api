# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-09-26 14:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0030_auto_20170921_1631'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workflowmethodsdocument',
            old_name='content',
            new_name='contents',
        ),
    ]
