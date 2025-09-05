from django.db import models
from django.contrib.auth.models import User

# Extension of Django's prebuilt "User" module
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    question_history = models.ManyToManyField('QuestionAttempt', blank=True)
    next_questions = models.ManyToManyField('Question', blank=True, related_name='next_for_profiles')

# Holds the coding question
class Question (models.Model): # Object that holds the coding question
    DIFFICULTY_CHOICES = [
        (1, 'Easy'),
        (2, 'Medium'),
        (3, 'Hard'),
    ]

    question_title = models.CharField(max_length = 255, default="Question_Title", primary_key=True)
    question_description = models.CharField(max_length = 2500, default="Description Missing") 
    test_cases = models.JSONField(default=list)
    target_function = models.CharField(max_length = 100)

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

# Tracks user progress per question
class QuestionAttempt(models.Model):
    associated_profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attempts", default="2")
    solved_test_cases = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('associated_profile', 'question')  # one record per user-question pair