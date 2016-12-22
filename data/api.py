from rest_framework import viewsets, permissions
from util import get_user_projects, get_user_project, get_user_project_content
from rest_framework.response import Response
from exceptions import DataServiceUnavailable
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, DDSJobInputFile, \
    DDSEndpoint, DDSUserCredential, URLJobInputFile, JobError, JobOutputDir
from data.serializers import WorkflowSerializer, WorkflowVersionSerializer, JobSerializer, \
    DDSEndpointSerializer, DDSUserCredSerializer, JobInputFileSerializer, DDSJobInputFileSerializer, \
    URLJobInputFileSerializer, JobErrorSerializer, AdminJobSerializer, DDSProjectSerializer
from data.serializers import AdminDDSUserCredSerializer, JobOutputDirSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import detail_route
from lando import LandoJob


class ProjectsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSProjectSerializer

    def list(self, request):
        try:
            projects = get_user_projects(request.user)
            serializer = self.serializer_class(instance=projects, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise DataServiceUnavailable(e)

    def retrieve(self, request, pk=None):
        project = get_user_project(request.user, pk)
        serializer = self.serializer_class(project)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def content(self, request, pk=None):
        search_str = request.GET.get('search', '')
        return Response(get_user_project_content(request.user, pk, search_str))


class WorkflowsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class WorkflowVersionsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = WorkflowVersion.objects.all()
    serializer_class = WorkflowVersionSerializer


class JobsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobSerializer

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

    @detail_route(methods=['post'])
    def start(self, request, pk=None):
        job = LandoJob(pk)
        job.start()
        return Response({'status': 'ok'})

    @detail_route(methods=['post'])
    def cancel(self, request, pk=None):
        job = LandoJob(pk)
        job.cancel()
        return Response({'status': 'ok'})

    @detail_route(methods=['post'])
    def restart(self, request, pk=None):
        job = LandoJob(pk)
        job.restart_job()
        return Response({'status': 'ok'})


class AdminJobsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AdminJobSerializer
    queryset = Job.objects.all()


class DDSJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSJobInputFileSerializer

    def get_queryset(self):
        return DDSJobInputFile.objects.filter(job_input_file__job__user=self.request.user)


class JobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobInputFileSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)

    def get_queryset(self):
        return JobInputFile.objects.filter(job__user=self.request.user)


class AdminJobInputFileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = JobInputFileSerializer
    queryset = JobInputFile.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)


class URLJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = URLJobInputFileSerializer

    def get_queryset(self):
        return URLJobInputFile.objects.filter(job_input_file__job__user=self.request.user)


class DDSEndpointViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSEndpointSerializer
    queryset = DDSEndpoint.objects.all()


class DDSUserCredViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)

    def get_queryset(self):
        return DDSUserCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        self.save_with_user(serializer)

    def perform_update(self, serializer):
        self.save_with_user(serializer)

    def save_with_user(self, serializer):
        serializer.save(user=self.request.user)


class AdminDDSUserCredentialsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    queryset = DDSUserCredential.objects.all()
    serializer_class = AdminDDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)


class JobErrorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobErrorSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)

    def get_queryset(self):
        return JobError.objects.filter(job__user=self.request.user)


class AdminJobErrorViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    queryset = JobError.objects.all()
    serializer_class = JobErrorSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)


class JobOutputDirViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobOutputDir.objects.all()
    serializer_class = JobOutputDirSerializer
