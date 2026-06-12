# AI-TUTOR: Intelligent Learning Platform

[![Status](https://img.shields.io/badge/Status-Development-orange.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![AI](https://img.shields.io/badge/AI-Google%20Gemini-purple.svg)](https://deepmind.google/technologies/gemini/)

**AI-TUTOR** is a state-of-the-art, AI-powered educational platform designed to provide a personalized, immersive learning experience for students and developers. By leveraging advanced generative AI, AI-TUTOR creates custom learning paths, provides real-time tutoring, and evaluates progress through dynamic assessments.

---

## 🚀 Key Features

### 🧠 Intelligent Tutoring & Roadmaps
- **Custom Roadmaps**: Generate personalized learning paths based on your goals and target programming language (Python, Java, C++, etc.).
- **Live AI Chat**: Interact with an AI tutor (powered by Google Gemini) for instant clarifications, code explanations, and concept deep-dives.
- **Technical Notes**: Automatically generate comprehensive study notes for any topic in your roadmap.

### 🎥 Curated Visual Learning
- **AI-Driven Video Search**: Seamless integration with the YouTube API to fetch the most relevant, high-quality tutorials for each specific lesson.
- **Interactive Video Player**: Learn visually with a centered focus on top-tier educational content.

### 📝 Assessments & Growth
- **Dynamic Quizzes**: AI-generated assessments that test your knowledge on specific topics.
- **Progress Tracking**: Monitor your journey with detailed stats, module completion status, and score history.
- **Gamification**: Stay motivated with daily streaks, earnable badges, and a global leaderboard.

### 💻 Integrated Code Sandbox
- **In-Browser Execution**: Test your code immediately within the platform using the integrated Piston API sandbox.
- **Multi-Language Support**: Run Python, Java, and C++ code directly in your browser without any local setup.

### 🤝 Social & Community
- **Friends System**: Search for and connect with other learners.
- **Real-Time Messaging**: Chat with friends to discuss topics or share progress.
- **Leaderboard**: Compete with others for the highest streaks and most badges earned.

---

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML5, CSS3 (Modern Glassmorphism Design), JavaScript (ES6+).
- **Backend**: [Flask](https://flask.palletsprojects.com/) (Python).
- **Database**: [SQLite](https://www.sqlite.org/) with [SQLAlchemy](https://www.sqlalchemy.org/) ORM.
- **AI Models**: [Google Gemini Pro](https://deepmind.google/technologies/gemini/) (Text & Chat).
- **External APIs**: 
    - YouTube Data API (Video search).
    - Piston API (Code execution).
- **Authentication**: [Flask-Login](https://flask-login.readthedocs.io/).

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9 or higher.
- A Google API Key (for YouTube and Gemini).

### Step-by-Step Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd AI-TUTOR
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here
   SECRET_KEY=your_flask_secret_key_here
   ```
   *(Refer to `.env.example` for all required fields.)*

5. **Initialize Database & Run**:
   ```bash
   python app.py
   ```
   The application will be available at `http://127.0.0.1:5000`.

---

## 📂 Project Structure

```text
AI-TUTOR/
├── app.py              # Main Flask application & API routes
├── models.py           # Database models (Optional: check app.py)
├── static/             # Frontend assets (CSS, JS, Images)
│   ├── css/            # Modern UI stylesheets
│   └── js/             # API client & UI logic
├── data/               # Static data files (Roadmaps, etc.)
├── utils/              # Helper modules (AI integration, APIs)
├── templates/          # HTML pages (or root .html files)
└── requirements.txt    # Project dependencies
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

- Powered by **Google Gemini** for intelligent tutoring.
- Code execution provided by the **Piston API**.
- UI inspired by modern educational platforms and glassmorphism design principles.
