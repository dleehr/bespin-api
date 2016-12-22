from __future__ import unicode_literals

from django.db import models
from django.conf import settings


class DDSEndpoint(models.Model):
    """
    Stores the agent key for this application
    """
    name = models.CharField(max_length=255, blank=False, unique=True)
    agent_key = models.CharField(max_length=32, blank=False, unique=True)
    api_root = models.URLField()


class DDSUserCredential(models.Model):
    """
    DDS Credentials for bespin users
    """
    endpoint = models.ForeignKey(DDSEndpoint, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    token = models.CharField(max_length=32, blank=False, unique=True)

    class Meta:
        unique_together = ('endpoint', 'user',)


class Workflow(models.Model):
    """
    Name of a workflow that will apply some processing to some data.
    """
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

    class JSONAPIMeta:
        resource_name = 'workflows'


class WorkflowVersion(models.Model):
    """
    Specific version of a Workflow.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='versions')
    description = models.TextField()
    object_name = models.CharField(max_length=255, null=True, default='#main',
                                   help_text="Name of the object in a packed workflow to run. "
                                             "Typically set to '#main'.")
    created = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    version = models.IntegerField(null=False)
    url = models.URLField(null=False, help_text="URL to packed CWL workflow file.")

    def __unicode__(self):
        return '{} version: {} created: {}'.format(self.workflow.name, self.version, self.created)

    class JSONAPIMeta:
        resource_name = 'workflow-versions'


class Job(models.Model):
    """
    Instance of a workflow that is in some state of progress.
    """
    JOB_STATE_NEW = 'N'
    JOB_STATE_RUNNING = 'R'
    JOB_STATE_FINISHED = 'F'
    JOB_STATE_ERROR = 'E'
    JOB_STATE_CANCEL = 'C'
    JOB_STATES = (
        (JOB_STATE_NEW, 'New'),
        (JOB_STATE_RUNNING, 'Running'),
        (JOB_STATE_FINISHED, 'Finished'),
        (JOB_STATE_ERROR, 'Error'),
        (JOB_STATE_CANCEL, 'Canceled')
    )

    JOB_STEP_CREATE_VM = 'V'
    JOB_STEP_STAGING = 'S'
    JOB_STEP_RUNNING = 'R'
    JOB_STEP_STORE_OUTPUT = 'O'
    JOB_STEP_TERMINATE_VM = 'T'
    JOB_STEPS = (
        (JOB_STEP_CREATE_VM, 'Create VM'),
        (JOB_STEP_STAGING, 'Staging In'),
        (JOB_STEP_RUNNING, 'Running Workflow'),
        (JOB_STEP_STORE_OUTPUT, 'Store Job Output'),
        (JOB_STEP_TERMINATE_VM, 'Terminate VM'),
    )

    workflow_version = models.ForeignKey(WorkflowVersion, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255, blank=False, null=False,
                                        help_text="User specified name for this job.")

    created = models.DateTimeField(auto_now_add=True, blank=False)
    state = models.CharField(max_length=1, choices=JOB_STATES, default='N',
                             help_text="High level state of the project")
    step = models.CharField(max_length=1, choices=JOB_STEPS, null=True,
                            help_text="Job step (progress within Running state)")
    last_updated = models.DateTimeField(auto_now=True, blank=False)
    vm_flavor = models.CharField(max_length=255, blank=False, default='m1.small',
                                 help_text="Determines CPUs and RAM VM allocation used to run this job.")
    vm_instance_name = models.CharField(max_length=255, blank=True, null=True,
                                        help_text="Name of the vm this job is/was running on.")
    vm_project_name = models.CharField(max_length=255, blank=False, null=False,
                                       help_text="Name of the cloud project where vm will be created.")
    workflow_input_json = models.TextField(null=True,
                                           help_text="CWL input json for use with the workflow.")

    def __unicode__(self):
        workflow_name = ''
        if self.workflow_version:
            workflow_name = self.workflow_version.workflow
        return '{} ({}) for user {}'.format(workflow_name, self.get_state_display(), self.user)

    class JSONAPIMeta:
        resource_name = 'jobs'


class JobOutputDir(models.Model):
    """
    Output directory where results of workflow will be uploaded to.
    """
    job = models.OneToOneField(Job, on_delete=models.CASCADE, null=False, related_name='output_dir')
    dir_name = models.CharField(max_length=255, blank=False, null=True)
    project_id = models.CharField(max_length=255, blank=False, null=True)
    dds_user_credentials = models.ForeignKey(DDSUserCredential, on_delete=models.CASCADE, null=True)

    def __unicode__(self):
        return 'Directory name: {} Project: {}'.format(self.dir_name, self.project_id)


class JobInputFile(models.Model):
    """
    Input file that will be downloaded before running a workflow.
    """
    DUKE_DS_FILE = 'dds_file'
    DUKE_DS_FILE_ARRAY = 'dds_file_array'
    URL_FILE = 'url_file'
    URL_FILE_ARRAY = 'url_file_array'
    INPUT_FILE_TYPE = (
        (DUKE_DS_FILE, 'DukeDS File'),
        (DUKE_DS_FILE_ARRAY, 'DukeDS File Array'),
        (URL_FILE, 'URL File'),
        (URL_FILE_ARRAY, 'URL File Array'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, related_name='input_files')
    file_type = models.CharField(max_length=30, choices=INPUT_FILE_TYPE)
    workflow_name = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return 'Job Input File "{}"  ({})'.format(self.workflow_name, self.file_type)


class DDSJobInputFile(models.Model):
    """
    Settings for a DUKE_DS_FILE or DUKE_DS_FILE_ARRAY type JobInputFile.
    """
    job_input_file = models.ForeignKey(JobInputFile, on_delete=models.CASCADE, null=False, related_name='dds_files')
    project_id = models.CharField(max_length=255, blank=False, null=True)
    file_id = models.CharField(max_length=255, blank=False, null=True)
    dds_user_credentials = models.ForeignKey(DDSUserCredential, on_delete=models.CASCADE)
    destination_path = models.CharField(max_length=255, blank=False, null=True)
    index = models.IntegerField(null=True)

    def __unicode__(self):
        return 'DDS Job Input File "{}" ({}) id:{}'.format(self.destination_path, self.job_input_file.workflow_name,
                                                     self.file_id)


class URLJobInputFile(models.Model):
    """
    Settings for a URL_FILE or URL_FILE_ARRAY type JobInputFile.
    """
    job_input_file = models.ForeignKey(JobInputFile, on_delete=models.CASCADE, null=False, related_name='url_files')
    url = models.TextField(null=True)
    destination_path = models.CharField(max_length=255, blank=False, null=True)
    index = models.IntegerField(null=True)

    def __unicode__(self):
        return 'URL Job Input File {} ({})'.format(self.url, self.job_input_file.workflow_name)


class JobError(models.Model):
    """
    Record of a particular error that happened with a job including the state the job was at when the error happened.
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, related_name='job_errors')
    content = models.TextField(null=False)
    job_step = models.CharField(max_length=1, choices=Job.JOB_STEPS)
    created = models.DateTimeField(auto_now_add=True, blank=False)


class LandoConnection(models.Model):
    """
    Settings used to connect with lando to start, restart or cancel a job.
    """
    host = models.CharField(max_length=255, blank=False, null=False)
    username = models.CharField(max_length=255, blank=False, null=False)
    password = models.CharField(max_length=255, blank=False, null=False)
    queue_name = models.CharField(max_length=255, blank=False, null=False)
