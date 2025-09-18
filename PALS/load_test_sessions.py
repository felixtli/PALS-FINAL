import os
import django
import csv
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pals_project.settings")
django.setup()

from studentSystem.models import Question, Session

def createSession(question: Question, id: int):
    session, created = Session.objects.get_or_create(
        pk=id,
        user_id=1,
        question=question,
        codeSubmission=question.target_function
    )

    return session, created

if __name__ == "__main__":
    questions = Question.objects.all()

    for q in range(0, len(questions)):
        question = questions[q]
        pk = q
        session, created = createSession(question, pk)

        if created:
            print(f"Created new session for Question ID: {question.pk}")
        else:
            print(f"Session already exists for Question ID: {question.pk}")


