import json
import logging
import requests
from requests.exceptions import ConnectionError, ReadTimeout
from django.conf import settings
from . import models
from jepostule.crypto import decrypt


AMI_API_TIMEOUT_SECONDS = 10
AMI_API_STAGING_URL = 'https://api-r.es-qvr.fr/partenaire/candidaturespontanee/v1/candidaturespontanee'
AMI_API_PRODUCTION_URL = 'https://api.emploi-store.fr/partenaire/candidaturespontanee/v1/candidaturespontanee'


logger = logging.getLogger(__name__)


class TooManyRequests(Exception):
    pass


class RequestFailed(Exception):
    pass


def forward_job_application(job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)

    # The condition
    # job_application.client_platform.client_id == 'lbb'
    # is met in 2 cases:
    # - in production JP for applications coming from production LBB.
    # - in local dev JP for regular applications (not via the backdoor link).
    # Thus we have to additionally test for
    # settings.ALLOW_SENDING_APPLICATIONS_TO_PRODUCTION_AMI
    # to be sure we are in the case of production JP.
    if (settings.ALLOW_SENDING_APPLICATIONS_TO_PRODUCTION_AMI 
        and job_application.client_platform.client_id == 'lbb'):
        url = AMI_API_PRODUCTION_URL
    else:
        url = AMI_API_STAGING_URL

    params = None
    # AMI API specification mentions a maximum of 1500 characters for this field.
    texte_motivation = job_application.message[:1500]
    data = {
        "idCompetRecherchees": job_application.candidate_rome_code,
        "siret": job_application.siret,
        "texteMotivation": texte_motivation,
        "coordonneesCandidat": {
            "prenomNom": job_application.candidate_name,
            "adresse": job_application.candidate_address,
            "telFixe": job_application.candidate_phone,
            "telPortable": job_application.candidate_phone,
            "mail": job_application.candidate_email,
        },
    }

    decrypted_candidate_peam_access_token = decrypt(job_application.candidate_peam_access_token)

    headers = {
        "Authorization": "Bearer {}".format(decrypted_candidate_peam_access_token),
        "Content-Type": "application/json",
    }

    response = get_response(url, params, data, headers)
    # Nothing to check if no exception was raised,
    # as the expected normal return is a 204 HTTP code
    # without any actual content. The fact that it was
    # actually a 204 HTTP code was already tested in get_response.
    return


def get_response(url, params, data, headers):
    """
    Generic method fetching the response for a POST request to a given
    url with a given data object.
    """
    try:
        response = requests.post(
            url=url,
            params=params,
            data=json.dumps(data),
            headers=headers,
            timeout=AMI_API_TIMEOUT_SECONDS,
            verify=True,
        )
    except (ConnectionError, ReadTimeout) as e:
        logger.exception(e)
        raise e

    http_too_many_requests = 429
    # The AMI API answers with an unusual 204 http code (success but no content).
    expected_status_codes = [204]

    if response.status_code == http_too_many_requests:
        raise TooManyRequests
    elif response.status_code not in expected_status_codes:
        msg = '{} responded with an unexpected status_code {} : {}'.format(
            url,
            response.status_code,
            response.content,
        )
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, msg)
        raise RequestFailed("response={}".format(response))

    return response
