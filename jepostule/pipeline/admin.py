from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from . import models


class JobApplicationEventAdminMixin:
    def visualize(self, obj):
        if obj.name == models.JobApplicationEvent.SENT_TO_EMPLOYER:
            url = reverse(
                'pipeline:email_application',
                kwargs={'job_application_id': obj.job_application.id}
            )
            return format_html("<a href='{url}' target='_blank' rel='noopener'>Email</a>", url=url)
        if obj.name == models.JobApplicationEvent.CONFIRMED_TO_CANDIDATE:
            url = reverse(
                'pipeline:email_confirmation',
                kwargs={'job_application_id': obj.job_application.id}
            )
            return format_html("<a href='{url}' target='_blank' rel='noopener'>Email</a>", url=url)
        if obj.name == models.JobApplicationEvent.ANSWERED:
            url = reverse(
                'pipeline:email_answer',
                kwargs={'answer_id': obj.job_application.answer.id}
            )
            return format_html("<a href='{url}' target='_blank' rel='noopener'>Email</a>", url=url)
        return ''
    visualize.short_description = "Visualiser"


class JobApplicationEventInlineAdmin(admin.TabularInline, JobApplicationEventAdminMixin):
    model = models.JobApplicationEvent
    readonly_fields = ('created_at', 'name', 'value', 'visualize')
    extra = 0


@admin.register(models.JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'created_at', 'candidate_email', 'employer_email',)
    list_display_links = ('id', 'candidate_email', 'employer_email',)
    ordering = ('-created_at',)
    search_fields = ('id', 'created_at', 'candidate_email', 'employer_email', 'job',)
    sortable_by = ('created_at', 'candidate_email', 'employer_email',)
    readonly_fields = ('detailed_answer_link',)
    inlines = (JobApplicationEventInlineAdmin,)

    def detailed_answer_link(self, obj):
        # This will display "-" in case there is no answer
        return detailed_answer_link(obj.answer.get_details())
    detailed_answer_link.short_description = "Voir la réponse détaillée"


@admin.register(models.JobApplicationEvent)
class JobApplicationEventAdmin(admin.ModelAdmin, JobApplicationEventAdminMixin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'created_at', 'name', 'value', 'candidate_email', 'employer_email', 'visualize',)
    list_display_links = ('id', 'name', 'value',)
    ordering = ('-created_at',)
    search_fields = ('created_at', 'job_application', 'name',)
    sortable_by = ('created_at', 'job_application', 'name',)
    readonly_fields = ('visualize',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job_application')

    def candidate_email(self, obj):
        return obj.job_application.candidate_email

    def employer_email(self, obj):
        return obj.job_application.employer_email

class BaseAnswerAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('job_application_link', 'email_link',)
    exclude = ('job_application',)

    def job_application_link(self, obj):
        url = reverse(
            'admin:jepostulepipeline_jobapplication_change',
            kwargs={'object_id': obj.job_application.id},
        )
        return format_html(
            "<a href='{url}'>Job Application ({email})</a>",
            url=url,
            email=obj.job_application.candidate_email,
        )
    job_application_link.short_description = "Voir la candidature associée"

    def email_link(self, obj):
        return answer_email_link(obj.answer_ptr)
    email_link.short_description = "Voir l'email"


@admin.register(models.Answer)
class AnswerAdmin(BaseAnswerAdmin):
    list_display = ('created_at', 'job_application',)
    list_display_links = ('created_at',)
    readonly_fields = (
        'id', 'job_application_link', 'detailed_answer_link', 'email_link',
        'answerrejection', 'answerrequestinfo', 'answerinterview',
    )

    def detailed_answer_link(self, obj):
        return detailed_answer_link(obj.get_details())
    detailed_answer_link.short_description = "Voir la réponse détaillée"

    def email_link(self, obj):
        return answer_email_link(obj)
    email_link.short_description = "Voir l'email"


@admin.register(models.AnswerRejection)
class AnswerRejectionAdmin(BaseAnswerAdmin):
    list_display = ('created_at', 'reason',)


@admin.register(models.AnswerRequestInfo)
class AnswerRequestInfoAdmin(BaseAnswerAdmin):
    list_display = ('created_at', 'employer_email',)


@admin.register(models.AnswerInterview)
class AnswerInterviewAdmin(BaseAnswerAdmin):
    list_display = ('created_at', 'employer_email', 'datetime', 'location',)


def detailed_answer_link(detailed_answer):
    answer_type = models.Answer.Types.ALL[detailed_answer.answer_type]
    url = reverse(
        'admin:jepostulepipeline_{}_change'.format(detailed_answer.__class__.__name__.lower()),
        kwargs={'object_id': detailed_answer.id},
    )
    return format_html("<a href='{url}'>{type}</a>", url=url, type=answer_type)

def answer_email_link(answer):
    url = reverse(
        'pipeline:email_answer',
        kwargs={'answer_id': answer.id}
    )
    return format_html("<a href='{url}' target='_blank' rel='noopener'>Email</a>", url=url)
