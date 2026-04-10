from django.contrib import admin
from .models import *

admin.site.register(Session)
admin.site.register(Question)
admin.site.register(Profile)
admin.site.register(QuestionAttempt)
admin.site.register(PageView)
admin.site.register(WebsiteSession)
admin.site.register(CursorEvent)
admin.site.register(DeletionEvent)
admin.site.register(EndSurveyResponse)
admin.site.register(SystemHint)
admin.site.register(MCQResponse)



# Register your models here.
