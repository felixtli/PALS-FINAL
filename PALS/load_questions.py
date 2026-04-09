import os
import django
import csv
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pals_project.settings")
django.setup()

from studentSystem.models import Question

def createQuestion(title, description, group, difficulty, target_function, target_function_definition, test_cases):
    difficulty_map = {"Easy" : 1, "Medium" : 2, "Hard" : 3, "Exam" : 4}

    question, created = Question.objects.get_or_create(
        question_title=title,
        defaults={
            "question_description": description,
            "group": group,
            "difficulty": difficulty_map[difficulty],
            "target_function": target_function,
            "target_function_definition": target_function_definition,
            "test_cases": test_cases
        }
    )
    if created:
        print("Question created successfully!")
    else:
        print("Question already exists")

if __name__ == "__main__":
    with open("Standard ML Problems & Solutions Dataset (Adjusted).csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title, description, group, difficulty, target_function, target_function_definition, test_cases = row["Problem Title"], row["Problem Description"], row["Group"], row["Difficulty"], row["Target Function"], row["Target Function Definition"], json.loads(row["Final JSON"])
            createQuestion(title, description, group, difficulty, target_function, target_function_definition, test_cases)