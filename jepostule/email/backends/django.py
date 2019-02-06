from django.core import mail

def send(subject, html_content, from_email, recipients, reply_to=None, attachments=None):
    connection = mail.get_connection()
    message = mail.EmailMultiAlternatives(
        subject, html_content, from_email, recipients,
        connection=connection,
        reply_to=reply_to,
        attachments=attachments,
    )
    message.attach_alternative(html_content, 'text/html')
    message.send()
    return [None] * len(recipients)
