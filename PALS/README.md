# PALS

A Django-based web application for interactive chat and code submission, featuring AI-powered responses using the Ollama Llama 3.2 model.

## Project Overview
PALS (Personalized AI Learning System) is designed to facilitate interactive learning and code review through a chat interface. Users can sign up, log in, create chat sessions, and submit code for feedback. The backend leverages Django, while the frontend uses custom HTML, CSS, and JavaScript for a modern, responsive experience.

## Features
- **User Authentication**: Sign up and log in with styled forms.
- **Chat Interface**: Create and manage chat sessions, with persistent chat logs per user.
- **AI Integration**: Uses Ollama's Llama model to generate thoughtful responses to user prompts.
- **Code Submission (In Progress)**: Interface for submitting code, intended for future AI review/feedback.
- **Session Management**: Each chat/code session is stored and associated with the user.
- **Modern UI**: Custom CSS for chat, login, signup, and code submission pages.

## Project Structure
```
PALS/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── pals_project/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── static/
│       ├── CSS/
│       │   ├── chatStyle.css
│       │   ├── loginStyle.css
│       │   ├── signupStyle.css
│       │   └── submitStyle.css
│       └── JS/
│           ├── chat.js
│           └── submission.js
└── studentSystem/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── chatbot.py
    ├── forms.py
    ├── migrations/
    │   └── 0001_initial.py
    ├── models.py
    ├── templates/
    │   └── studentSystem/
    │       ├── chat.html
    │       ├── codeSubmit.html
    │       ├── index.html
    │       ├── login.html
    │       └── signup.html
    ├── tests.py
    ├── urls.py
    └── views.py
```

## Setup Instructions
1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```
4. **Run the development server**:
   ```bash
   python manage.py runserver
   ```
5. **Download and Configure the Ollama Client**: Ensure the Ollama server is running and accessible for AI features.

## Unfinished Components / Areas Needing Development
- **Home Page**: `index.html` and the corresponding view are placeholders and need content/design.
- **Code Submission Page**: `codeSubmit.html` and related backend logic are unfinished; currently, the page is a UI placeholder.
- **Testing**: No automated tests are implemented yet (`tests.py` is empty).
- **Error Styling**: Login form error messages need styled display (see TODO in `login.html`).
- **Code Review AI**: The backend logic for AI-powered code review/feedback is not yet implemented.

## Dependencies
See `requirements.txt` for the full list. Key dependencies:
- Django 5.2.1
- Ollama 0.4.8 (for AI integration)

## Author & Contact
- **Author**: Felix Li
- **Email**: felixtl1014@gmail.com
- **GitHub**: [Ftl1014](https://github.com/Ftl1014)