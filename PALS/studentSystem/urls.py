from django.urls import path
from studentSystem import views

urlpatterns = [
    path("", views.home, name="home"), # Homepages
    path("signup/", views.signupView, name="signup"), # Signup screen
    path("login/", views.loginView, name="login"), # Login screen
    path('create-chat/', views.createChat, name='createChat'), # Function to create a new chat session
    path("<int:id>/chat/", views.chat, name="chat"), # Each chat session, which takes an argument for the id of the session
    path("codesubmission/", views.codeSubmit, name="codeSubmit"), # Code submission page
    path('<int:id>/chat/add-chat/', views.updateChat, name='updateChat'), # Function to save a new chat to the database
    path('<int:id>/chat/next-response/', views.getAIResponse, name='nextResponse') # Function to get the next AI response
]