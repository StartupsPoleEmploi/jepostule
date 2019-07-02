# coding: utf8
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils.timezone import make_aware, datetime

from jepostule.pipeline import models


class Command(BaseCommand):
    help = """
    Dump job application and answer stats. Eg:
        
        ./manage.py dumpstats --min-date 20190101-00:00:00 --max-date 20190201-00:00:00
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-date',
            help="Earliest job application creation date (e.g: '20190101-00:00:00')",
        )
        parser.add_argument(
            '--max-date',
            help="Latest job application creation date (e.g: '20190201-00:00:00')",
        )

    def handle(self, *args, **options):
        datetime_format = "%Y%m%d-%H:%M:%S"
        min_date = make_aware(datetime.strptime(options["min_date"], datetime_format)) if options["min_date"] else None
        max_date = make_aware(datetime.strptime(options["max_date"], datetime_format)) if options["max_date"] else None

        application_query = {}
        answer_query = {}

        if min_date:
            application_query['created_at__gte'] = min_date
            answer_query['job_application__created_at__gte'] = min_date
        if max_date:
            application_query['created_at__lt'] = max_date
            answer_query['job_application__created_at__lt'] = max_date
        
        applications = models.JobApplication.objects.filter(**application_query)
        
        answers = models.Answer.objects.filter(**answer_query)
        answers_rejection = models.AnswerRejection.objects.filter(**answer_query)
        answers_interview = models.AnswerInterview.objects.filter(**answer_query)
        answers_request_info = models.AnswerRequestInfo.objects.filter(**answer_query)

        candidates = applications.values('candidate_email').annotate(Count('candidate_email'))

        print("""{} candidatures
{} candidats
{} candidatures par candidat
{} entreprises ont reçu au moins une candidature
{} réponses (tous types)
{}% taux de réponse employeur
{} entreprises ont répondu à au moins une candidature (tous types)
{} candidats ont reçu au moins une réponse à une candidature (tous types)
{} réponses (type 1 - refus)
{}% proportion des réponses de type 1 - refus
{} entreprises ont répondu à au moins une candidature (type 1 - refus)
{} candidats ont reçu au moins une réponse à une candidature (type 1 - refus)
{} réponses (type 2 - demande d'informations)
{}% proportion des réponses de type 2 - demande d'informations
{} entreprises ont répondu à au moins une candidature (type 2 - demande d'informations)
{} candidats ont reçu au moins une réponse à une candidature (type 2 - demande d'informations)
{} réponses (type 3 - proposition d'entretien)
{}% proportion des réponses de type 3 - proposition d'entretien
{} entreprises ont répondu à au moins une candidature (type 3 - proposition d'entretien)
{} candidats ont reçu au moins une réponse à une candidature (type 3 - proposition d'entretien)""".format(
            applications.count(),
            candidates.count(),
            round(applications.count() / candidates.count(), 1) if candidates.count() else "N/A",
            applications.values('siret').annotate(Count('siret')).count(),
            answers.count(),
            round(100.0 * answers.count() / applications.count(), 1) if applications.count() else "N/A",
            answers.values('job_application__siret').annotate(Count('job_application__siret')).count(),
            answers.values(
                'job_application__candidate_email').annotate(Count('job_application__candidate_email')).count(),
            answers_rejection.count(),
            round(100.0 * answers_rejection.count() / answers.count(), 1) if answers.count() else "N/A",
            answers_rejection.values('job_application__siret').annotate(Count('job_application__siret')).count(),
            answers_rejection.values(
                'job_application__candidate_email').annotate(Count('job_application__candidate_email')).count(),
            answers_request_info.count(),
            round(100.0 * answers_request_info.count() / answers.count(), 1) if answers.count() else "N/A",
            answers_request_info.values('job_application__siret').annotate(Count('job_application__siret')).count(),
            answers_request_info.values(
                'job_application__candidate_email').annotate(Count('job_application__candidate_email')).count(),
            answers_interview.count(),
            round(100.0 * answers_interview.count() / answers.count(), 1) if answers.count() else "N/A",
            answers_interview.values('job_application__siret').annotate(Count('job_application__siret')).count(),
            answers_interview.values(
                'job_application__candidate_email').annotate(Count('job_application__candidate_email')).count(),
        ))
