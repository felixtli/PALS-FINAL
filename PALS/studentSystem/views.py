from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from .models import *
import json
from django.views.decorators.csrf import csrf_exempt
from .chatbot import generateCloudResponse
from .forms import StyledUserCreationForm, StyledAuthenticationForm
from django.contrib.auth import login, logout
from .compiler import compileCode, handler, categorize_error
from .question_assignment import assignment
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest
from json import JSONDecodeError
from django.db import transaction
from django.utils import timezone
from django.db.models.functions import Random
import logging
from django.core.exceptions import PermissionDenied


logger = logging.getLogger(__name__)


def user_has_ai_access(user):
    if not getattr(user, "is_authenticated", False):
        return False

    profile = getattr(user, "profile", None)
    return bool(profile and profile.user_type == "A")


def get_owned_session_or_404(user, session_id):
    return get_object_or_404(Session, pk=session_id, user=user)


def require_ai_access(user):
    if not user_has_ai_access(user):
        raise PermissionDenied("AI features are only available to Group A users.")


def home(request): 
    return render(request, "studentSystem/index.html")


def ensure_current_question_attempt(profile, user):
    try:
        logger.info(
            "ensure_current_question_attempt start profile_id=%s user_id=%s",
            getattr(profile, "id", None),
            getattr(user, "id", None),
        )

        current_attempt = profile.question_history.order_by("-created_at").first()
        if current_attempt is not None:
            logger.info(
                "existing question attempt found attempt_id=%s session_id=%s",
                current_attempt.id,
                current_attempt.session_id,
            )
            return current_attempt

        question_count = Question.objects.count()
        logger.info("question bank count=%s", question_count)
        if question_count == 0:
            return None

        queued_count_before = profile.next_questions.count()
        logger.info("queued questions before assignment=%s", queued_count_before)
        if queued_count_before == 0:
            assignment(profile)
            logger.info(
                "assignment completed queued questions after assignment=%s",
                profile.next_questions.count(),
            )

        queued_question = profile.next_questions.order_by('difficulty').first()
        if queued_question is None:
            logger.warning(
                "no queued question available after assignment profile_id=%s",
                getattr(profile, "id", None),
            )
            return None

        logger.info(
            "creating bootstrap session for question=%s",
            queued_question.question_title,
        )
        session = Session.objects.create(user=user, question=queued_question)
        session.codeSubmission = (
            queued_question.target_function_definition +
            " (* <- Keep the provided function name. It needs to be maintained for the compiler to work properly. *)"
        )
        session.save()

        attempt = QuestionAttempt.objects.create(
            associated_profile=profile,
            question=queued_question,
            solved_test_cases=0,
            session=session
        )
        profile.question_history.add(attempt)
        profile.next_questions.remove(queued_question)
        logger.info(
            "bootstrap attempt created attempt_id=%s session_id=%s",
            attempt.id,
            session.id,
        )
        return attempt
    except Exception:
        logger.exception(
            "ensure_current_question_attempt failed profile_id=%s user_id=%s",
            getattr(profile, "id", None),
            getattr(user, "id", None),
        )
        raise

def signupView(request): # TODO - Style error messages
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            try:
                new_user = form.save()
                logger.info("signup created user_id=%s username=%s", new_user.id, new_user.username)
                login(request, new_user)

                # Get current profile
                currentProfile = Profile.objects.get(user=new_user)

                currentProfile.user_type = form.cleaned_data["user_type"]
                currentProfile.save()
                logger.info("signup profile ready profile_id=%s", currentProfile.id)

                attempt = ensure_current_question_attempt(currentProfile, new_user)

                if attempt:
                    return redirect("codeSubmit", id=attempt.session.pk)
                return redirect("next_problem")
            except Exception:
                logger.exception("signupView failed during user bootstrap")
                raise

        else:
            logger.warning("signup form invalid errors=%s", form.errors.as_json())
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

            currentProfile = Profile.objects.get(user=loggedUser)
            attempt = ensure_current_question_attempt(currentProfile, loggedUser)

            if attempt:
                return redirect("codeSubmit", id=attempt.session.pk)
            return redirect("next_problem")
        else:
            pass
    else:
        form = StyledAuthenticationForm()
    return render(request, "studentSystem/login.html", { "form" : form})

def logoutView(request):
    logout(request) 
    return redirect("home") 
 
def dashboard(request): # TODO: Style "# of cases passed" tooltips to float above past problem blocks
    try:
        currentUser = request.user
        logger.info("dashboard load start user_id=%s authenticated=%s", getattr(currentUser, "id", None), currentUser.is_authenticated)
        currentProfile = Profile.objects.get(user=request.user) # Get the current user's profile
        logger.info("dashboard profile loaded profile_id=%s", currentProfile.id)
        currentQuestionAttempt = ensure_current_question_attempt(currentProfile, currentUser)
        if currentQuestionAttempt is None:
            logger.warning("dashboard has no current question attempt profile_id=%s", currentProfile.id)
            return render(request, "studentSystem/dashboard.html", {
                "sessions": Session.objects.filter(user=currentUser).order_by('-pk'),
                "user": currentUser,
                "pastQuestions": [],
                "currentQuestion": None,
                "questionBankLoaded": Question.objects.exists(),
            })

        sessions = Session.objects.filter(user=currentUser).order_by('-pk') # All sessions associated with the user, ordered by most recent
        nextQuestions = currentProfile.next_questions.all()
        attempt_count = currentProfile.question_history.count()
        completed_count = max(0, attempt_count - 1)
        logger.info(
            "dashboard state attempt_count=%s completed_count=%s queued_count=%s",
            attempt_count,
            completed_count,
            nextQuestions.count(),
        )

        if completed_count >= 6:
            return render(request, "studentSystem/userEndSurvey.html")

        request_type = None
        if request.method == "POST": # Use POST request to request the next question
            if request.content_type == "application/json":
                body = json.loads(request.body.decode("utf-8"))
                request_type = body.get("request_type")
            else:
                request_type = request.POST.get("request_type")

            if request_type == "next_question" and nextQuestions.exists():
                queuedQuestion = nextQuestions.order_by('difficulty').first()

                attempt = QuestionAttempt.objects.create(
                    associated_profile=currentProfile,
                    question=queuedQuestion,
                    solved_test_cases=0,
                    session=Session.objects.create(user=currentUser, question=queuedQuestion)
                )

                currentProfile.question_history.add(attempt)
                currentProfile.next_questions.remove(queuedQuestion)

            elif request_type == "next_question" and not nextQuestions.exists():

                assignment(currentProfile)
                queuedQuestion = currentProfile.next_questions.order_by('difficulty').first()

                attempt = QuestionAttempt.objects.create(
                    associated_profile=currentProfile,
                    question=queuedQuestion,
                    solved_test_cases=0,
                    session=Session.objects.create(user=currentUser, question=queuedQuestion)
                )

                currentProfile.question_history.add(attempt)
                currentProfile.next_questions.remove(queuedQuestion)

            currentQuestionAttempt = currentProfile.question_history.latest('created_at')
            currentQuestionAttempt.session.codeSubmission = currentQuestionAttempt.question.target_function_definition + " (* <- Keep the provided function name. It needs to be maintained for the compiler to work properly. *)"
            currentQuestionAttempt.session.save()
        
        pastQuestions = currentProfile.question_history.all().order_by('-pk') [1:] # Exclude the current question from past questions & order by most recent

        context = {
            "sessions" : sessions,
            "user" : currentUser,
            "pastQuestions" : pastQuestions,
            "currentQuestion" : currentQuestionAttempt,
            "questionBankLoaded": True,
        }
        return render(request, "studentSystem/dashboard.html", context)
    except Exception:
        logger.exception("dashboard failed for user_id=%s", getattr(request.user, "id", None))
        raise

def next_problem(request):
    """Assign the next question and redirect straight to its code editor."""
    currentUser = request.user
    currentProfile = Profile.objects.get(user=currentUser)

    attempt_count = currentProfile.question_history.count()
    completed_count = max(0, attempt_count - 1)

    if completed_count >= 6:
        return redirect("post_experiment_survey")

    nextQuestions = currentProfile.next_questions.all()

    if nextQuestions.exists():
        queuedQuestion = nextQuestions.order_by('difficulty').first()
    else:
        assignment(currentProfile)
        queuedQuestion = currentProfile.next_questions.order_by('difficulty').first()

    if queuedQuestion is None:
        return redirect("post_experiment_survey")

    session = Session.objects.create(user=currentUser, question=queuedQuestion)
    session.codeSubmission = (
        queuedQuestion.target_function_definition
        + " (* <- Keep the provided function name. It needs to be maintained for the compiler to work properly. *)"
    )
    session.save()

    attempt = QuestionAttempt.objects.create(
        associated_profile=currentProfile,
        question=queuedQuestion,
        solved_test_cases=0,
        session=session,
    )
    currentProfile.question_history.add(attempt)
    currentProfile.next_questions.remove(queuedQuestion)

    return redirect("codeSubmit", id=session.pk)


def createChat (request):
    currentUser = request.user
    session = Session.objects.create(user=currentUser)
    return redirect('chat', id=session.pk)

def chat(request, id):
    session = get_owned_session_or_404(request.user, id) # Current session and associated fields
    if not user_has_ai_access(request.user):
        return redirect("codeSubmit", id=id)

    chatLog = json.dumps(session.chatLog) # Chats of the current session
    existingChats = Session.objects.filter(user=session.user).exclude(pk=id) # Other chats asssociated with the user

    context = {
        "session" : session,
        "sessionID" : id,
        "chatLog" : chatLog,
        "existingChats" : existingChats,
        "ai_enabled": True,
    }
    return render(request, "studentSystem/chat.html", context)

def updateChat(request, id):
    if request.method == 'POST':
        try:
            session = get_owned_session_or_404(request.user, id)
            require_ai_access(request.user)
            data = json.loads(request.body)
            new_chat = data.get('chat')

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
        session = get_owned_session_or_404(request.user, id)
        require_ai_access(request.user)
        conversationHistory = session.chatLog
        question_description = session.question.question_description

        conversationHistory.insert(0, {"role": "system", "content": "You are a helpful programming assistant that has expertise in Standard ML."
                                    + "\nThe user will ask you for help on a programming question." +
                                    "\nNever provide a complete working solution or full function definition."
                                    + "\nYou may provide at most 3–5 lines of code at a time, and only as illustrative fragments."
                                    + "\nFocus on algorithm, decomposition, invariants, test cases, and debugging steps."
                                    + "\nIf you do suggest a code change, it is vital that you explain the details of why you made that change."})
        conversationHistory.insert(1, {"role": "assistant", "content": "Hello, I am a helpful programming assistant specialized in Standard ML! Let me know if you have any questions about the language, and I'm here to help!"})
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
    session = get_owned_session_or_404(request.user, id)

    # Record when the student first opens this problem
    attempt = session.attempts.first()
    if attempt and attempt.opened_at is None:
        attempt.opened_at = timezone.now()
        attempt.save(update_fields=["opened_at"])

    submission = session.codeSubmission
    context = {
        "codeSubmission" : submission,
        "session" : session,
        "nextSession" : id + 1,
        "previousSession" : id - 1,
        "ai_enabled": user_has_ai_access(request.user),
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
        session = get_owned_session_or_404(request.user, id)
        require_ai_access(request.user)

        body = json.loads(request.body)

        submission = body.get("submission")
        compiler_output = body.get("compiler_output")
        question_description = session.question.question_description

        response = generateCloudResponse([{"role": "system", "content": "You are a helpful programming assistant that has expertise in Standard ML."
                                    + "\nThe user will ask you for help on a programming question." +
                                    "\nNever provide a complete working solution or full function definition."
                                    + "\nYou may provide at most 3–5 lines of code at a time, and only as illustrative fragments."
                                    + "\nFocus on algorithm, decomposition, invariants, test cases, and debugging steps."
                                    + "\nIf you do suggest a code change, it is vital that you explain the details of why you made that change."},
                                      {"role" : "user", "content" : "\nAnalyze the following Standard ML code: " + submission
                                    +"\nThis what the code currently outputs in the compiler when it is run: " + compiler_output
                                    +"\nIf there is an error, explain what the error means and how to fix it." + 
                                    " \nIf there is no error, suggest improvements to the code or optimizations that can be made." }])
        return JsonResponse({"AI_response" : response})

@require_POST
def save_system_hint(request, id):
    try:
        session = get_owned_session_or_404(request.user, id)
        require_ai_access(request.user)
    except PermissionDenied as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=403)

    try:
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
        session_id = body.get("session_id")
        compiled_output = str(compileCode(submission))

        # Log the compile attempt
        if session_id and request.user.is_authenticated:
            try:
                session = Session.objects.get(pk=session_id)
                seq = session.compile_attempts.count() + 1
                CompileAttempt.objects.create(
                    user=request.user,
                    session=session,
                    sequence_number=seq,
                    raw_output=compiled_output,
                    error_category=categorize_error(compiled_output),
                )
            except Session.DoesNotExist:
                pass

        return JsonResponse({"compiled_output" : compiled_output})

def submitCode(request, id):
    if request.method == "POST":
        currentProfile = Profile.objects.get(user=request.user)
        session = Session.objects.get(pk=id)

        casesSolved = handler(currentProfile, session=session)

        # Record submission timestamp and total test cases
        attempt = session.attempts.first()
        if attempt:
            attempt.submitted_at = timezone.now()
            attempt.total_test_cases = len(session.question.test_cases)
            attempt.save(update_fields=["submitted_at", "total_test_cases"])

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
        body = json.loads(request.body)
        survey_response = body.get("survey_response")
        session = Session.objects.get(pk = id)
        attempt = QuestionAttempt.objects.get(session=session)
        attempt.survey_response = survey_response
        attempt.save()
        return JsonResponse({"status": "ok"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@csrf_exempt
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
            ts = None
            if "t" in p:
                ts = timezone.datetime.fromtimestamp(
                    p["t"] / 1000, tz=timezone.get_current_timezone()
                )
            events.append(CursorEvent(
                user=user,
                session_id=session_id,
                path=path,
                x=p["x"],
                y=p["y"],
                viewport_width=p["vw"],
                viewport_height=p["vh"],
                scroll_y=p["sy"],
                timestamp=ts,
            ))
        except KeyError:
            continue

    if events:
        CursorEvent.objects.bulk_create(events)

    return JsonResponse({"status": "ok", "saved": len(events), "timestamp": timezone.now().isoformat()})

def track_deletion(request):
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
            # F. Open-Ended Feedback
            # ======================
            liked_most=data.get("liked_most", ""),
            liked_least=data.get("liked_least", ""),
            change_one_thing=data.get("change_one_thing", ""),
            additional_comments=data.get("additional_comments", ""),

            # ======================
            # G. Manipulation Check
            # ======================
            # difficulty_notice=data.get("difficulty_notice"),
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
