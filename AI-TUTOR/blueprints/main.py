from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
import json
from extensions import db
from models import User, Progress, QuizResult

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/api/user_stats')
@login_required
def get_user_stats():
    assessments_count = Progress.query.filter_by(user_id=current_user.id).count()
    
    total_modules = 0
    try:
        with open('data/roadmap.json', 'r') as f:
            rd = json.load(f)
            for lang in rd:
                for level in rd[lang]:
                    total_modules += len(rd[lang][level])
    except:
        total_modules = 18
    
    completed_modules = Progress.query.filter_by(user_id=current_user.id, completed=True).count()
    progress_percent = int((completed_modules / total_modules) * 100) if total_modules > 0 else 0

    recent_lessons = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.id.desc()).limit(5).all()
    lessons_data = [{"topic_id": l.topic_id, "language": l.language, "completed": l.completed} for l in recent_lessons]

    quiz_results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.desc()).all()
    quizzes_data = [{"topic_id": q.topic_id, "language": q.language, "score": q.score, "total_questions": q.total_questions, "timestamp": q.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for q in quiz_results]

    if progress_percent < 25: role = "Beginner"
    elif progress_percent < 50: role = "Explorer"
    elif progress_percent < 80: role = "Scholar"
    else: role = "Academic"
        
    plan = "Basic Plan" if current_user.streak_count < 10 else "Pro Plan"

    return jsonify({
        "username": current_user.username,
        "assessments_count": assessments_count,
        "progress_percent": progress_percent,
        "recent_lessons": lessons_data,
        "quiz_history": quizzes_data,
        "streak_count": current_user.streak_count,
        "role": role,
        "plan": plan
    })

@main_bp.route('/api/heartbeat', methods=['GET'])
def heartbeat():
    return jsonify({
        "status": "ok", 
        "message": "Backend modularized and alive!",
        "authenticated": current_user.is_authenticated
    })

@main_bp.route('/api/leaderboard', methods=['GET'])
@login_required
def get_leaderboard():
    top_users = User.query.order_by(User.streak_count.desc()).limit(10).all()
    leaderboard = [{"username": u.username, "streak_count": u.streak_count, "badges_count": len(json.loads(u.badges)) if u.badges else 0, "is_current": u.id == current_user.id} for u in top_users]
    return jsonify({"leaderboard": leaderboard})

@main_bp.route('/<path:path>.html')
def serve_html(path):
    if path in ['index', 'login', 'signup', 'dashboard']:
        if path == 'index':
            return redirect(url_for('main.index'))
        elif path == 'dashboard':
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for(f'auth.{path}'))
    if path == 'tutor':
        lang = request.args.get('lang', 'python')
        topic = request.args.get('topic', 'start')
        return redirect(url_for('tutor.tutor', language=lang, topic_id=topic))
    return render_template(f'{path}.html')
