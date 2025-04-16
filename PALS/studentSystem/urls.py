from django.urls import path
from studentSystem import views

urlpatterns = [
    path("", views.home, name="home"),
    path("codesubmission/", views.codeSubmit, name="codeSubmit"),
    # path("nextResponse", views.nextResponse, name="nextResponse"), <-- Path for chatbot function
]