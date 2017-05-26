from django.core.management.base import BaseCommand
from argparse import FileType
from data.models import Workflow, WorkflowVersion, JobQuestionnaire
from cwltool.load_tool import load_tool
from cwltool.workflow import defaultMakeTool
import json
import sys


class CWLDocument(object):
    """
    Simple CWL document parser
    """

    def __init__(self, url):
        """
        Creates a parser for the given URL
        :param url: The URL to a CWL document to be parsed
        """
        self.url = url
        self._parsed = None

    @property
    def parsed(self):
        """
        Lazy property to parse CWL on-demand
        :return: The CWL document, parsed into a dict
        """
        if self._parsed is None:
            self._parsed = load_tool(self.url + '#main', defaultMakeTool)
        return self._parsed

    @property
    def input_fields(self):
        """
        The input fields from the CWL document
        :return: List of input fields from the CWL document
        """
        return self.parsed.inputs_record_schema.get('fields')

    def get(self, key):
        """
        Gets the value of a key in the root of the CWL document
        :param key: The key to get
        :return: value associated with the key in the parsed CWL
        """
        return self.parsed.tool.get(key)


class BaseImporter(object):
    """
    Base for importer with simple logging facility
    """

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        """
        Creates a base importer with logging IO streams
        :param stdout: For writing info log messages
        :param stderr: For writing error messages
        """
        self.stdout = stdout
        self.stderr = stderr

    def log_creation(self, created, kind, name, id):
        if created:
            self.stdout.write("{} '{}' created with id {}".format(kind, name, id))
        else:
            self.stderr.write("{} '{}' already exists with id {}".format(kind, name, id))


class WorkflowImporter(BaseImporter):
    """
    Creates Workflow and WorkflowVersion model objects from a CWL document and supplied version number
    """

    def __init__(self,
                 cwl_url,
                 version_number=1,
                 stdout=sys.stdout,
                 stderr=sys.stderr):
        """
        Creates a WorkflowImporter to import the specified CWL and its variables into bespin-api models
        :param cwl_url: The URL to a CWL Workflow to import 
        :param version_number: the version number to assign
        :param stdout: For writing info log messages
        :param stderr: For writing error messages
        """
        super(WorkflowImporter, self).__init__(stdout, stderr)
        self.cwl_url = cwl_url
        self.version_number = version_number
        # django model objects built up
        self.built_workflow = None
        self.built_workflow_version = None

    def _create_workflow_models(self):
        # Short description used for the Workflow name
        document = CWLDocument(self.cwl_url)
        workflow_name = document.get('label')
        # Longer description used in workflow version
        workflow_version_description = document.get('doc')
        workflow, created = Workflow.objects.get_or_create(name=workflow_name)
        self.log_creation(created, 'Workflow', workflow_name, workflow.id)
        workflow_version, created = WorkflowVersion.objects.get_or_create(
            workflow=workflow,
            url=self.cwl_url,
            description=workflow_version_description,
            version=self.version_number,
        )
        self.log_creation(created, 'Workflow Version', workflow_version_description, workflow_version.id)
        self.built_workflow = workflow
        self.built_workflow_version = workflow_version

    def cleanup(self):
        self.built_workflow_version.delete()
        self.built_workflow.delete()

    def run(self):
        # Parse in the workflow file
        self._create_workflow_models()


class Command(BaseCommand):
    help = 'Imports a workflow from CWL'

    def add_arguments(self, parser):
        parser.add_argument('cwl-url', help='URL to packed CWL workflow file. Do not include #main')
        parser.add_argument('version-number', help='Version number to assign to imported workflow')

    def handle(self, *args, **options):
        version_number = options.get('version-number')
        importer = WorkflowImporter(options.get('cwl-url'),
                                    version_number=version_number,
                                    stdout=self.stdout,
                                    stderr=self.stderr)
        importer.run()
        # importer.cleanup()
