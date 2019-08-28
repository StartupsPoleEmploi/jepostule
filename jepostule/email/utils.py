import os

from django.conf import settings

from jepostule.email.services import mailjet
from jepostule.email.services import django as django_email


# pylint: disable=too-many-arguments
def send_mail(
        subject,
        html_content,
        from_email,
        recipient_list,
        from_name=None,
        reply_to=None,
        attachments=None,
        mailjet_template_id=None,
        mailjet_template_data=None,
        monitoring_category=None):
    """
    Entry point for sending emails. This function will activate the correct
    email delivery service.

    The email service depends on the arguments received and the value
    of the `EMAIL_DELIVERY_SERVICE` setting.

    As long as the async tasks trigger only one email each, it is not necessary
    to run the send_mail function asynchronously.

    Returns:
        message IDs (int/None list): the list of message ID associated to each
        recipient. This list has the same size as the recipient list. When no
        message ID is available, it is None.
    """
    attachments = [
        (os.path.basename(f.name), f.content, None) for f in attachments
    ] if attachments else []

    email_args = (subject, html_content, from_email, recipient_list)
    email_kwargs = {
        'from_name': from_name,
        'reply_to': reply_to,
        'attachments': attachments,
    }

    use_mailjet = settings.EMAIL_DELIVERY_SERVICE == 'mailjet'
    use_mailjet_template = all([mailjet_template_id, mailjet_template_data, use_mailjet])

    if use_mailjet or use_mailjet_template:
        email_kwargs['monitoring_category'] = monitoring_category

    if use_mailjet_template:
        email_args = (subject, mailjet_template_id, mailjet_template_data, from_email, recipient_list)
        return mailjet.send_using_template(*email_args, **email_kwargs)

    if use_mailjet:
        return mailjet.send(*email_args, **email_kwargs)

    return django_email.send(*email_args, **email_kwargs)
