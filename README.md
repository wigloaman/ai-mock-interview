# AI Mock Interview

A Django web app for practising job interviews with an AI interviewer. Enter a job role (and optionally a
company and job description), answer questions by typing or speaking, and get a detailed review of your
performance. Everything runs on free services.

## Features

- **Tailored questions**: AI generates questions for the job role, company and job description you enter
- **Follow-up questions**: vague or incomplete answers get a follow-up, like in a real interview
- **Voice**: questions are read aloud with a natural voice, and you can answer with your microphone
- **Interview review**: overall score, strong and weak points, improvements and a hire decision
- **Answer review**: a score, feedback and an expert answer for every question
- **Profiles and history**: sign up with email, edit your profile and revisit past interviews
- **Contact and feedback** forms, stored in the Django admin
- **Auto-answer** (staff only): let the AI answer every question to test the full flow quickly

## Tech stack

- Python, Django 5.2
- PostgreSQL (Supabase)
- Bootstrap, jQuery
- django-allauth for authentication
- Groq API (gpt-oss models) for AI questions and reviews
- Groq Whisper for voice answers, edge-tts for spoken questions

## Getting started

You need Python 3.12+ and a free Groq API key from https://console.groq.com/keys.

```bash
git clone https://github.com/<your-username>/ai-mock-interview.git
cd ai-mock-interview
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in your values
python manage.py migrate
python manage.py createsuperuser   # optional, for the admin and auto-answer
python manage.py runserver
```

Open http://127.0.0.1:8000, sign up and start an interview.

The app uses a Supabase Postgres database when `DATABASE_URL` is set, and local SQLite otherwise.

## Configuration

All settings are read from `.env` (see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for questions, reviews and speech-to-text | required |
| `DATABASE_URL` | Postgres connection string | local SQLite |
| `DJANGO_SECRET_KEY` | Django secret key | development key |
| `DEBUG` | Debug mode | `True` |
| `AI_MODEL` | Model for questions and reviews | `openai/gpt-oss-120b` |
| `AI_FAST_MODEL` | Model for follow-ups and answer reviews | `openai/gpt-oss-20b` |
| `TTS_VOICE` | edge-tts voice for spoken questions | `en-US-AvaNeural` |
| `STT_MODEL` | Groq speech-to-text model | `whisper-large-v3-turbo` |

## Deploying on Render

Create a **Web Service** from the repository with these settings:

| Setting | Value |
|---|---|
| Build Command | `./build.sh` |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |

Add `GROQ_API_KEY`, `DATABASE_URL`, `DJANGO_SECRET_KEY` and `DEBUG=False` as environment variables. Render's
hostname is added to the allowed hosts automatically. A single worker keeps background review generation
consistent, and the long timeout leaves room for question generation.

## Credits

Based on the open-source project InterviewStreak.
