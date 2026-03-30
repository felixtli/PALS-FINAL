# PALS - Personalized AI Learning System

A Django research platform studying AI's impact on learning. Students solve Standard ML (SML) coding problems in two groups:
- **Group A**: Has AI chat assistance (Ollama gemma3:4b)
- **Group B**: No AI assistance (control group)

The system collects detailed analytics (cursor tracking, code deletions, page views, idle detection) and survey responses for research analysis.

## Tech Stack

- **Backend**: Django 5.2.1, Gunicorn, WhiteNoise
- **Database**: PostgreSQL (production), SQLite (local dev)
- **AI**: Ollama API (local or cloud with API key)
- **Code Compilation**: SML/NJ subprocess + tree-sitter for parsing
- **Frontend**: Django templates, vanilla JS, custom CSS (dark mode support)
- **Infrastructure**: Docker

## Project Structure

- `pals_project/` - Django project config, static assets (CSS/JS)
- `studentSystem/` - Main Django app (models, views, forms, templates)
- `studentSystem/chatbot.py` - Ollama AI integration
- `studentSystem/compiler.py` - SML code compilation and test case evaluation
- `studentSystem/question_assignment.py` - Non-adaptive question pool (1 Easy, 3 Medium, 2 Hard)
- `tree-sitter-sml/` / `build/` - SML grammar and compiled parser

## Running Locally

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata # or python load_questions.py to populate questions from CSV
python manage.py runserver
```

With Docker:
```bash
docker build -t pals .
docker run -p 8000:8000 pals
```

## Key Decisions

- Questions are assigned from a fixed pool (non-adaptive), shuffled per user
- Group assignment happens at signup via radio buttons on the registration form
- AI access is determined by `Profile.has_ai_access` property based on `user_type`
- Analytics are collected client-side via JS and posted to Django endpoints
- Post-study survey covers usability, engagement, cognitive load, trust, and fairness
