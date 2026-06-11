# SmartHire

AI-powered interview platform that automates candidate screening. Employers set questions with expected keywords; candidates record video responses that are automatically transcribed, sentiment-analysed, and scored — giving employers a structured result dashboard without manual review.

## Features

- **Two user roles** — employer (sets questions, reviews results) and employee (answers questions via webcam)
- **Video recording** — captures candidate responses directly in the browser
- **Speech-to-text** — transcribes responses using Google Speech Recognition
- **Sentiment analysis** — scores responses (positive/negative/neutral/compound) via VADER
- **Keyword matching** — compares transcription against employer-defined expected answers
- **People detection** — flags if multiple people are present during the interview (OpenCV + Haar Cascade)
- **Results dashboard** — per-candidate charts (ECharts) showing sentiment and answer accuracy
- **Email notifications** — employer can notify selected candidates

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate
- **Database:** SQLite
- **AI/ML:** OpenCV, SpeechRecognition, VADER Sentiment, MoviePy
- **Frontend:** Jinja2 templates, ECharts

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Initialize the database:

```bash
flask db upgrade
```

Run the app:

```bash
python app.py
```

Navigate to `http://localhost:5000`.

## Environment variables

Create a `.env` file (see `.env.example`):

```
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.example.com
MAIL_PORT=465
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
```

## Usage

1. Register as an **employer** → add interview questions with expected keyword answers
2. Share the platform link with candidates
3. Candidate registers as an **employee** → selects employer → answers questions on video
4. Employer views the results dashboard — sentiment charts + keyword match scores per candidate
