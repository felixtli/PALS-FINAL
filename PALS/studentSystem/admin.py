from django.contrib import admin
from .models import Session, Question, Profile, QuestionAttempt, PageView

admin.site.register(Session)
admin.site.register(Question)
admin.site.register(Profile)
admin.site.register(QuestionAttempt)
admin.site.register(PageView)



# Register your models here.
