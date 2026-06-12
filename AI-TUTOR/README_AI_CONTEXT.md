# Project: AI-TUTOR (AI-Powered Learning Platform)

## 🎯 Overview
AI-TUTOR is a personalized learning platform that uses Google Gemini to generate custom roadmaps, provide real-time tutoring, and create interactive quizzes for programming languages (Python, Java, C++).

## 🛠️ Tech Stack
- **Backend**: Python 3.9+ (Flask, Flask-SQLAlchemy, Flask-Login)
- **Frontend**: Vanilla JS, HTML, CSS (Modern Glassmorphism UI)
- **Database**: SQLite (SQLAlchemy ORM)
- **AI/APIs**: 
  - **Google Gemini Pro**: Tutoring, Roadmap generation, Quiz creation.
  - **YouTube Data API**: Automated relevance-based video tutorials.
  - **Piston API**: In-browser code execution sandbox.

## 📂 Key Files & Structure
- `app.py`: Main Flask application with API endpoints for all features.
- `utils/llm_api.py`: Gemini AI integration (Chat, Roadmaps, Quizzes).
- `utils/youtube_api.py`: YouTube search logic.
- `static/js/api-client.js`: Frontend API wrapper with resilience/bypass modes.
- `data/roadmap.json`: Predefined learning paths for various languages.
- `templates/`: Interactive pages (`dashboard.html`, `tutor.html`, `messages.html`).

## 🚀 Core Functionalities
1. **AI Tutoring**: Interactive chat & technical notes generation (Gemini).
2. **Dynamic Roadmaps**: Goal-based learning paths with module tracking.
3. **Quizzes & Stats**: AI-generated assessments + XP, streaks, and badges.
4. **Code Sandbox**: Multi-language execution in the browser.
5. **Social**: Friend requests, real-time messaging, and leaderboards.

## 🔑 Environment Variables
- `GOOGLE_API_KEY`: For Gemini and YouTube.
- `SECRET_KEY`: Flask session security.
- `DATABASE_URL`: (Optional, defaults to local SQLite).
