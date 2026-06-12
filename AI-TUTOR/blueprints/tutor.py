from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import json
import asyncio
import requests
from extensions import db
from models import Note, QuizResult, Progress, User
from utils.youtube_api import get_youtube_video
from utils.llm_api import generate_technical_notes, get_chat_response, generate_quiz, generate_custom_roadmap, generate_quiz_review

tutor_bp = Blueprint('tutor', __name__)

@tutor_bp.route('/roadmap/<language>')
@login_required
def get_roadmap(language):
    try:
        with open('data/roadmap.json', 'r') as f:
            data = json.load(f)
        return jsonify(data.get(language, {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tutor_bp.route('/tutor/<language>')
@tutor_bp.route('/tutor/<language>/<topic_id>')
@login_required
def tutor(language, topic_id='start'):
    return render_template('tutor.html', language=language, topic_id=topic_id)

@tutor_bp.route('/api/video', methods=['POST'])
@login_required
def get_video():
    data = request.json
    topic = data.get('topic')
    language = data.get('language', 'programming')
    refresh = data.get('refresh', False)
    video_url = get_youtube_video(topic, language, force_refresh=refresh)
    return jsonify({"video_url": video_url})

@tutor_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    topic = data.get('topic')
    query = data.get('query')
    history = data.get('history', [])
    is_interview = data.get('interview_mode', False)
    response = asyncio.run(get_chat_response(query, topic, history, is_interview))
    return jsonify({"response": response})

@tutor_bp.route('/api/execute', methods=['POST'])
@login_required
def execute_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    lang_map = {
        'python': {'language': 'python', 'version': '3.10.0'},
        'java': {'language': 'java', 'version': '15.0.2'},
        'cpp': {'language': 'cpp', 'version': '10.2.0'}
    }
    
    config = lang_map.get(language, lang_map['python'])
    payload = {
        "language": config['language'],
        "version": config['version'],
        "files": [{"content": code}]
    }
    
    try:
        resp = requests.post('https://emkc.org/api/v2/piston/execute', json=payload, timeout=10)
        result = resp.json()
        if 'run' in result:
            output = result['run'].get('output', '')
            if result['run'].get('code', 0) != 0:
                output = result['run'].get('stderr', '') or output
            return jsonify({"output": output})
        return jsonify({"error": result.get('message', 'Execution error')}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tutor_bp.route('/api/review_quiz', methods=['POST'])
@login_required
def review_quiz():
    data = request.json
    errors = data.get('errors')
    topic = data.get('topic')
    feedback = asyncio.run(generate_quiz_review(errors, topic))
    return jsonify({"feedback": feedback})

@tutor_bp.route('/api/quiz', methods=['POST'])
@login_required
def quiz():
    data = request.json
    topic = data.get('topic')
    language = data.get('language', 'programming')
    quiz_data = asyncio.run(generate_quiz(topic, language))
    return jsonify({"quiz": quiz_data})

@tutor_bp.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    data = request.json
    topic_id = data.get('topic_id')
    language = data.get('language')
    score = data.get('score')
    total_questions = data.get('total_questions')
    
    result = QuizResult(
        user_id=current_user.id,
        topic_id=topic_id,
        language=language,
        score=score,
        total_questions=total_questions
    )
    db.session.add(result)
    
    # Also update progress
    prog = Progress.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    if not prog:
        prog = Progress(user_id=current_user.id, topic_id=topic_id, language=language)
        db.session.add(prog)
    
    prog.completed = True
    if prog.score is None or score > prog.score:
        prog.score = score
        
    badges = json.loads(current_user.badges) if current_user.badges else []
    if score == total_questions and total_questions > 0:
        if not any(b['id'] == 'perfect_quiz' for b in badges):
            badges.append({"id": "perfect_quiz", "name": "Perfect Score", "icon": "⭐", "desc": "Ace an assessment with 100% accuracy."})
            
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    if quiz_count >= 5:
        if not any(b['id'] == 'quiz_5' for b in badges):
            badges.append({"id": "quiz_5", "name": "Quiz Master", "icon": "🧠", "desc": "Complete 5 assessments."})
    
    current_user.badges = json.dumps(badges)
    db.session.commit()
    return jsonify({"status": "success", "message": "Quiz result saved"})

@tutor_bp.route('/api/progress', methods=['POST'])
@login_required
def update_progress():
    data = request.json
    topic_id = data.get('topic_id')
    language = data.get('language')
    completed = data.get('completed', True)
    score = data.get('score', 0)
    
    prog = Progress.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    if not prog:
        prog = Progress(user_id=current_user.id, topic_id=topic_id, language=language)
        db.session.add(prog)
    
    prog.completed = completed
    prog.score = score
    db.session.commit()
    return jsonify({"status": "success"})

@tutor_bp.route('/api/notes/save', methods=['POST'])
@login_required
def save_note():
    data = request.json
    topic_id = data.get('topic_id')
    content = data.get('content')
    
    note = Note.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    if not note:
        note = Note(user_id=current_user.id, topic_id=topic_id)
        db.session.add(note)
    
    note.content = content
    db.session.commit()
    return jsonify({"status": "success"})

@tutor_bp.route('/api/notes/load/<topic_id>')
@login_required
def load_note(topic_id):
    note = Note.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    return jsonify({"content": note.content if note else ""})

@tutor_bp.route('/api/custom_roadmap', methods=['POST'])
@login_required
def custom_roadmap():
    data = request.json
    goal = data.get('goal')
    language = data.get('language')
    roadmap = asyncio.run(generate_custom_roadmap(goal, language))
    return jsonify(roadmap)

@tutor_bp.route('/api/notes', methods=['POST'])
@login_required
def get_notes():
    data = request.json
    topic = data.get('topic')
    language = data.get('language', 'programming')
    notes = asyncio.run(generate_technical_notes(topic, language))
    return jsonify({"notes": notes})
