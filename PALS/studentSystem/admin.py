from django.contrib import admin
from .models import Session, Question, Profile, QuestionAttempt

admin.site.register(Session)
admin.site.register(Question)
admin.site.register(Profile)
admin.site.register(QuestionAttempt)



# Register your models here.
