from django.contrib import admin
from .models import Session, Question, Profile, QuestionAttempt, PageView, WebsiteSession, CursorEvent

admin.site.register(Session)
admin.site.register(Question)
admin.site.register(Profile)
admin.site.register(QuestionAttempt)
admin.site.register(PageView)
admin.site.register(WebsiteSession)
admin.site.register(CursorEvent)



# Register your models here.
