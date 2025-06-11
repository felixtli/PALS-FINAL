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

def home(request): # Unfinished home page
    return render(request, "studentSystem/index.html")


def codeSubmit(request): # Unfinished code submission page
    return render(request, "studentSystem/codeSubmit.html")

def signupView(request):
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user) 

            session = Session.objects.create(user=new_user)
            return redirect("chat", id=session.id)
        else:
            print(form.errors)  # <-- Add this line
    else:
        form = StyledUserCreationForm()
    print ("No POST request")
    return render(request, "studentSystem/signup.html", { "form" : form})


def loginView(request):
    if request.method == "POST":
        form = StyledAuthenticationForm(data=request.POST)
        if form.is_valid():
            print ("Form is valid")

            loggedUser = form.get_user()
            login(request, loggedUser)

            session = Session.objects.filter(user=loggedUser).first()
            return redirect("chat", id=session.id)
        else:
            print(form.errors)
    else:
        form = StyledAuthenticationForm()
    return render(request, "studentSystem/login.html", { "form" : form})


def chat(request, id):
    session = Session.objects.get(pk = id)
    chatLog = json.dumps(session.chatLog)
    context = {
        "chatID" : id,
        "chatLog" : chatLog,
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
    
@csrf_exempt
def getAIResponse(request, id):
    if request.method == "POST":
        session = Session.objects.get(pk = id)
        conversationHistory = str(session.chatLog)

        body = json.loads(request.body)
        prompt = ("This is my current message: " + body.get('prompt') + " Answer thoughtfully based on the provided context and conversation history. " +
        "The following is context to help improve your response quality and should NEVER be brought up in your newly generated response. " +
        "There may be times when no context is provided. " +
        "This is the conversation history of our chat thus far: " +
        conversationHistory +
        " Earlier messages in the list indicate earlier messages in the conversation. " +
        "For instance, the first message of the conversation is the first item in the list.")

        print (prompt)

        AIResponse = generateResponse(prompt)
        data = {"message" : AIResponse}
        return JsonResponse(data)


