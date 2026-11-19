from django.conf import settings
from django.db import models
from django.db.models import Q


class Question(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers")
    body = models.TextField()
    is_visible = models.BooleanField(default=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_accepted", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["question"],
                condition=Q(is_accepted=True),
                name="one_accepted_answer_per_question",
            )
        ]

    def __str__(self):
        return f"Answer to {self.question.title}"

# Create your models here.
