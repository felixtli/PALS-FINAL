from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from .models import Session
import json
from django.views.decorators.csrf import csrf_exempt
from .chatbot import generateResponse
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from django.contrib.auth import login
from .compiler import compileCode

def home(request): # Unfinished home page
    return render(request, "studentSystem/index.html")

def signupView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user) 

            # session = Session.objects.create(user=new_user)
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

def dashboard(request):
    currentUser = request.user
    sessions = Session.objects.filter(user=currentUser).order_by('id') # Get all sessions for the current user, ordered by creation date
    context = {
        "sessions" : sessions,
        "user" : currentUser
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
        "chatID" : id,
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
    
def codeSubmit(request, id): # Unfinished code submission page
    session = Session.objects.get(pk = id) # Current session and associated fields
    submission = json.dumps(session.codeSubmission) # Chats of the current session
    context = {
        "codeSubmission" : submission
    }
    print(session.codeSubmission)
    return render(request, "studentSystem/codeSubmit.html", context)
    
def runCompile(request):
    if request.method == "POST":
        body = json.loads(request.body)
        submission = body.get("submission")
        compiled_output = str(compileCode(submission))
        print (compiled_output)
        return JsonResponse({"compiled_output" : compiled_output})
    
        



