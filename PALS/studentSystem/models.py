from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Extension of Django's prebuilt "User" module
class Profile(models.Model):
    USER_TYPES = (
        ("A", "Group A"),
        ("B", "Group B"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    user_type = models.CharField(max_length=1, choices=USER_TYPES)

    question_history = models.ManyToManyField('QuestionAttempt', blank=True)
    next_questions = models.ManyToManyField('Question', blank=True, related_name='next_for_profiles')

# Holds the coding question
class Question (models.Model): # Object that holds the coding question
    DIFFICULTY_CHOICES = [
        (1, 'Easy'),
        (2, 'Medium'),
        (3, 'Hard'),
        (4, 'Exam'),
    ]

    question_title = models.CharField(max_length = 255, default="Question_Title", primary_key=True)
    question_description = models.CharField(max_length = 2500, default="Description Missing")  # TODO: CHANGE THIS TO A TEXTFIELD SO LINE BREAKS WORK
    test_cases = models.JSONField(default=list)
    target_function = models.CharField(max_length = 100)
    target_function_definition = models.CharField(max_length = 1000, default="")

    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_CHOICES,
        default=1
    )

    def get_difficulty_label(self):
        #Convenience method to get the label string for this difficulty.
        return dict(self.DIFFICULTY_CHOICES).get(self.difficulty, "Unknown")


# Holds a code submission and its corresponding chatlog
class Session (models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) # associates every new session object with a user
    title = models.CharField(max_length=255, default="Session")
    question = models.ForeignKey(  # associates session with a question
        Question,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    chatLog = models.JSONField(default=list, blank=True)
    codeSubmission = models.CharField(max_length=2500, default="") 

class SystemHint(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    contents = models.TextField()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="system_hints")
    session = models.ForeignKey("Session", on_delete=models.CASCADE, related_name="system_hints")
    code_contents = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"SystemHint(session={self.session_id}, user={self.user_id}, created_at={self.created_at})"

# Tracks user progress per question
class QuestionAttempt(models.Model):
    associated_profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attempts", default="2")
    solved_test_cases = models.IntegerField(default=0)
    survey_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
# Tracks page analytics
class PageView(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    session_key = models.CharField(max_length=40, db_index=True)
    path = models.CharField(max_length=2048, db_index=True)
    referrer = models.CharField(max_length=2048, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    duration_ms = models.PositiveIntegerField()  # store milliseconds
    extra = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["session_key", "path", "created_at"])]

# Tracks overall website session activity
class WebsiteSession(models.Model):
    session_key = models.CharField(max_length=64, db_index=True, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    total_active_ms = models.BigIntegerField(default=0)   # accumulated active time
    last_ping = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Tracks cursor position
class CursorEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL
    )
    session_id = models.CharField(max_length=64, blank=True)
    path = models.CharField(max_length=255)          # which page
    x = models.FloatField()                          # cursor x (px)
    y = models.FloatField()                          # cursor y (px)
    viewport_width = models.IntegerField()
    viewport_height = models.IntegerField()
    scroll_y = models.IntegerField()                 # scroll offset
    created_at = models.DateTimeField(auto_now_add=True)

# Tracks code deletion events
class DeletionEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    position = models.IntegerField() # Position in the code where deletion occurred
    length = models.IntegerField() # Number of characters deleted
    deleted_content = models.TextField() # Content that was deleted
    new_content = models.TextField(null=True, blank=True) # Content that was written
    timestamp = models.DateTimeField(auto_now_add=True)
    old_code = models.TextField() # Old content pre-deletion
    new_code = models.TextField() # Resultant content post-deletion

class EndSurveyResponse(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)

    courses_completed = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(0, 4)] + [(3, "3+")],
        help_text="Number of programming courses completed"
    )

    years_experience = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(0, 5)] + [(5, "5+")],
        help_text="Years of programming experience"
    )

    ml_familiarity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Self-rated ML / Standard ML familiarity (1–7)"
    )

    current_fatigue = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="How rested the participant feels (1–7)"
    )

    # Section B: Usability
    ease_of_use = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    feedback_helpfulness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    challenge_match = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    reuse_intent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    # Section C: Engagement & Attention

    focus_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    time_distortion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Time felt like it passed quickly (1–7)"
    )

    # Section D: Cognitive Load

    mental_demand = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    effort = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    frustration = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    # Section E: Trust & Fairness

    trusted_system = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    fairness_of_system = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    # Section F: Adaptive Features
    adaptation_quality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    adaptive_hint_helpfulness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    # Section G: Open-Ended Feedback
    liked_most = models.TextField(blank=True)
    liked_least = models.TextField(blank=True)
    change_one_thing = models.TextField(blank=True)
    additional_comments = models.TextField(blank=True)

    # Section H: Attention & manipulation Check
    difficulty_notice = models.CharField(
        max_length=10,
        choices=[
            ("yes", "Yes"),
            ("no", "No"),
            ("unsure", "Not sure"),
        ]
    )

    def __str__(self):
        return f"SurveyResponse #{self.id} ({self.created_at.date()})"
