from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from .models import Session, Profile, Question, QuestionAttempt
import json
from django.views.decorators.csrf import csrf_exempt
from .chatbot import generateResponse
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from django.contrib.auth import login, logout
from .compiler import compileCode, handler
from .question_assignment import initialQuestion, assignment
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest
from json import JSONDecodeError
from django.db import transaction


def home(request): # Unfinished home page
    return render(request, "studentSystem/index.html")

def signupView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user) 

            return redirect("dashboard") # Redirect to the dashboard after signup
        else:
            print(form.errors)  # <-- Add this line
    else:
        form = StyledUserCreationForm()
    print ("No POST request")
    return render(request, "studentSystem/signup.html", { "form" : form})


def loginView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledAuthenticationForm(data=request.POST)
        if form.is_valid():
            print ("Form is valid")

            loggedUser = form.get_user()
            login(request, loggedUser)

            session = Session.objects.filter(user=loggedUser).first()
            return redirect("dashboard")
        else:
            print(form.errors)
    else:
        form = StyledAuthenticationForm()
    return render(request, "studentSystem/login.html", { "form" : form})

def logoutView(request):
    logout(request) 
    return redirect("home") 

def dashboard(request):
    currentUser = request.user
    currentProfile = Profile.objects.get(user=currentUser) # Get the current user's profile

    sessions = Session.objects.filter(user=currentUser).order_by('-id') # All sessions associated with the user, ordered by most recent
    pastQuestions = currentProfile.question_history.all().order_by('-pk')
    nextQuestions = currentProfile.next_questions.all() # All next questions assigned to the user

    if not nextQuestions.exists(): # TODO: Change this condition to be based off of nextQuestions instead
        initialQuestion(currentProfile)
        nextQuestions = currentProfile.next_questions.all()

        queuedQuestion = nextQuestions.first()
        attempt = QuestionAttempt.objects.create(
            associated_profile=currentProfile,
            question=queuedQuestion,
            solved_test_cases=0,
            session=Session.objects.create(user=currentUser, question=queuedQuestion)
        )
        currentProfile.question_history.add(attempt)
        currentProfile.next_questions.remove(nextQuestions.first()) # Remove the assigned question after adding it to the history

    # TODO: Get the next questions necessary and render them on the dashboard
    elif nextQuestions.exists():
        attempt = QuestionAttempt.objects.create(
            associated_profile=currentProfile,
            question=nextQuestions.first(),
            solved_test_cases=0,
            session=Session.objects.create(user=currentUser, question=nextQuestions.first())
        )
        currentProfile.question_history.add(attempt) # Add the new attempt to the user's question history
        currentProfile.next_questions.remove(nextQuestions.first()) # Remove the assigned question after adding it to the history

    currentQuestion = currentProfile.question_history.latest('created_at')
    print (currentQuestion)

    pastQuestions = currentProfile.question_history.all().order_by('-pk') [1:] # Exclude the current question from past questions & order by most recent

    context = {
        "sessions" : sessions,
        "user" : currentUser,
        "pastQuestions" : pastQuestions,
        "currentQuestion" : currentQuestion,
    }
    return render(request, "studentSystem/dashboard.html", context)

def createChat (request):
    currentUser = request.user
    session = Session.objects.create(user=currentUser)
    return redirect('chat', id=session.pk)

def chat(request, id):
    session = Session.objects.get(pk = id) # Current session and associated fields
    chatLog = json.dumps(session.chatLog) # Chats of the current session
    existingChats = Session.objects.filter(user=session.user).exclude(pk=id) # Other chats asssociated with the user

    context = {
        "session" : session,
        "sessionID" : id,
        "chatLog" : chatLog,
        "existingChats" : existingChats
    }
    print (context)
    return render(request, "studentSystem/chat.html", context)

@csrf_exempt # for testing purposes. Use CSRF tokens in deployment.
def updateChat(request, id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_chat = data.get('chat')
            session = Session.objects.get(pk = id)

            if not isinstance(session.chatLog, list):
                session.chatLog = []
            session.chatLog.append(new_chat) 
            session.save()

            return JsonResponse({'status': 'success'})
        except Session.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
@csrf_exempt # for testing purposes. Use CSRF tokens in deployment.
def getAIResponse(request, id):
    if request.method == "POST":
        session = Session.objects.get(pk = id)
        conversationHistory = str(session.chatLog)

        body = json.loads(request.body)
        prompt = ("This is my current message: " + body.get('prompt') +
        " This is the conversation history of our chat thus far: " +
        conversationHistory +
        " Every odd entry in the list is a message from the user, while every even entry is a response from the AI. " +
        "The AI should always respond in a way that is helpful and relevant to the user's messages.")

        print (prompt)

        AIResponse = generateResponse(prompt)
        data = {"message" : AIResponse}
        return JsonResponse(data)
    
def codeSubmit(request, id):
    session = Session.objects.get(pk = id) 
    submission = session.codeSubmission
    context = {
        "codeSubmission" : submission,
        "session" : session,
    }
    return render(request, "studentSystem/codeSubmit.html", context)

def saveSubmission(request, id):
    session = Session.objects.get(pk = id)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
            new_submission = body.get("submission")

            session.codeSubmission = new_submission
            session.save()

            return JsonResponse({'status': 'success'})
        except Session.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def askAI(request, id):
    if request.method == "POST":
        print ("here")

        body = json.loads(request.body)

        print (body)
        submission = body.get("submission")
        print (submission)
        compiler_output = body.get("compiler_output")

        response = generateResponse("Analyze the following StandardML code: " + submission
                                    +"This what the code currently outputs: " + compiler_output
                                    +"If there is an error, explain what the error means and how to fix it." + 
                                    " If there is no error, suggest improvements to the code or optimizations that can be made.")
        return JsonResponse({"AI_response" : response})


def runCompile(request): # TODO - Save compiler output to session
    if request.method == "POST":
        body = json.loads(request.body)
        submission = body.get("submission")
        compiled_output = str(compileCode(submission))
        print (compiled_output)
        return JsonResponse({"compiled_output" : compiled_output})
    
def runTestCases(request, id):
    if request.method == "POST":
        print("hello there")

        profile = request.user.profile
        assignment(profile)
        print (profile.next_questions.all())

        return JsonResponse({"status" : "success"})
    
def tester(request, id): # Temporary view for testing compiler features
    currentProfile = Profile.objects.get(user=request.user) # Get the current user's profile
    nextQuestions = currentProfile.next_questions.all()
    session = Session.objects.get(pk = id)

    handler(currentProfile, currentProfile.question_history.latest('id'), session=session)
    return redirect("dashboard")





