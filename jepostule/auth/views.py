import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import events
from . import exceptions
from . import utils


def required_parameters(*parameters):
    """
    View decorator to verify that some parameters are present and non-empty.
    """
    def decorator(func):
        def decorated(request, *args, **kwargs):
            for parameter in parameters:
                if not getattr(request, request.method).get(parameter):
                    return missing_parameter_response(parameter)
            return func(request, *args, **kwargs)
        return decorated
    return decorator


def catch_auth_errors(func):
    """
    View decorator to catch authentication exceptions and return the right response.
    """
    def decorated(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except exceptions.ApplicationAuthError as e:
            return error_response(e.args[0], 403)
    return decorated


@required_parameters('client_id', 'client_secret', 'candidate_email', 'employer_email')
@catch_auth_errors
def application_token(request):
    utils.verify_client_secret(request.GET['client_id'], request.GET['client_secret'])

    token = utils.make_application_token(request.GET['client_id'], request.GET['candidate_email'], request.GET['employer_email'])
    return JsonResponse({
        "token": token,
    })


@require_POST
@csrf_exempt
def application_event_callback(request):
    """
    Callback endpoint used by Mailjet to monitor event updates
    https://dev.mailjet.com/guides/#events
    """
    if request.content_type != 'application/json':
        return error_response("Invalid content type", 400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response("Invalid json content", 400)
    if not isinstance(data, list):
        return error_response("Expected array in json content", 400)
    for event in data:
        # Note that there is no way to make sure we are not flooded with spam events
        events.log(event)
    return JsonResponse({})


def missing_parameter_response(name):
    return error_response("Missing required '{}' argument".format(name), 400)


def error_response(reason, status):
    return JsonResponse({
        'error': reason
    }, status=status)
