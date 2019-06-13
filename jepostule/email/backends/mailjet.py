import base64
import mimetypes

from mailjet_rest import Client

from django.conf import settings


mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')


def send(subject, html_content, from_email, recipients, from_name=None, reply_to=None, attachments=None):
    attachments = [{
        "ContentType": mimetype(attachment[0]),
        "Filename": attachment[0],
        "Base64Content": base64.encodebytes(attachment[1]).decode().strip(),
    } for attachment in attachments] if attachments else []

    data = {
        "Messages": [
            {
                "From": {
                    "Email": from_email,
                },
                "To": [{
                    "Email": recipient,
                } for recipient in recipients],
                "Subject": subject,
                "HTMLPart": html_content,
                "Attachments": attachments,
            },
        ],
    }
    if from_name:
        data['Messages'][0]['From']['Name'] = from_name

    response = post_api(data)
    return [message["MessageID"] for message in response["Messages"][0]["To"]]


def mimetype(url):
    types = mimetypes.guess_type(url, strict=False)
    return types[0] if types and types[0] else 'application/octet-stream'


def post_api(data):
    response = mailjet.send.create(data=data)
    # In case of error, we just crash: it's important that the task queue
    # crashes, too, so failed messages can be tried again.
    if response.status_code >= 400:
        raise MailjetAPIError(response.status_code, response.content)
    return response.json()


class MailjetAPIError(Exception):
    pass
