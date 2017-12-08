# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-12-08 18:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def update_questionnaires(apps, schema_editor):
    """
    Forward migration function to normalize settings into VMSettings and CloudSettings models
    :param apps: Django apps
    :param schema_editor: unused
    :return: None
    """
    VMSettings = apps.get_model("data", "VMSettings")
    CloudSettings = apps.get_model("data", "CloudSettings")
    JobQuestionnaire = apps.get_model("data", "JobQuestionnaire")
    Job = apps.get_model("data", "Job")
    for q in JobQuestionnaire.objects.all():
        # Create a cloud settings object with the VM project from the questionnaire.
        # Object initially just has the project name as its name
        cloud_settings, _ = CloudSettings.objects.get_or_create(name=q.vm_project.name, vm_project=q.vm_project)
        vm_settings, _ = VMSettings.objects.get_or_create(name=q.vm_project.name, cloud_settings=cloud_settings)
        q.vm_settings = vm_settings
        q.save()

def update_jobs(apps, schema_editor):
    """
    In this migration, we update jobs so that
    1. CharField vm_flavor_name is normalized into a VMFlavor foreign key
    2. CharField vm_project_name is normalized into a VMProject foreign key, and referenced via
        Job -> VMSettings -> CloudSettings -> VMProject
    """
    Job = apps.get_model("data", "Job")
    VMSettings = apps.get_model("data", "VMSettings")
    VMProject = apps.get_model("data", "VMProject")
    CloudSettings = apps.get_model("data", "CloudSettings")
    VMFlavor = apps.get_model("data", "VMFlavor")
    for j in Job.objects.all():
        # 1. handle vm_flavor
        vm_flavor, _ = VMFlavor.objects.get_or_create(name=j.vm_flavor_name)
        j.vm_flavor = vm_flavor

        # 2. Handle vm_project
        vm_project, _ = VMProject.objects.get_or_create(name=j.vm_project_name)
        cloud_settings, _ = CloudSettings.objects.get_or_create(name=j.vm_project.name, vm_project=vm_project)
        vm_settings, _ = VMSettings.objects.get_or_create(name=vm_project.name, cloud_settings=cloud_settings)
        j.vm_settings = vm_settings
        j.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0038_auto_20171106_1623'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default_settings', help_text='Short name of this cloudsettings', max_length=255, unique=True)),
                ('ssh_key_name', models.CharField(help_text='Name of SSH key to inject into VM on launch', max_length=255)),
                ('network_name', models.CharField(help_text='Name of network to attach VM to on launch', max_length=255)),
                ('allocate_floating_ips', models.BooleanField(default=False, help_text='Allocate floating IPs to launched VMs')),
                ('floating_ip_pool_name', models.CharField(blank=True, help_text='Name of floating IP pool to allocate from', max_length=255, null=True)),
                ('vm_project', models.ForeignKey(help_text='Project name to use when creating VM instances for this questionnaire', on_delete=django.db.models.deletion.CASCADE, to='data.VMProject')),
            ],
        ),
        migrations.CreateModel(
            name='VMSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default_settings', help_text='Short name of these settings', max_length=255, unique=True)),
                ('image_name', models.CharField(help_text='Name of the VM Image to launch', max_length=255)),
                ('cwl_base_command', models.TextField(help_text="JSON-encoded command array to run the  image's installed CWL engine")),
                ('cwl_post_process_command', models.TextField(blank=True, help_text='JSON-encoded command array to run after workflow completes', null=True)),
                ('cwl_pre_process_command', models.TextField(blank=True, help_text='JSON-encoded command array to run before cwl_base_command', null=True)),
                ('cloud_settings', models.ForeignKey(help_text='Cloud settings ', on_delete=django.db.models.deletion.CASCADE, to='data.CloudSettings')),
            ],
            options={
                'verbose_name_plural': 'VM Settings Collections',
            },
        ),
        #############################
        # Update JobQuestionnaires
        #############################
        # Add JobQuestionnaire.vm_settings with a temporary default
        migrations.AddField(
            model_name='jobquestionnaire',
            name='vm_settings',
            field=models.ForeignKey(default=0, help_text='Collection of settings to use when launching job VMs for this questionnaire', on_delete=django.db.models.deletion.CASCADE, to='data.VMSettings'),
            preserve_default=False,
        ),

        # Populate VMSettings and CloudSettings objects from JobQuesetionnaire
        migrations.RunPython(update_questionnaires),
        migrations.RemoveField(
            model_name='jobquestionnaire',
            name='vm_project',
        ),
        migrations.AddField(
            model_name='jobquestionnaire',
            name='volume_mounts',
            field=models.TextField(default=b'{"/dev/vdb1": "/work"}',
                                   help_text='JSON-encoded list of volume mounts, e.g. {"/dev/vdb1": "/work"}'),
        ),

        # Remove the default value
        migrations.AlterField(
            model_name='jobquestionnaire',
            name='vm_settings',
            field=models.ForeignKey(
                help_text='Collection of settings to use when launching job VMs for this questionnaire',
                on_delete=django.db.models.deletion.CASCADE, to='data.VMSettings'),
        ),

        #############################
        # Update Jobs
        #############################
        migrations.RenameField(
            model_name='job',
            old_name='vm_flavor',
            new_name='vm_flavor_name'
        ),
        migrations.AddField(
            model_name='job',
            name='vm_flavor',
            field=models.ForeignKey(help_text='VM Flavor to use when creating VM instances for this questionnaire',
                                    on_delete=django.db.models.deletion.CASCADE, to='data.VMFlavor'),
        ),
        migrations.AddField(
            model_name='job',
            name='vm_settings',
            field=models.ForeignKey(default=0, help_text='Collection of settings to use when launching VM for this job',
                                    on_delete=django.db.models.deletion.CASCADE, to='data.VMSettings'),
            preserve_default=False,
        ),

        # Populate VMSettings and CloudSettings objects from Job
        migrations.RunPython(update_jobs),
        # Remove the default value
        migrations.AlterField(
            model_name='job',
            name='vm_settings',
            field=models.ForeignKey(help_text='Collection of settings to use when launching VM for this job',
                                    on_delete=django.db.models.deletion.CASCADE, to='data.VMSettings'),
        ),

        # Remove the renamed vm_flavor_name field
        migrations.RemoveField(
            model_name='job',
            name='vm_flavor_name',
        ),

        migrations.RemoveField(
            model_name='job',
            name='vm_project_name',
        ),

    ]
