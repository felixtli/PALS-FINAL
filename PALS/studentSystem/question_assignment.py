from .models import Profile, Question, QuestionAttempt, Session
from django.db.models.functions import Random
import random

def initialQuestion(profile: Profile):
    available_questions = Question.objects.all().filter(difficulty=1) # change to intermediate later on
    print ("available questions:" + str(available_questions) + " count: " + str(available_questions.count()))
    
    next_questions = Question.objects.filter(
        difficulty=2
    ).order_by(Random())[:3] # Gets 3 random questions from the available pool

    profile.next_questions.set(next_questions) # Update the next_questions field

    return {"status" : "success", "question" : random.choice(available_questions)}

def assignment(profile: Profile):
    difficulty_multiplier_map = { # Currently not used since questions in each block of are all the same difficulty
        "Easy" : 1,
        "Medium" : 1.25,
        "Hard" : 1.5
    }

    ascend_cutoff = 20 # Determines how many test cases need to be correctly solved before moving to the next difficulty. Can be adjusted. 
    descend_cutoff = 10 # Determines how many test cases need to be correctly solved before moving down a difficulty. Can be adjusted.

    # Determine the next question difficulty based on user's solved counts

    # Gets the user's last 3 question attempts. This can be changed to look at different approaches.
    question_history = QuestionAttempt.objects.all().filter(associated_profile=profile).order_by('-created_at')[:3]

    total_solved = 0
    for attempt in question_history: # Each attempt is an individual QuestionAttempt object
        total_solved += attempt.solved_test_cases
    
    # Get all question IDs the user has already attempted
    attempted_questions = QuestionAttempt.objects.filter(
        associated_profile=profile
    ).values_list('question_id', flat=True)

    if total_solved >= ascend_cutoff:
        print("ASCENDING")
        if question_history[0].question.difficulty < 3:
            next_difficulty = question_history[0].question.difficulty + 1
        else:
            next_difficulty = 3

        # Get available questions excluding attempted ones
        next_questions = Question.objects.filter(
            difficulty=next_difficulty
        ).exclude(
            question_title__in=attempted_questions
        ).order_by(Random())[:3] # Gets 3 random questions from the available pool

        print("NEXT QUESTIONS: " + str(next_questions))

        profile.next_questions.set(next_questions) # Update the next_questions field
    
    elif total_solved <= descend_cutoff:
        print("DESCENDING")
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

        print("NEXT QUESTIONS: " + str(next_questions))

        profile.next_questions.set(next_questions) # Update the next_questions field
    
        

