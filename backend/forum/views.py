from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from core.models import AuditLog
from .forms import AnswerForm, QuestionForm
from .models import Answer, Question


def question_list(request):
    questions = Question.objects.filter(is_visible=True).select_related("author").annotate(
        visible_answer_count=Count("answers", filter=Q(answers__is_visible=True))
    )
    keyword = request.GET.get("keyword", "").strip()
    if keyword:
        questions = questions.filter(Q(title__icontains=keyword) | Q(body__icontains=keyword))
    questions = questions.order_by("-created_at")
    page_obj = Paginator(questions, 10).get_page(request.GET.get("page"))
    return render(request, "forum/question_list.html", {"page_obj": page_obj})


def question_detail(request, pk):
    question = get_object_or_404(Question.objects.select_related("author"), pk=pk, is_visible=True)
    answers = question.answers.filter(is_visible=True).select_related("author")
    form = AnswerForm()
    return render(request, "forum/question_detail.html", {"question": question, "answers": answers, "form": form})


@login_required
def question_create(request):
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.author = request.user
        question.save()
        AuditLog.objects.create(actor=request.user, action="question_created", object_type="Question", object_id=str(question.pk))
        messages.success(request, "Question posted.")
        return redirect("forum:detail", pk=question.pk)
    return render(request, "forum/question_form.html", {"form": form, "heading": "Ask a question"})


@login_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk, author=request.user)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid():
        form.save()
        AuditLog.objects.create(actor=request.user, action="question_edited", object_type="Question", object_id=str(question.pk))
        messages.success(request, "Question updated.")
        return redirect("forum:detail", pk=question.pk)
    return render(request, "forum/question_form.html", {"form": form, "heading": "Edit question"})


@login_required
def answer_create(request, question_id):
    question = get_object_or_404(Question, pk=question_id, is_visible=True)
    if request.method != "POST":
        return redirect("forum:detail", pk=question.pk)
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(commit=False)
        answer.question = question
        answer.author = request.user
        answer.save()
        AuditLog.objects.create(actor=request.user, action="answer_created", object_type="Answer", object_id=str(answer.pk))
        messages.success(request, "Answer posted.")
    else:
        messages.error(request, "Answer cannot be empty.")
    return redirect("forum:detail", pk=question.pk)


@login_required
def answer_edit(request, pk):
    answer = get_object_or_404(Answer.objects.select_related("question"), pk=pk, author=request.user)
    form = AnswerForm(request.POST or None, instance=answer)
    if request.method == "POST" and form.is_valid():
        form.save()
        AuditLog.objects.create(actor=request.user, action="answer_edited", object_type="Answer", object_id=str(answer.pk))
        messages.success(request, "Answer updated.")
        return redirect("forum:detail", pk=answer.question_id)
    return render(request, "forum/answer_form.html", {"form": form, "answer": answer})


@login_required
def accept_answer(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    answer = get_object_or_404(Answer.objects.select_related("question"), pk=pk, is_visible=True)
    if answer.question.author != request.user:
        raise PermissionDenied
    with transaction.atomic():
        Answer.objects.filter(question=answer.question, is_accepted=True).update(is_accepted=False)
        answer.is_accepted = True
        answer.save(update_fields=["is_accepted"])
        AuditLog.objects.create(actor=request.user, action="answer_accepted", object_type="Answer", object_id=str(answer.pk))
    messages.success(request, "Answer marked as accepted.")
    return redirect("forum:detail", pk=answer.question_id)
