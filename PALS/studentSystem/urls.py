from django.urls import path
from studentSystem import views

urlpatterns = [
    path("", views.home, name="home"), # Homepages
    path("analytics/track-time/", views.track_page_time, name="track_page_time"), # Track time spent on page
    path("analytics/track-website-time/", views.track_website_time, name="track_website_time"), # Track overall website time
    path("analytics/track-cursor/", views.track_cursor, name="track_cursor"), # Track cursor movements
    path("analytics/track-deletion/", views.track_deletion, name="track_deletion"), # Track code deletions
    path("analytics/analytics-csv/", views.analyticsCSV, name="analyticsCSV"), # Download analytics CSV
    path("signup/", views.signupView, name="signup"), # Signup screen
    path("login/", views.loginView, name="login"), # Login screen
    path("logout/", views.logoutView, name="logout"), # Logout function
    path("dashboard/", views.dashboard, name="dashboard"), # Dashboard after login
    path('create-chat/', views.createChat, name='createChat'), # Function to create a new chat session
    path("<int:id>/chat/", views.chat, name="chat"), # Each chat session, which takes an argument for the id of the session
    path("<int:id>/codesubmission/", views.codeSubmit, name="codeSubmit"), # Code submission page
    path("<int:id>/survey/", views.user_survey, name="user_survey"), # User survey page
    path("<int:id>/post-survey-response/", views.post_survey_response, name="post_survey_response"), # Function to handle survey response submission
    path("<int:id>/save/", views.saveSubmission, name="saveSubmission"), # Function to save the current code submission
    path("<int:id>/ask-ai/", views.askAI, name="askAI"), # Function to ask the AI for help
    path("compile/", views.runCompile, name="runCompile"), # Function to compile the current code submission
    path("<int:id>/submit-code/", views.submitCode, name="submitCode"), # Function to submit the current code submission
    path('<int:id>/chat/add-chat/', views.updateChat, name='updateChat'), # Function to save a new chat to the database
    path('<int:id>/chat/next-response/', views.getAIResponse, name='nextResponse') # Function to get the next AI response
]