# PALS

A Django-based web application for interactive chat and code submission, featuring AI-powered responses using Ollama and Standard ML (SML) code compilation support.

## Project Overview

PALS (Personalized AI Learning System) is designed to facilitate interactive learning and code review through a chat interface. Users can sign up, log in, create chat sessions, submit Standard ML code for compilation and testing, and receive AI-powered feedback. The backend leverages Django, while the frontend uses custom HTML, CSS, and JavaScript for a modern, responsive experience.

## Features

- **User Authentication**: Sign up and log in with styled forms
- **Chat Interface**: Create and manage chat sessions, with persistent chat logs per user
- **AI Integration**: Uses Ollama's gemma3:4b model to generate thoughtful responses to user prompts
- **Code Compilation**: Compile and test Standard ML code submissions with real-time feedback
- **Test Case Evaluation**: Automatic test case execution and scoring for coding problems
- **Session Management**: Each chat/code session is stored and associated with the user
- **Question Assignment**: Fixed non-adaptive question pools for study participants
- **Modern UI**: Custom CSS for chat, login, signup, and code submission pages

## Prerequisites

Before running the server, you must install and configure the following:

### External Applications

1. **Python 3.8+**
   - Required for running the Django application
   - Download from [python.org](https://www.python.org/downloads/)

2. **Standard ML of New Jersey (SML/NJ)**
   - Required for compiling and running Standard ML code
   - **Windows**: Download from [smlnj.org](https://www.smlnj.org/dist/working/install.html)
   - **Linux/Mac**: Install via package manager or download from [smlnj.org](https://www.smlnj.org/dist/working/install.html)
   - Verify installation by running `sml` in your terminal - you should see the SML/NJ prompt

3. **Ollama Server**
   - Required for AI-powered chat responses
   - Download from [ollama.ai](https://ollama.ai/)
   - After installation, pull the required model:
     ```bash
     ollama pull gemma3:4b
     ```
   - Start the Ollama server (it should run automatically on installation):
     ```bash
     ollama serve
     ```
   - The server should be accessible at `http://localhost:11434`

### Python Dependencies

All Python libraries are listed in `requirements.txt`. Install them using:

```bash
pip install -r requirements.txt
```

**Key Python Libraries:**
- `Django==5.2.1` - Web framework
- `ollama==0.4.8` - Ollama API client
- `tree-sitter` - Required for SML code parsing (may need to install separately: `pip install tree-sitter`)
- `httpx==0.28.1` - HTTP client library
- `pydantic==2.11.5` - Data validation
- Additional dependencies: `asgiref`, `sqlparse`, `certifi`, `idna`, `sniffio`, `tzdata`, `typing-extensions`, `annotated-types`, `h11`, `httpcore`, `pydantic-core`, `typing-inspection`

**Note:** If `tree-sitter` is not automatically installed, install it manually:
```bash
pip install tree-sitter
```

## Setup Instructions

Follow these steps in order before running the server:

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PALS
```

### Step 2: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# If tree-sitter is missing, install it separately
pip install tree-sitter
```

### Step 3: Build the SML Parser (if needed)

The project includes a tree-sitter parser for Standard ML. If the `build/sml.dll` (Windows) or `build/sml.so` (Linux/Mac) files are missing, build them:

```bash
python studentSystem/build_sml.py
```

**Note:** This step may require a C compiler (like GCC or Visual Studio Build Tools) depending on your platform.

### Step 4: Verify External Applications

Before proceeding, ensure:

1. **SML/NJ is installed and accessible:**
   ```bash
   sml
   # Should show: Standard ML of New Jersey v110.XX [built: ...]
   ```

2. **Ollama server is running:**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   # Or visit http://localhost:11434 in your browser
   
   # If not running, start it:
   ollama serve
   
   # Verify the model is available:
   ollama list
   # Should show gemma3:4b
   ```

### Step 5: Apply Database Migrations

```bash
python manage.py migrate
```

This will create the SQLite database (`db.sqlite3`) and set up all required tables.

### Step 6: Load Questions Data

Load the dataset of coding questions to the SQLite database.

```bash
# Ensure the CSV file exists: "Standard ML Problems & Solutions Dataset - Problems.csv"
python load_questions.py
```

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/` by default.

### Step 8: Access the Application

Open your web browser and navigate to:
- Home: `http://127.0.0.1:8000/`
- Sign Up: `http://127.0.0.1:8000/signup/`
- Login: `http://127.0.0.1:8000/login/`
- Dashboard: `http://127.0.0.1:8000/dashboard/` (requires login)

## Project Structure

```
PALS/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── load_questions.py          # Script to load questions from CSV
├── load_test_sessions.py       # Script to create test sessions
├── evaluate_parser.py         # Parser evaluation script
├── build/                      # Compiled tree-sitter parser files
│   ├── sml.dll                # Windows parser library
│   └── sml.so                 # Linux/Mac parser library
├── pals_project/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── static/                # Static files (CSS, JS)
│       ├── CSS/
│       └── JS/
├── studentSystem/             # Main Django app
│   ├── models.py              # Database models
│   ├── views.py               # View functions
│   ├── urls.py                # URL routing
│   ├── chatbot.py             # AI chat integration
│   ├── compiler.py            # SML code compilation
│   ├── new_parser.py          # SML code parser
│   ├── build_sml.py           # Parser build script
│   ├── question_assignment.py # Question difficulty logic
│   └── templates/             # HTML templates
└── tree-sitter-sml/           # SML grammar for tree-sitter
```

## Troubleshooting

### Issue: "sml: command not found"
- **Solution**: Ensure SML/NJ is installed and added to your system PATH
- Verify installation: `sml --version` or `which sml` (Linux/Mac)

### Issue: "Connection refused" when accessing Ollama
- **Solution**: Start the Ollama server:
  ```bash
  ollama serve
  ```
- Verify it's running: `curl http://localhost:11434/api/tags`

### Issue: "Model not found" error
- **Solution**: Pull the required model:
  ```bash
  ollama pull gemma3:4b
  ```

### Issue: "tree-sitter Language not found" or "sml.dll/sml.so not found"
- **Solution**: Build the parser:
  ```bash
  python studentSystem/build_sml.py
  ```
- Ensure you have a C compiler installed (GCC, Visual Studio Build Tools, etc.)

### Issue: Database migration errors
- **Solution**: Delete `db.sqlite3` and run migrations again:
  ```bash
  rm db.sqlite3  # Linux/Mac
  del db.sqlite3  # Windows
  python manage.py migrate
  ```

### Issue: Port 8000 already in use
- **Solution**: Run on a different port:
  ```bash
  python manage.py runserver 8001
  ```

## Development Notes

### Unfinished Components / Areas Needing Development
- **Home Page**: `index.html` and the corresponding view are placeholders
- **Error Styling**: Login form error messages need styled display (see TODO in `login.html`)
- **Code Submission**: Some code submission features are still in development
- **Testing**: Automated tests are not yet implemented

### Configuration

The application uses the following default settings:
- **Ollama Model**: `gemma3:4b` (configured in `studentSystem/chatbot.py`)
- **Ollama URL**: `http://localhost:11434` (configured in `studentSystem/chatbot.py`)
- **Database**: SQLite (`db.sqlite3`)
- **Debug Mode**: Enabled (set `DEBUG = False` in `pals_project/settings.py` for production)

## Dependencies Summary

### Python Packages (from requirements.txt)
- annotated-types==0.7.0
- anyio==4.9.0
- asgiref==3.8.1
- certifi==2025.4.26
- Django==5.2.1
- h11==0.16.0
- httpcore==1.0.9
- httpx==0.28.1
- idna==3.10
- ollama==0.4.8
- pydantic==2.11.5
- pydantic_core==2.33.2
- sniffio==1.3.1
- sqlparse==0.5.3
- typing-inspection==0.4.1
- typing_extensions==4.13.2
- tzdata==2025.2
- tree-sitter (install separately if not included)

### External Applications
- **Python 3.8+** - Runtime environment
- **SML/NJ** - Standard ML compiler/interpreter
- **Ollama** - AI model server (with gemma3:4b model)
- **C Compiler** - Required for building tree-sitter parser (GCC, Visual Studio Build Tools, etc.)

## Author & Contact

- **Author**: Felix Li
- **Email**: felixtl1014@gmail.com
- **GitHub**: [Ftl1014](https://github.com/Ftl1014)

## License
