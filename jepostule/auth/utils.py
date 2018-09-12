import hashlib
from django.conf import settings

from . import exceptions


def make_application_token(client_id, candidate_email, employer_email):
    """
    Create an application token that cannot be reverse computed such that
    candidates cannot apply from or send to any email address.

    There is no expiration date on this token: we assume that users will take a
    long time to write and send their application. However, we will (in the
    future) limit multiple applications to the same company.
    """
    client_secret = get_client_secret(client_id)
    string = settings.SECRET_KEY + client_secret + candidate_email + employer_email
    return hashlib.sha256(string.encode()).hexdigest()


def verify_application_token(client_id, token, candidate_email, employer_email):
    if not token or token != make_application_token(client_id, candidate_email, employer_email):
        raise exceptions.ApplicationAuthError("Invalid application token")


def verify_client_secret(client_id, client_secret):
    if not client_secret or get_client_secret(client_id) != client_secret:
        raise exceptions.ApplicationAuthError("Incorrect Client ID/Secret")


def get_client_secret(client_id):
    try:
        return settings.JEPOSTULE_CLIENTS[client_id]
    except KeyError:
        raise exceptions.ApplicationAuthError("Incorrect Client ID")
