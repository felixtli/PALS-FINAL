from .models import Profile, Question
from django.db.models.functions import Random
import random

def assignment(profile: Profile):
    easy = list(
        Question.objects.filter(difficulty=1)
        .order_by(Random())[:2]
    )

    medium = list(
        Question.objects.filter(difficulty=2)
        .order_by(Random())[:2]
    )

    hard = list(
        Question.objects.filter(difficulty=3)
        .order_by(Random())[:2]
    )

    # Ordered: 2 easy, 2 medium, 2 hard (shuffled within each tier)
    questions = easy + medium + hard

    # Assign to profile
    profile.next_questions.set(questions)

    return {
        "status": "success",
        "count": len(questions),
    }

def non_adaptive_assignment(profile: Profile):
    return assignment(profile)

