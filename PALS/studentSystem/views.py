from django.shortcuts import render
# from studentSystem.chatbot import generateResponse
from django.http import JsonResponse

def home(request):
    return render(request, "studentSystem/index.html")

def codeSubmit(request):
    return render(request, "studentSystem/codeSubmit.html")

# Unfinished view function to call chatbot feature
""" def nextResponse(request):
    userInput = request.POST.get("userInput")
    aiOutput = generateResponse(userInput)
    return JsonResponse({'aiOutput': aiOutput}) """