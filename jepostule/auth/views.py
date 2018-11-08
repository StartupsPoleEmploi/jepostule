import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import events
from . import exceptions
from . import utils


def catch_credentials_errors(func):
    """
    View decorator to catch authentication exceptions and return the right response.
    """
    def decorated(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except exceptions.AuthError as e:
            return error_response(e.message, 403)
    return decorated


@require_POST
@csrf_exempt
@catch_credentials_errors
def application_token(request):
    """
    This is POST to avoid client secrets passed in clear in the url.
    """
    utils.verify_client_secret(request.POST.get('client_id'), request.POST.get('client_secret'))
    params = dict(request.POST.items())
    token, timestamp = utils.make_new_application_token(**params)
    return JsonResponse({
        "token": token,
        "timestamp": timestamp,
    })


@require_POST
@csrf_exempt
@catch_credentials_errors
def application_token_refresh(request):
    params = dict(request.POST.items())
    utils.verify_application_token(**params)
    token, timestamp = utils.make_new_application_token(**params)
    return JsonResponse({
        "token": token,
        "timestamp": timestamp,
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
