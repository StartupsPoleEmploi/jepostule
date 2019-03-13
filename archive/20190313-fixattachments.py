# Script used to apologize to send emails to users explaining the incident that
# caused missing attachments and saying "you should re-apply".
from django.template import Context, Template

from jepostule.kvstore import redis
from jepostule.pipeline import models
from jepostule.security.blacklist import is_blacklisted
from jepostule.email.backends import mailjet

REDIS_KEY = "jobapplicationswithoutattachment"

def main():
    store_applications()
    redis_client = redis()
    for candidate_email, sirets in iter_applications():
        print(candidate_email, sirets)
        send_email(candidate_email, sirets)
        key_name = REDIS_KEY + ":" + candidate_email
        redis_client.delete(key_name)

def store_applications():
    stored_key = REDIS_KEY + "-stored"
    redis_client = redis()
    if redis_client.exists(stored_key):
        return

    applications = models.JobApplication.objects.filter(
        events__email__message_id__isnull=False, events__name="sent", events__created_at__lt="2019-03-07"
    ).values("candidate_email", "siret").distinct()
    candidates = {}
    for application in applications:
        email = application["candidate_email"]
        if email not in candidates:
            candidates[email] = []
        candidates[email].append(application["siret"])

    redis_client = redis()
    for email, sirets in candidates.items():
        key_name = REDIS_KEY + ":" + email
        redis_client.delete(key_name)
        redis_client.lpush(key_name, *sirets)

    redis_client.set(stored_key, 1)

def iter_applications():
    redis_client = redis()
    for key in redis_client.keys(REDIS_KEY + ":*"):
        candidate_email = key.decode().split(":")[1]
        if is_blacklisted(candidate_email):
            continue
        sirets = [siret.decode() for siret in redis_client.lrange(key, 0, -1)]
        yield candidate_email, sirets

def send_email(candidate_email, sirets):
    template = Template("""Madame, Monsieur,

Dans la période du 26 février au 5 mars, vous avez envoyé des candidatures spontanées aux entreprises suivantes depuis La Bonne Boite : 
{% for siret in sirets %}
- https://labonneboite.pole-emploi.fr/{{ siret }}/details
{% endfor %}
Nous sommes au regret de vous annoncer que l'outil d'envoi de candidatures a subi un dysfonctionnement durant cette période : vos candidatures ont bien été envoyées, mais les pièces jointes que vous avez éventuellement ajoutées à vos messages n'ont pas été transmises. Ce problème est désormais résolu et nous vous encourageons donc à candidater à nouveau auprès de ces entreprises. 

Croyez bien que nous prenons ce dysfonctionnement très au sérieux et que nous mettons toutes les mesures en place pour que cet incident ne se reproduise pas.

Toute l'équipe de La Bonne Boite vous souhaite beaucoup de réussite dans votre recherche d'emploi.

Bien cordialement,

L'équipe technique de La Bonne Boite (https://labonneboite.pole-emploi.fr/)""")
    message = template.render(Context({"sirets": sirets}))
    mailjet.post_api(
        "/send",
        {
            "Messages": [
                {
                    "From": {
                        "Name": "La Bonne Boite",
                        "Email": "contact@jepostule.labonneboite.pole-emploi.fr",
                    },
                    "To": [{
                        "Name": "",
                        "Email": candidate_email,
                    }],
                    "Subject": "Problème lors de l'envoi de vos candidatures",
                    "TextPart": message,
                }
            ]
        }
    )
