from django.contrib import admin
from core.models import AuditLog
from .models import Answer, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_visible", "created_at", "updated_at"]
    list_filter = ["is_visible", "created_at"]
    search_fields = ["title", "body", "author__username"]
    actions = ["show_questions", "hide_questions"]

    @admin.action(description="Show selected questions")
    def show_questions(self, request, queryset):
        for question in queryset:
            question.is_visible = True
            question.save(update_fields=["is_visible"])
            AuditLog.objects.create(actor=request.user, action="question_shown", object_type="Question", object_id=str(question.pk))

    @admin.action(description="Hide selected questions")
    def hide_questions(self, request, queryset):
        for question in queryset:
            question.is_visible = False
            question.save(update_fields=["is_visible"])
            AuditLog.objects.create(actor=request.user, action="question_hidden", object_type="Question", object_id=str(question.pk))


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "author", "is_accepted", "is_visible", "created_at"]
    list_filter = ["is_accepted", "is_visible", "created_at"]
    search_fields = ["body", "author__username", "question__title"]
    actions = ["show_answers", "hide_answers"]

    @admin.action(description="Show selected answers")
    def show_answers(self, request, queryset):
        for answer in queryset:
            answer.is_visible = True
            answer.save(update_fields=["is_visible"])
            AuditLog.objects.create(actor=request.user, action="answer_shown", object_type="Answer", object_id=str(answer.pk))

    @admin.action(description="Hide selected answers")
    def hide_answers(self, request, queryset):
        for answer in queryset:
            answer.is_visible = False
            answer.is_accepted = False
            answer.save(update_fields=["is_visible", "is_accepted"])
            AuditLog.objects.create(actor=request.user, action="answer_hidden", object_type="Answer", object_id=str(answer.pk))

# Register your models here.
