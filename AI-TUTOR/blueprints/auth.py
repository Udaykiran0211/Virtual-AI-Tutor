from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # Update streak and last_active
            today = date.today()
            if user.last_active:
                last_active_date = user.last_active.date()
                if last_active_date == today - timedelta(days=1):
                    user.streak_count += 1
                elif last_active_date < today - timedelta(days=1):
                    user.streak_count = 1
            else:
                user.streak_count = 1
            user.last_active = datetime.utcnow()
            
            # Badge logic
            badges = json.loads(user.badges) if user.badges else []
            if user.streak_count >= 3 and not any(b['id'] == 'streak_3' for b in badges):
                badges.append({"id": "streak_3", "name": "3-Day Streak", "icon": "🔥", "desc": "Log in 3 days in a row!"})
            if user.streak_count >= 7 and not any(b['id'] == 'streak_7' for b in badges):
                badges.append({"id": "streak_7", "name": "7-Day Streak", "icon": "⚡", "desc": "Log in 7 days in a row!"})
            user.badges = json.dumps(badges)
            db.session.commit()
            
            login_user(user)
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({"status": "success", "redirect": "dashboard.html"})
            return redirect(url_for('main.dashboard'))
        
        if request.is_json:
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
        return "Invalid credentials", 401
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json() or request.form
        username = data.get('username')
        password = data.get('password')
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({"status": "error", "message": "User already exists"}), 400
            return "Username already exists", 400
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        if request.is_json:
            return jsonify({"status": "success", "message": "Account created"})
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
