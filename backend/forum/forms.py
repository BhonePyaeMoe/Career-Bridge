from django import forms
from .models import Answer, Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 7})}


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["body"]
        labels = {"body": "Your answer"}
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}
