from .models import Profile, Question, QuestionAttempt, Session
from django.db.models.functions import Random
import random

def initialQuestion(profile: Profile):
    available_questions = Question.objects.all().filter(difficulty=2) # Starts off with an easy question
    
    next_questions = Question.objects.filter(
        difficulty=2
    ).order_by(Random())[:3] # Gets 3 random questions from the available pool

    profile.next_questions.set(next_questions) # Update the next_questions field

    return {"status" : "success", "question" : random.choice(available_questions)}

def assignment(profile: Profile):

    ascend_cutoff = 20 # Determines how many test cases need to be correctly solved before moving to the next difficulty. Can be adjusted. 
    descend_cutoff = 10 # Determines how many test cases need to be correctly solved before moving down a difficulty. Can be adjusted.

    # Determine the next question difficulty based on user's solved counts

    # Gets the user's last 3 question attempts.
    question_history = QuestionAttempt.objects.all().filter(associated_profile=profile).order_by('-created_at')[:3]

    total_solved = 0
    for attempt in question_history: # Each attempt is an individual QuestionAttempt object
        total_solved += attempt.solved_test_cases
    
    # Get all question IDs the user has already attempted
    attempted_questions = QuestionAttempt.objects.filter(
        associated_profile=profile
    ).values_list('question_id', flat=True)

    if total_solved >= ascend_cutoff:
        if question_history[0].question.difficulty < 4:
            next_difficulty = question_history[0].question.difficulty + 1
        else:
            next_difficulty = 4

        # Get available questions excluding attempted ones
        next_questions = Question.objects.filter(
            difficulty=next_difficulty
        ).exclude(
            question_title__in=attempted_questions
        ).order_by(Random())[:3] # Gets 3 random questions from the available pool

        profile.next_questions.set(next_questions) # Update the next_questions field
    
    elif total_solved <= descend_cutoff:
        if question_history[0].question.difficulty > 1:
            next_difficulty = question_history[0].question.difficulty - 1
        else:
            next_difficulty = 1

        # Get available questions excluding attempted ones
        next_questions = Question.objects.filter(
            difficulty=next_difficulty
        ).exclude(
            question_title__in=attempted_questions
        ).order_by(Random())[:3]

        profile.next_questions.set(next_questions) # Update the next_questions field
    
        

