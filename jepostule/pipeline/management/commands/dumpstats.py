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
        applications_no_answer = models.JobApplication.objects.filter(**application_query, answer=None)
        answers = models.Answer.objects.filter(**answer_query)
        answers_rejection = models.AnswerRejection.objects.filter(**answer_query)
        answers_interview = models.AnswerInterview.objects.filter(**answer_query)
        answers_request_info = models.AnswerRequestInfo.objects.filter(**answer_query)

        print("""{} candidatures
{} candidats uniques
{} entreprises
{} candidatures sans réponse
{} reponses
{} reponses(refus)
{} reponses(demande d'informations)
{} reponses (interview)""".format(
            applications.count(),
            applications.values('candidate_email').annotate(Count('candidate_email')).count(),
            applications.values('siret').annotate(Count('siret')).count(),
            applications_no_answer.count(),
            answers.count(),
            answers_rejection.count(),
            answers_request_info.count(),
            answers_interview.count(),
        ))
