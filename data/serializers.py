from rest_framework_json_api import serializers
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, DDSJobInputFile, \
    DDSEndpoint, DDSUserCredential, JobOutputDir, URLJobInputFile, JobError


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'name', 'versions')
        read_only_fields = ('versions',)


class WorkflowVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersion
        fields = ('id', 'workflow', 'description', 'object_name', 'created', 'url', 'version')


class JobOutputDirSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Users can only use their own credentials
        if data['dds_user_credentials'].user.id != data['job'].user.id:
            raise serializers.ValidationError("You cannot use another user's credentials.")
        return data
    class Meta:
        model = JobOutputDir
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    output_dir = JobOutputDirSerializer(required=False, read_only=True)
    vm_project_name = serializers.CharField(required=False)
    state = serializers.CharField(read_only=True)
    step = serializers.CharField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Job
        fields = ('id', 'workflow_version', 'user', 'name', 'created', 'state', 'step', 'last_updated',
                  'vm_flavor', 'vm_instance_name', 'vm_project_name', 'workflow_input_json', 'output_dir')


class AdminJobSerializer(serializers.ModelSerializer):
    workflow_version = WorkflowVersionSerializer(required=False)
    output_dir = JobOutputDirSerializer(required=False, read_only=True)
    vm_project_name = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=False)
    class Meta:
        model = Job
        fields = ('id', 'workflow_version', 'user_id', 'created', 'state', 'step', 'last_updated',
                  'vm_flavor', 'vm_instance_name', 'vm_project_name', 'workflow_input_json', 'output_dir')


class DDSEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DDSEndpoint
        fields = ('id', 'name', 'api_root')


class DDSUserCredSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        model = DDSUserCredential
        fields = ('id', 'user', 'token', 'endpoint')


class DDSJobInputFileSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Users can only use their own credentials
        if data['dds_user_credentials'].user.id != data['job_input_file'].job.user.id:
            raise serializers.ValidationError("You cannot use another user's credentials.")
        return data

    class Meta:
        model = DDSJobInputFile
        fields = '__all__'


class URLJobInputFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = URLJobInputFile
        fields = '__all__'


class JobInputFileSerializer(serializers.ModelSerializer):
    dds_files = serializers.SerializerMethodField()
    url_files = serializers.SerializerMethodField()

    # Sort inner dds files by their index so we can keep our arrays in the same order.
    def get_dds_files(self, obj):
        qset = DDSJobInputFile.objects.filter(job_input_file__pk=obj.pk).order_by('index')
        ser = DDSJobInputFileSerializer(qset, many=True, read_only=True)
        return ser.data

    # Sort inner url files by their index so we can keep our arrays in the same order.
    def get_url_files(self, obj):
        qset = URLJobInputFile.objects.filter(job_input_file__pk=obj.pk).order_by('index')
        ser = URLJobInputFileSerializer(qset, many=True, read_only=True)
        return ser.data

    class Meta:
        model = JobInputFile
        fields = ('id', 'job', 'file_type', 'workflow_name', 'dds_files', 'url_files')


class JobErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobError
        fields = '__all__'


class AdminDDSEndpointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DDSEndpoint
        fields = ('id','name', 'agent_key', 'api_root')


class AdminDDSUserCredSerializer(serializers.ModelSerializer):
    endpoint = AdminDDSEndpointSerializer()

    class Meta:
        model = DDSUserCredential
        fields = ('id', 'user', 'token', 'endpoint')


class DDSProjectSerializer(serializers.Serializer):
    """
    Serializer for dds_resources.DDSProject
    """
    pk = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
