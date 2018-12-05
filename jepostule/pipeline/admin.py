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
    search_fields = ('created_at', 'candidate_email', 'employer_email', 'job',)
    sortable_by = ('created_at', 'candidate_email', 'employer_email',)
    readonly_fields = ('employer_answer',)
    inlines = (JobApplicationEventInlineAdmin,)

    def employer_answer(self, obj):
        return answer_link(obj.answer)


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


@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'job_application',)
    list_display_links = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('id', 'view_answer', 'job_application', 'answerrejection', 'answerrequestinfo', 'answerinterview',)

    def view_answer(self, obj):
        return answer_link(obj)


@admin.register(models.AnswerRejection)
class AnswerRejectionAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'reason',)


@admin.register(models.AnswerRequestInfo)
class AnswerRequestInfoAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'employer_email',)


@admin.register(models.AnswerInterview)
class AnswerInterviewAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'employer_email', 'datetime', 'location',)


def answer_link(answer):
    # This will display "-" in case there is no answer
    url = reverse(
        'pipeline:email_answer',
        kwargs={'answer_id': answer.id}
    )
    value = models.Answer.Types.ALL[answer.get_details().answer_type]
    return format_html("<a href='{url}' target='_blank' rel='noopener'>Answer: {value}</a>", url=url, value=value)
