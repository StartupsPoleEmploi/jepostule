import importlib

from django.http import JsonResponse


def import_object(dotted_path):
    """
    Import an object given its dotted string path.
    """
    names = dotted_path.split('.')
    module = importlib.import_module('.'.join(names[:-1]))
    return getattr(module, names[-1])


def error_response(reason, status):
    """
    Return a JSON-formatted HTTP response with the proper error message and
    status code.
    """
    return JsonResponse({
        'error': reason
    }, status=status)
