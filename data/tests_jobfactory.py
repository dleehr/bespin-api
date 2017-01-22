from django.test import TestCase
from models import DDSEndpoint, DDSUserCredential
from models import Workflow, WorkflowVersion
from models import Job, JobInputFile, DDSJobInputFile, URLJobInputFile, JobOutputDir, JobError
from models import LandoConnection
from models import JobQuestionnaire, JobQuestion, JobAnswerSet, JobAnswer, JobStringAnswer, JobDDSFileAnswer, \
    JobAnswerKind, JobDDSOutputDirectoryAnswer
from models import JobQuestionDataType
from django.contrib.auth.models import User
from jobfactory import JobFactory, QuestionKeyMap, \
    JOB_FIELD_NAME, JOB_FIELD_PROJECT_NAME, JOB_FIELD_VM_FLAVOR, JOB_FIELD_OUTPUT_DIRECTORY

from rest_framework.exceptions import ValidationError
from mock.mock import MagicMock, patch, Mock

FLY_RNASEQ_URL = "https://raw.githubusercontent.com/Duke-GCB/bespin-cwl/master/packed-workflows/rnaseq-pt1-packed.cwl"


def setup_rnaseq_job_answer_set():
    user = User.objects.create_user('test_user')
    workflow = Workflow.objects.create(name='RNASeq')
    workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                      description="RNASeq using Star",
                                                      version=1,
                                                      url=FLY_RNASEQ_URL)
    align_out_prefix = JobQuestion.objects.create(key="align_out_prefix",
                                                  name="Output filename prefix",
                                                  data_type=JobQuestionDataType.STRING)
    questionnaire = JobQuestionnaire.objects.create(description="dm3 fly RNASeq",
                                                    workflow_version=workflow_version)
    questionnaire.questions = [align_out_prefix]
    questionnaire.save()
    job_answer = JobAnswer.objects.create(user=user,
                                          question=align_out_prefix,

                                          kind=JobAnswerKind.STRING)
    JobStringAnswer.objects.create(answer=job_answer, value='bespin-rna-seq-0001_')
    job_answer_set = JobAnswerSet.objects.create(user=user, questionnaire=questionnaire)
    job_answer_set.answers = [job_answer]
    job_answer_set.save()
    return job_answer_set



class QuestionAnswerMapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.cred = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)

    def test_prevent_duplicate_question_keys(self):
        question1 = JobQuestion.objects.create(key="align_out_prefix",
                                                      name="Output filename prefix",
                                                      data_type=JobQuestionDataType.STRING)
        question2 = JobQuestion.objects.create(key="align_out_prefix",
                                                      name="Other Output filename prefix",
                                                      data_type=JobQuestionDataType.STRING)

        question_answer_map = QuestionKeyMap()
        question_answer_map.add_questions([question1, question2])
        errors = question_answer_map.get_errors()
        self.assertEqual(2, len(errors))
        self.assertIn({'source': 'align_out_prefix',
                       'details': 'Setup error: Multiple questions with same key: align_out_prefix.'}, errors)

    def test_two_different_question_keys(self):
        question1 = JobQuestion.objects.create(key="align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        question2 = JobQuestion.objects.create(key="align_out_prefix2",
                                               name="Other Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        question_answer_map = QuestionKeyMap()
        question_answer_map.add_questions([question1, question2])
        # We have two unanswered questions so we should have two errors
        errors = question_answer_map.get_errors()
        self.assertEqual(2, len(errors))
        self.assertIn({'source': 'align_out_prefix',
                       'details': 'Required field.'}, errors)
        self.assertIn({'source': 'align_out_prefix2',
                       'details': 'Required field.'}, errors)

    def test_two_different_question_keys_with_user_answers(self):
        question1 = JobQuestion.objects.create(key="align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='data_')
        question2 = JobQuestion.objects.create(key="output_index_filename",
                                               name="Output index file",
                                               data_type=JobQuestionDataType.STRING)
        answer2 = JobAnswer.objects.create(question=question2, user=self.user, kind=JobAnswerKind.DDS_FILE)
        JobDDSFileAnswer.objects.create(answer=answer2, project_id='1', file_id='1', dds_user_credentials=self.cred)

        question_answer_map = QuestionKeyMap()
        question_answer_map.add_questions([question1, question2])
        question_answer_map.add_answers([answer1, answer2])
        # We have two unanswered questions so we should have two errors
        errors = question_answer_map.get_errors()
        self.assertEqual(0, len(errors))

    def test_answer_without_question(self):
        question1 = JobQuestion.objects.create(key="align_out_prefix",
                                               name="Output filename prefix",
                                               data_type=JobQuestionDataType.STRING)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='data_')
        question_answer_map = QuestionKeyMap()
        question_answer_map.add_answers([answer1])
        errors = question_answer_map.get_errors()
        self.assertEqual(1, len(errors))
        self.assertIn({'source': 'align_out_prefix',
                       'details': 'Setup error: Answer without question: align_out_prefix.'}, errors)


class JobFactoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')
        self.cred = DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        workflow = Workflow.objects.create(name='RnaSeq')
        self.workflow_version = WorkflowVersion.objects.create(workflow=workflow,
                                                               object_name='#main',
                                                               version='1',
                                                               url=FLY_RNASEQ_URL)

    def add_job_fields(self, job_factory, name, project_name, vm_flavor, project_id, directory_name,
                       dds_user_credentials):
        self.add_string_field(job_factory, JOB_FIELD_NAME, name)
        self.add_string_field(job_factory, JOB_FIELD_PROJECT_NAME, project_name)
        self.add_string_field(job_factory, JOB_FIELD_VM_FLAVOR, vm_flavor)
        question = JobQuestion.objects.create(key=JOB_FIELD_OUTPUT_DIRECTORY,
                                               name="Directory where results will be saved",
                                               data_type=JobQuestionDataType.DIRECTORY)
        answer = JobAnswer.objects.create(question=question, user=self.user, kind=JobAnswerKind.DDS_OUTPUT_DIRECTORY)
        JobDDSOutputDirectoryAnswer.objects.create(answer=answer, project_id=project_id,
                                                   directory_name=directory_name,
                                                   dds_user_credentials=dds_user_credentials)
        job_factory.add_question(question)
        job_factory.add_answer(answer)

    def add_string_field(self, job_factory, key, value):
        question = JobQuestion.objects.create(key=key, name="Some name", data_type=JobQuestionDataType.STRING)
        answer = JobAnswer.objects.create(question=question, user=self.user, kind=JobAnswerKind.STRING, index=0)
        JobStringAnswer.objects.create(answer=answer, value=value)
        job_factory.add_question(question)
        job_factory.add_answer(answer)

    def test_simple_build_cwl_input(self):

        question1 = JobQuestion.objects.create(key="threads",
                                               name="Threads to use",
                                               data_type=JobQuestionDataType.INTEGER)
        answer1 = JobAnswer.objects.create(question=question1, user=self.user, kind=JobAnswerKind.STRING)
        JobStringAnswer.objects.create(answer=answer1, value='4')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        cwl_input = job_factory._build_cwl_input(job_factory._build_question_key_map())
        expected = {
            "threads": 4
        }
        self.assertEqual(expected, cwl_input)

    def test_string_array_build_cwl_input(self):
        question1 = JobQuestion.objects.create(key="cores",
                                               name="DNA cores to use",
                                               data_type=JobQuestionDataType.STRING,
                                               occurs=2)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=0)
        JobStringAnswer.objects.create(answer=answer1, value='ACGT')
        answer2 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=1)
        JobStringAnswer.objects.create(answer=answer2, value='CCGT')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer2)
        job_factory.add_answer(answer1)
        cwl_input = job_factory._build_cwl_input(job_factory._build_question_key_map())
        expected = {
            "cores": [
                "ACGT",
                "CCGT"
            ]
        }
        self.assertEqual(expected, cwl_input)

    def test_string_file_build_cwl_input(self):
        question1 = JobQuestion.objects.create(key="datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.STRING,
                                           index=0)
        JobStringAnswer.objects.create(answer=answer1, value='/data/stuff.csv')
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        cwl_input = job_factory._build_cwl_input(job_factory._build_question_key_map())
        expected = {
            "datafile": {
                    "class": "File",
                    "path": "/data/stuff.csv"
            }
        }
        self.assertEqual(expected, cwl_input)

    @patch("data.jobfactory.get_file_name")
    def test_file_build_cwl_input(self, mock_get_file_name):
        mock_get_file_name.return_value = 'stuff.csv'
        question1 = JobQuestion.objects.create(key="datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.DDS_FILE,
                                           index=0)
        JobDDSFileAnswer.objects.create(answer=answer1, project_id='1', file_id='1', dds_user_credentials=self.cred)
        job_factory = JobFactory(self.user, workflow_version=None)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        cwl_input = job_factory._build_cwl_input(job_factory._build_question_key_map())
        expected_filename = '{}_{}'.format(answer1.id, 'stuff.csv')
        expected = {
            "datafile": {
                "class": "File",
                "path": expected_filename
            }
        }
        self.assertEqual(expected, cwl_input)

    @patch("data.jobfactory.get_file_name")
    def test_create_simple_job(self, mock_get_file_name):
        mock_get_file_name.return_value = 'stuff.csv'
        question1 = JobQuestion.objects.create(key="datafile",
                                               name="Some data file",
                                               data_type=JobQuestionDataType.FILE)
        answer1 = JobAnswer.objects.create(question=question1,
                                           user=self.user,
                                           kind=JobAnswerKind.DDS_FILE,
                                           index=0)
        JobDDSFileAnswer.objects.create(answer=answer1, project_id='1', file_id='1', dds_user_credentials=self.cred)
        job_factory = JobFactory(self.user, workflow_version=self.workflow_version)
        job_factory.add_question(question1)
        job_factory.add_answer(answer1)
        self.add_job_fields(job_factory, name="Test project", project_name="myproj",
                            vm_flavor="m1.small", project_id="1", directory_name="results",
                            dds_user_credentials=self.cred)
        job = job_factory.create_job()
        expected = {
            'datafile': {'path': '1_stuff.csv', 'class': 'File'}
        }
        self.assertEqual(expected, job.workflow_input_json)

