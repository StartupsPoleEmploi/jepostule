from django.contrib import admin

from .models import FailedMessage, DelayedMessage
from . import topics


@admin.register(FailedMessage)
class FailedMessageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'created_at', 'status', 'topic', 'exception', 'traceback',)
    list_display_links = ('id', 'created_at',)
    list_filter = ('topic', 'status',)
    ordering = ('-created_at', 'status', 'topic',)
    search_fields = ('created_at', 'topic', 'exception', 'traceback',)
    sortable_by = ('created_at', 'topic', 'status',)
    actions = ('archive', 'retry_and_archive', 'retry_and_delete',)
    readonly_fields = ('created_at', 'topic', 'exception', 'traceback', 'value_readable',)

    def archive(self, request, queryset):
        for message in queryset:
            message.archive()

    def retry_and_archive(self, request, queryset):
        for message in queryset:
            topics.retry_and_archive(message)

    def retry_and_delete(self, request, queryset):
        for message in queryset:
            topics.retry_and_delete(message)


@admin.register(DelayedMessage)
class DelayedMessageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'created_at', 'until', 'topic',)
    list_display_links = ('id', 'created_at',)
    list_filter = ('topic',)
    ordering = ('-created_at', 'topic',)
    search_fields = ('created_at', 'topic',)
    sortable_by = ('created_at', 'topic',)
    actions = ('dequeue',)
    readonly_fields = ('created_at', 'topic', 'value_readable',)

    def dequeue(self, request, queryset):
        for message in queryset:
            topics.dequeue(message)
