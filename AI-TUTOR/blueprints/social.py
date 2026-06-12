from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, FriendRequest, Friendship, Message

social_bp = Blueprint('social', __name__)

@social_bp.route('/api/friends/search', methods=['GET'])
@login_required
def search_friends():
    query = request.args.get('q', '')
    if not query: return jsonify({"users": []})
    users = User.query.filter(User.username.ilike(f'%{query}%'), User.id != current_user.id).limit(5).all()
    return jsonify({"users": [{"id": u.id, "username": u.username} for u in users]})

@social_bp.route('/api/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    receiver_id = request.json.get('receiver_id')
    if receiver_id == current_user.id: return jsonify({"error": "Cannot friend yourself"}), 400
    existing = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=receiver_id, status='pending').first()
    if existing: return jsonify({"status": "success"}) # already sent
    freq = FriendRequest(sender_id=current_user.id, receiver_id=receiver_id)
    db.session.add(freq)
    db.session.commit()
    return jsonify({"status": "success"})

@social_bp.route('/api/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    reqs = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    res = []
    for r in reqs:
        sender = User.query.get(r.sender_id)
        if sender: res.append({"id": r.id, "sender_id": sender.id, "sender_name": sender.username})
    return jsonify({"requests": res})

@social_bp.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend():
    req_id = request.json.get('request_id')
    action = request.json.get('action') # 'accept' or 'decline'
    req = FriendRequest.query.get(req_id)
    if not req or req.receiver_id != current_user.id: return jsonify({"error": "Invalid"}), 400
    
    req.status = action
    if action == 'accept':
        existing = Friendship.query.filter_by(user_id=current_user.id, friend_id=req.sender_id).first()
        if not existing:
            f1 = Friendship(user_id=current_user.id, friend_id=req.sender_id)
            f2 = Friendship(user_id=req.sender_id, friend_id=current_user.id)
            db.session.add_all([f1, f2])
    db.session.commit()
    return jsonify({"status": "success"})

@social_bp.route('/api/friends/list', methods=['GET'])
@login_required
def get_friends():
    friends = Friendship.query.filter_by(user_id=current_user.id).all()
    res = []
    for f in friends:
        friend_user = User.query.get(f.friend_id)
        if friend_user: res.append({"id": friend_user.id, "username": friend_user.username})
    return jsonify({"friends": res})

@social_bp.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')
    if not receiver_id or not content: return jsonify({"error": "Missing data"}), 400
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "success", "message": {"id": msg.id, "content": msg.content, "timestamp": msg.timestamp.strftime('%I:%M %p')}})

@social_bp.route('/api/messages/history/<int:friend_id>', methods=['GET'])
@login_required
def get_chat_history(friend_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    
    res = [{"id": m.id, "content": m.content, "sender_id": m.sender_id, "timestamp": m.timestamp.strftime('%I:%M %p')} for m in messages]
    return jsonify({"messages": res})
