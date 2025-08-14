from django.db import models
from django.contrib.auth.models import User

class Question (models.Model):
    question_title = models.CharField(max_length = 255, default="Question_Title", primary_key=True)
    question_description = models.CharField(max_length = 1000, default="Description Missing")
    test_cases = models.JSONField(default=list)
    target_function = models.CharField(max_length = 100)

class Session (models.Model): # Object that holds a code submission and its corresponding chatlog
    user = models.ForeignKey(User, on_delete=models.CASCADE) # associates every new session object with a user
    title = models.CharField(max_length=255, default="Session")
    question = models.ForeignKey(  # associates session with a question
        Question,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    chatLog = models.JSONField(default=list, blank=True)
    codeSubmission = models.CharField(max_length=1000)