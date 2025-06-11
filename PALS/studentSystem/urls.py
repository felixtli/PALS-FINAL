from django.urls import path
from studentSystem import views

urlpatterns = [
    path("", views.home, name="home"), # Path to homepages
    path("signup/", views.signupView, name="signup"), # Path to signup screen
    path("login/", views.loginView, name="login"), # Path to login screen
    path("<int:id>/chat/", views.chat, name="chat"), # Path to each chat session, which takes an argument for the id of the session
    path("codesubmission/", views.codeSubmit, name="codeSubmit"), # Path to code submission page
    path('<int:id>/chat/add-chat/', views.updateChat, name='updateChat'), # Path to call the function to save a new chat to the database
    path('<int:id>/chat/next-response/', views.getAIResponse, name='nextResponse') # Path to get the next AI response
]