import os
import django
import csv
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pals_project.settings")
django.setup()

from studentSystem.models import Question, Session, QuestionAttempt

def createQuestionAttempt(question: Question, id: int):
    session, created = Session.objects.get_or_create(
        pk=id,
        user_id=71,
        question=question,
        codeSubmission=question.target_function
    )

    attempt, created = QuestionAttempt.objects.get_or_create(
        pk=id,
        question=question,
        associated_profile_id=71,
        session_id=session.pk,
        solved_test_cases=0
    )

    return attempt, created

if __name__ == "__main__":
    questions = Question.objects.all()

    for q in range(0, len(questions)):
        question = questions[q]
        pk = q
        session, created = createQuestionAttempt(question, pk)

        if created:
            print(f"Created new QuestionAttempt for Question ID: {question.pk}")
        else:
            print(f"QuestionAttempt already exists for Question ID: {question.pk}")


