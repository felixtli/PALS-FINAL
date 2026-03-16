from .models import Profile, Question
from django.db.models.functions import Random
import random

def assignment(profile: Profile):
    easy = list(
        Question.objects.filter(difficulty=1)
        .order_by(Random())[:1]
    )

    medium = list(
        Question.objects.filter(difficulty=2)
        .order_by(Random())[:3]
    )

    hard = list(
        Question.objects.filter(difficulty=3)
        .order_by(Random())[:2]
    )

    # Combine + shuffle
    questions = easy + medium + hard
    random.shuffle(questions)

    # Assign to profile
    profile.next_questions.set(questions)

    return {
        "status": "success",
        "count": len(questions),
    }

def non_adaptive_assignment(profile: Profile):
    return assignment(profile)

