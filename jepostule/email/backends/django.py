from django.core import mail

def send(subject, html_content, from_email, recipients, from_name=None, reply_to=None, attachments=None):
    connection = mail.get_connection()
    if from_name:
        from_email = f"{from_name} <{from_email}>"
    message = mail.EmailMultiAlternatives(
        subject, html_content, from_email, recipients,
        connection=connection,
        reply_to=reply_to,
        attachments=attachments,
    )
    message.attach_alternative(html_content, 'text/html')
    message.send()
    return [None] * len(recipients)
