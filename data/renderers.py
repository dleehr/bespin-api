from rest_framework.renderers import JSONRenderer
from rest_framework import status

class JSONRootObjectRenderer(JSONRenderer):
    media_type = 'application/vnd.rootobject+json'
    format = 'json-rootobject'

    """
    Requires an attribute of 'resource_name' defined in the serializer's Meta class
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {}
        status_code = renderer_context.get('response').status_code
        if status.is_success(status_code):
            # Response is success, wrap the data in an object, depending on the serializer's resource_name
            try:
                view = renderer_context.get('view')
                resource_name = view.get_serializer().Meta.resource_name
                response_data[resource_name] = data
            except AttributeError:
                response_data = data
        else:
            # Response is an error, return data wrapped in errors
            response_data['errors'] = [data] # must be an array?
        response = super(JSONRootObjectRenderer, self).render(response_data, accepted_media_type, renderer_context)
        return response
