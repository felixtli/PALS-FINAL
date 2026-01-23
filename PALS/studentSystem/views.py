from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from .models import *
import json
from django.views.decorators.csrf import csrf_exempt
from .chatbot import generateResponse, generateCloudResponse
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from django.contrib.auth import login, logout
from .compiler import compileCode, handler
from .question_assignment import initialQuestion, assignment
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest
from json import JSONDecodeError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.db.models.functions import Random


def home(request): 
    return render(request, "studentSystem/index.html")

def signupView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user)

            # Call initialization logic
            currentProfile = Profile.objects.get(user=new_user)
            initialQuestion(currentProfile)

            # Queue the first set of questions
            nextQuestions = currentProfile.next_questions.all()

            if nextQuestions.exists():
                queuedQuestion = nextQuestions.first()
                session = Session.objects.create(user=new_user, question=queuedQuestion)

                session.codeSubmission = (
                    queuedQuestion.target_function_definition +
                    " (* <- Keep the provided function name. It needs to be maintained for the compiler to work properly. *)"
                )
                session.save()

                attempt = QuestionAttempt.objects.create(
                    associated_profile=currentProfile,
                    question=queuedQuestion,
                    solved_test_cases=0,
                    session=session
                )
                currentProfile.question_history.add(attempt)
                currentProfile.next_questions.remove(queuedQuestion)

            # Render the dashboard like a GET
            return redirect("/dashboard/")  

        else:
            pass
    else:
        form = StyledUserCreationForm()
    return render(request, "studentSystem/signup.html", {"form": form})


def loginView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledAuthenticationForm(data=request.POST)
        if form.is_valid():
            loggedUser = form.get_user()
            login(request, loggedUser)

            session = Session.objects.filter(user=loggedUser).first()
            return redirect("dashboard")
        else:
            pass
    else:
        form = StyledAuthenticationForm()
    return render(request, "studentSystem/login.html", { "form" : form})

def logoutView(request):
    logout(request) 
    return redirect("home") 
 
def dashboard(request): # TODO: Style "# of cases passed" tooltips to float above past problem blocks
    currentUser = request.user
    currentProfile = Profile.objects.get(user=request.user) # Get the current user's profile
    sessions = Session.objects.filter(user=currentUser).order_by('-pk') # All sessions associated with the user, ordered by most recent
    nextQuestions = currentProfile.next_questions.all()

    request_type = None
    if request.method == "POST": # Use POST request to request the next question
        if request.content_type == "application/json":
            body = json.loads(request.body.decode("utf-8"))
            request_type = body.get("request_type")
        else:
            request_type = request.POST.get("request_type")

        if request_type == "next_question" and nextQuestions.exists():
            queuedQuestion = nextQuestions.first()

            attempt = QuestionAttempt.objects.create(
                associated_profile=currentProfile,
                question=queuedQuestion,
                solved_test_cases=0,
                session=Session.objects.create(user=currentUser, question=queuedQuestion)
            )

            currentProfile.question_history.add(attempt)
            currentProfile.next_questions.remove(nextQuestions.first())

        elif request_type == "next_question" and not nextQuestions.exists():
            assignment(currentProfile)
            queuedQuestion = nextQuestions.first()

            attempt = QuestionAttempt.objects.create(
                associated_profile=currentProfile,
                question=queuedQuestion,
                solved_test_cases=0,
                session=Session.objects.create(user=currentUser, question=queuedQuestion)
            )

            currentProfile.question_history.add(attempt)
            currentProfile.next_questions.remove(nextQuestions.first())

        currentQuestionAttempt = currentProfile.question_history.latest('created_at')
        currentQuestionAttempt.session.codeSubmission = currentQuestionAttempt.question.target_function_definition + " (* <- Keep the provided function name. It needs to be maintained for the compiler to work properly. *)"
        currentQuestionAttempt.session.save()

    currentQuestionAttempt = currentProfile.question_history.latest('created_at')
    
    pastQuestions = currentProfile.question_history.all().order_by('-pk') [1:] # Exclude the current question from past questions & order by most recent

    context = {
        "sessions" : sessions,
        "user" : currentUser,
        "pastQuestions" : pastQuestions,
        "currentQuestion" : currentQuestionAttempt,
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
    return render(request, "studentSystem/chat.html", context)

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
    
def getAIResponse(request, id):
    if request.method == "POST":
        session = Session.objects.get(pk = id)
        conversationHistory = session.chatLog
        question_description = session.question.question_description

        conversationHistory.insert(0, {"role": "system", "content": "You are a helpful programming assistant that has expertise in StandardML."
                                    + "\nThe user will ask you for help on a programming question." +
                                    "\nNever provide a complete working solution or full function definition."
                                    + "\nYou may provide at most 3–5 lines of code at a time, and only as illustrative fragments."
                                    + "\nFocus on algorithm, decomposition, invariants, test cases, and debugging steps."
                                    + "\nIf you do suggest a code change, it is vital that you explain the details of why you made that change."})
        conversationHistory.insert(1, {"role": "assistant", "content": "Hello, I am a helpful programming assistant specialized in StandardML! Let me know if you have any questions about the language, and I'm here to help!"})
        for entry in range(2, len(conversationHistory)):
            if entry % 2 == 1:
                conversationHistory[entry] = {"role": "assistant", "content": conversationHistory[entry]}
            else:
                conversationHistory[entry] = {"role": "user", "content": conversationHistory[entry]}

        body = json.loads(request.body)
        prompt = (body.get('prompt')) 
        conversationHistory.append({"role": "user", "content": prompt})

        ai_response = generateCloudResponse(conversationHistory)
        data = {"message" : ai_response}
        return JsonResponse(data)
    
def codeSubmit(request, id): # TODO: Add tooltips to buttons
    session = Session.objects.get(pk = id) 
    submission = session.codeSubmission
    context = {
        "codeSubmission" : submission,
        "session" : session,
        "nextSession" : id + 1,
        "previousSession" : id - 1,
    }
    return render(request, "studentSystem/codeSubmit.html", context)

@csrf_exempt
def saveSubmission(request, id):
    try:
        session = Session.objects.get(pk=id)
    except Session.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
            new_submission = body.get("submission")

            session.codeSubmission = new_submission
            session.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print("Parse error:", e)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def askAI(request, id):
    if request.method == "POST":

        body = json.loads(request.body)

        submission = body.get("submission")
        compiler_output = body.get("compiler_output")
        question_description = Session.objects.get(pk=id).question.question_description

        response = generateCloudResponse([{"role": "system", "content": "You are a helpful programming assistant that has expertise in StandardML."
                                    + "\nThe user will ask you for help on a programming question." +
                                    "\nNever provide a complete working solution or full function definition."
                                    + "\nYou may provide at most 3–5 lines of code at a time, and only as illustrative fragments."
                                    + "\nFocus on algorithm, decomposition, invariants, test cases, and debugging steps."
                                    + "\nIf you do suggest a code change, it is vital that you explain the details of why you made that change."},
                                      {"role" : "user", "content" : "\nAnalyze the following StandardML code: " + submission
                                    +"\nThis what the code currently outputs in the compiler when it is run: " + compiler_output
                                    +"\nIf there is an error, explain what the error means and how to fix it." + 
                                    " \nIf there is no error, suggest improvements to the code or optimizations that can be made." }])
        return JsonResponse({"AI_response" : response})

@require_POST
def save_system_hint(request, id):
    try:
        session = Session.objects.get(pk=id)
    except Session.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Session not found"}, status=404)

    if not request.user.is_authenticated or session.user_id != request.user.id:
        return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

    try:
        print ("WE GOT TO THE MAIN VIEW")
        body = json.loads(request.body.decode("utf-8"))
        contents = (body.get("contents") or "").strip()
        if not contents:
            return JsonResponse({"status": "error", "message": "Empty contents"}, status=400)

        SystemHint.objects.create(
            user=request.user,
            session=session,
            contents=contents,
            code_contents=session.codeSubmission # This line may cause issues
        )

        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def runCompile(request): 
    if request.method == "POST":
        body = json.loads(request.body)
        submission = body.get("submission")
        print (submission)
        compiled_output = str(compileCode(submission))
        return JsonResponse({"compiled_output" : compiled_output})

def submitCode(request, id):
    if request.method == "POST": 
        currentProfile = Profile.objects.get(user=request.user)
        session = Session.objects.get(pk=id)

        casesSolved = handler(currentProfile, session=session)

        return JsonResponse({"status": "ok", "casesSolved": casesSolved})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def user_survey(request, id):
    session = Session.objects.get(pk = id)
    attempt = QuestionAttempt.objects.get(session=session)
    solved_test_cases = attempt.solved_test_cases
    context = {
        "session_id" : id,
        "solved_test_cases": solved_test_cases
    }
    return render(request, "studentSystem/userSurvey.html", context)

def post_survey_response(request, id):
    if request.method == "POST":
        print ("Successfully got to view")
        body = json.loads(request.body)
        survey_response = body.get("survey_response")
        session = Session.objects.get(pk = id)
        attempt = QuestionAttempt.objects.get(session=session)
        attempt.survey_response = survey_response
        attempt.save()
        return JsonResponse({"status": "ok"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@csrf_exempt  # Using sendBeacon, so CSRF token is not available
def track_page_time(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    # Total time from page load until submit, in ms
    duration_ms = int(max(0, data.get("duration_ms", 0)))
    path = data.get("path") or request.path

    started_at_ms = data.get("started_at_ms")
    if started_at_ms:
        started_at = timezone.datetime.fromtimestamp(started_at_ms / 1000)
        ended_at = started_at + timezone.timedelta(milliseconds=duration_ms)
    else:
        ended_at = timezone.now()
        started_at = ended_at - timezone.timedelta(milliseconds=duration_ms)

    session_key = getattr(getattr(request, "session", None), "session_key", None) \
                  or request.COOKIES.get("sessionid", "")

    # We want one record per submit, so create() is used
    page_view = PageView.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key or "",
        path=path,
        referrer=data.get("referrer", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        extra={
            "visible_only": bool(data.get("visible_only", True)),
            "idle_threshold_ms": data.get("idle_threshold_ms", 120000),
            "trigger": "submit",
        },
    )
    print ("Created page view!")

    return JsonResponse({"ok": True})

@csrf_exempt
# TODO: Fix error where the session key stays the same if a user tries multiple different accounts in the same browser session
# This is causing us to mix up website session data between different users
def track_website_time(request): 
    print ("Successfully got to website time view")
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        print ("Data received: " + str(data))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    session_key = data.get("session_key") or request.COOKIES.get("sessionid", "")
    duration_ms = int(max(0, data.get("duration_ms", 0)))
    print ("About to increment: " + str(duration_ms))

    # Create or update the session
    session, created = WebsiteSession.objects.get_or_create(
        session_key=session_key,
        defaults={
            "user": request.user if request.user.is_authenticated else None,
        },
    )
    print (session)
    print (WebsiteSession.objects.filter(session_key=session_key).count())
    if duration_ms > 0:
        WebsiteSession.objects.filter(pk=session.pk).update(
            total_active_ms=F("total_active_ms") + duration_ms,
            last_ping=timezone.now()
        )

    return JsonResponse({"ok": True})

def track_cursor(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    points = data.get("points", [])
    path = data.get("path", "")
    session_id = data.get("session_id", "")

    user = request.user if request.user.is_authenticated else None

    events = []
    for p in points:
        try:
            events.append(CursorEvent(
                user=user,
                session_id=session_id,
                path=path,
                x=p["x"],
                y=p["y"],
                viewport_width=p["vw"],
                viewport_height=p["vh"],
                scroll_y=p["sy"],
            ))
        except KeyError:
            continue

    if events:
        CursorEvent.objects.bulk_create(events)

    return JsonResponse({"status": "ok", "saved": len(events), "timestamp": timezone.now().isoformat()})

def track_deletion(request):
    print ("Successfully got to deletion view")

    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        session_id = int(data.get("session_id", ""))
        user = request.user if request.user.is_authenticated else None
        timestamp = timezone.now()

        DeletionEvent.objects.create(
            user = user,
            session = Session.objects.get(pk=session_id),
            position = data.get("position", 0),
            length = data.get("length", 0),
            deleted_content = data.get("deleted_content", ""),
            new_content = data.get("new_content", ""),
            timestamp = timestamp,
            old_code = data.get("old_code"),
            new_code = data.get("new_code"),
        )

    except Exception:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)
    
    return JsonResponse({"status": "ok", "data_received": data})

def post_experiment_survey(request):
    return render(request, "studentSystem/userEndSurvey.html")

def post_experiment_survey_submission(request):
    try:
        body = json.loads(request.body)
        data = body.get("survey_response", {})

        survey = EndSurveyResponse.objects.create(
            user=request.user if request.user.is_authenticated else None,

            # ======================
            # A. Background
            # ======================
            courses_completed=data.get("courses_completed"),
            years_experience=data.get("years_experience"),
            ml_familiarity=data.get("ml_familiarity"),
            current_fatigue=data.get("current_fatigue"),

            # ======================
            # B. Usability
            # ======================
            ease_of_use=data.get("ease_of_use"),
            feedback_helpfulness=data.get("feedback_helpfulness"),
            challenge_match=data.get("challenge_match"),
            reuse_intent=data.get("reuse_intent"),

            # ======================
            # C. Engagement & Attention
            # ======================
            focus_level=data.get("focus_level"),
            time_distortion=data.get("time_distortion"),

            # ======================
            # D. Cognitive Load
            # ======================
            mental_demand=data.get("mental_demand"),
            effort=data.get("effort"),
            frustration=data.get("frustration"),

            # ======================
            # E. Trust & Fairness
            # ======================
            trusted_system=data.get("trusted_system"),
            fairness_of_system=data.get("fairness"),

            # ======================
            # F. Adaptive Features
            # ======================
            adaptation_quality=data.get("adaptation_quality"),
            adaptive_hint_helpfulness=data.get("adaptive_hint_helpfulness"),

            # ======================
            # G. Open-Ended Feedback
            # ======================
            liked_most=data.get("liked_most", ""),
            liked_least=data.get("liked_least", ""),
            change_one_thing=data.get("change_one_thing", ""),
            additional_comments=data.get("additional_comments", ""),

            # ======================
            # H. Manipulation Check
            # ======================
            difficulty_notice=data.get("difficulty_notice"),
        )

        return JsonResponse({
            "status": "ok",
            "survey_id": survey.id
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


def final_FRQ(request):
    """
    Serves the current FRQ question in the user's final queue.
    Queue is stored in request.session so clicking submit can advance to the next.
    """
    user = request.user if request.user.is_authenticated else None
    if user is None:
        return redirect("login")  # or wherever you want unauth users to go

    profile = get_object_or_404(Profile, user=user)

    # Initialize queue once (3 random difficulty=4 questions)
    if "final_frq_queue" not in request.session or "final_frq_index" not in request.session:
        q_ids = list(
            Question.objects.filter(difficulty=4)
            .order_by(Random())
            .values_list("pk", flat=True)[:3]
        )
        request.session["final_frq_queue"] = q_ids
        request.session["final_frq_index"] = 0

    queue = request.session.get("final_frq_queue", [])
    idx = int(request.session.get("final_frq_index", 0))

    # If done, go to final page
    if idx >= len(queue) or not queue:
        return redirect("final")

    question = get_object_or_404(Question, pk=queue[idx])

    # Create a fresh session/attempt for THIS FRQ question page-load
    session = Session.objects.create(
        user=user,
        question=question
    )

    attempt = QuestionAttempt.objects.create(
        associated_profile=profile,
        question=question,
        session=session
    )

    submission = question.target_function_definition

    context = {
        "session": session,
        "codeSubmission": submission,
    }
    return render(request, "studentSystem/finalFRQ.html", context)

@require_POST
def final_frq_advance(request):
    """
    Advances the user's FRQ index by 1 and returns the next URL.
    Called by JS after grading succeeds.
    """
    user = request.user if request.user.is_authenticated else None
    if user is None:
        return JsonResponse({"status": "error", "message": "Not authenticated"}, status=401)

    queue = request.session.get("final_frq_queue", [])
    idx = int(request.session.get("final_frq_index", 0))

    idx += 1
    request.session["final_frq_index"] = idx

    if idx >= len(queue):
        return JsonResponse({"status": "ok", "next_url": "/final/"})  # or reverse("final")
    return JsonResponse({"status": "ok", "next_url": "/final-frq/"})  # or reverse("final_frq")

def final(request):
    return render(request, "studentSystem/final.html")

