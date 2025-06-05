from django.db import models
from django.contrib.auth.models import User

class Session (models.Model): # Object that holds a code submission and its corresponding chatlog

    user = models.ForeignKey(User, on_delete=models.CASCADE) # associates every new session object with a user

    title = models.CharField(max_length = 255, default = "Session")
    chatLog = models.JSONField(default=list, blank=True)
    codeSubmission = models.CharField(max_length=1000)

