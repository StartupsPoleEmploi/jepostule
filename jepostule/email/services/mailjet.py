import base64
import mimetypes

from mailjet_rest import Client

from django.conf import settings


MAILJET_CLIENT = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')


def send(
        subject,
        html_content,
        from_email,
        recipients,
        from_name=None,
        reply_to=None,
        attachments=None,
        monitoring_category=None):
    data = {
        "Messages": [
            {
                "From": {"Email": from_email},
                "To": [{"Email": recipient} for recipient in recipients],
                "Subject": subject,
                "HTMLPart": html_content,
                "Attachments": encode_attachments(attachments),
            },
        ],
    }
    if from_name:
        data['Messages'][0]['From']['Name'] = from_name
    if reply_to:
        data['Messages'][0]['ReplyTo'] = {"Email": reply_to}
    if monitoring_category:
        data['Messages'][0]['MonitoringCategory'] = monitoring_category
    json_response = post_api(data)
    return extract_ids(json_response)


def send_using_template(
        subject,
        mailjet_template_id,
        mailjet_template_data,
        from_email,
        recipients,
        from_name=None,
        reply_to=None,
        attachments=None,
        monitoring_category=None):
    data = {
        "Messages": [
            {
                "From": {"Email": from_email},
                "To": [{"Email": recipient} for recipient in recipients],
                "Subject": subject,
                "Attachments": encode_attachments(attachments),
                "TemplateID": mailjet_template_id,
                "TemplateLanguage": True,
                "Variables": mailjet_template_data,
            },
        ],
    }
    if from_name:
        data['Messages'][0]['From']['Name'] = from_name
    if reply_to:
        data['Messages'][0]['ReplyTo'] = {"Email": reply_to}
    if monitoring_category:
        data['Messages'][0]['MonitoringCategory'] = monitoring_category
    json_response = post_api(data)
    return extract_ids(json_response)


def extract_ids(json_response):
    return [message["MessageID"] for message in json_response["Messages"][0]["To"]]


def encode_attachments(attachments):
    return [{
        "ContentType": mimetype(attachment[0]),
        "Filename": attachment[0],
        "Base64Content": base64.encodebytes(attachment[1]).decode().strip(),
    } for attachment in attachments] if attachments else []


def mimetype(url):
    types = mimetypes.guess_type(url, strict=False)
    return types[0] if types and types[0] else 'application/octet-stream'


def post_api(data):
    response = MAILJET_CLIENT.send.create(data=data)
    # In case of error, we just crash: it's important that the task queue
    # crashes, too, so failed messages can be tried again.
    if response.status_code >= 400:
        raise MailjetAPIError(response.status_code, response.content)
    return response.json()


class MailjetAPIError(Exception):
    pass
