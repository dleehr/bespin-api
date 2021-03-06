from rest_framework.exceptions import APIException


class DataServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Data Service temporarily unavailable, try again later.'


class WrappedDataServiceException(APIException):
    """
    Converts error returned from DukeDS python code into one appropriate for django.
    """
    def __init__(self, data_service_exception):
        self.status_code = data_service_exception.status_code
        self.detail = data_service_exception.message


class BespinAPIException(APIException):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


class JobFactoryException(APIException):
    """
    Contains errors that occurred when trying to create a Job from a JobAnswerSet
    """
    def __init__(self, errors):
        self.status_code = 400
        self.detail = {
            "errors": errors
        }


class JobTokenException(APIException):
    def __init__(self, detail):
        self.status_code = 400
        self.detail = detail


class EmailServiceException(APIException):
    status_code = 503
    default_detail = 'Unable to send email, try again later'


class EmailAlreadySentException(APIException):
    status_code = 400
    default_detail = 'Email message has already been sent'

