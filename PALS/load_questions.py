import os
import django
import csv
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pals_project.settings")
django.setup()

from studentSystem.models import Question

def createQuestion(title, description, difficulty, target_function, test_cases):
    difficulty_map = {"Easy" : 1, "Medium" : 2, "Hard" : 3}

    question, created = Question.objects.get_or_create(
        question_title=title,
        defaults={
            "question_description": description,
            "difficulty": difficulty_map[difficulty],
            "target_function": target_function,
            "test_cases": test_cases
        }
    )
    if created:
        print("Question created successfully!")
    else:
        print("Question already exists")

if __name__ == "__main__":
    with open("Standard ML Problems & Solutions Dataset.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title, description, difficulty, target_function, test_cases = row["Problem Title"], row["Problem Description"], row["Difficulty"], row["Target Function Definition"], json.loads(row["Final JSON"])
            createQuestion(title, description, difficulty, target_function, test_cases)