from django.urls import path
from studentSystem import views

urlpatterns = [
    path("", views.home, name="home"), # Homepages
    path("analytics/track-time/", views.track_time, name="track_time"), # Track time spent on page
    path("signup/", views.signupView, name="signup"), # Signup screen
    path("login/", views.loginView, name="login"), # Login screen
    path("logout/", views.logoutView, name="logout"), # Logout function
    path("dashboard/", views.dashboard, name="dashboard"), # Dashboard after login
    path('create-chat/', views.createChat, name='createChat'), # Function to create a new chat session
    path("<int:id>/chat/", views.chat, name="chat"), # Each chat session, which takes an argument for the id of the session
    path("<int:id>/codesubmission/", views.codeSubmit, name="codeSubmit"), # Code submission page
    path("<int:id>/save/", views.saveSubmission, name="saveSubmission"), # Function to save the current code submission
    path("<int:id>/ask-ai/", views.askAI, name="askAI"), # Function to ask the AI for help
    path("compile/", views.runCompile, name="runCompile"), # Function to compile the current code submission
    path("<int:id>/submit-code/", views.submitCode, name="submitCode"), # Function to submit the current code submission
    path('<int:id>/chat/add-chat/', views.updateChat, name='updateChat'), # Function to save a new chat to the database
    path('<int:id>/chat/next-response/', views.getAIResponse, name='nextResponse') # Function to get the next AI response
]