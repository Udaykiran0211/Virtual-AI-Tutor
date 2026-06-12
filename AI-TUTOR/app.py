import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from extensions import db, login_manager
from config import Config
from models import User

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='.')
    app.config.from_object(config_class)
    
    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app, supports_credentials=True)
    
    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.tutor import tutor_bp
    from blueprints.social import social_bp
    from blueprints.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(tutor_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(main_bp)

    @app.before_request
    def auto_login_dev():
        from flask_login import login_user, current_user
        from models import User
        from werkzeug.security import generate_password_hash
        
        if request.path.startswith('/static') or request.path == '/favicon.ico':
            return
            
        is_local = (request.host.startswith('127.0.0.1') or request.host.startswith('localhost')) and not os.environ.get('RENDER')
        if is_local and not current_user.is_authenticated:
            try:
                user = User.query.filter_by(username='Student').first()
                if not user:
                    user = User(username='Student', password=generate_password_hash('password'))
                    db.session.add(user)
                    db.session.commit()
            except Exception:
                db.session.rollback()
                user = User.query.filter_by(username='Student').first()
                
            if user:
                login_user(user, remember=True)


    @login_manager.user_loader

    def load_user(user_id):
        return User.query.get(int(user_id))

    # Global Error Handlers
    @app.errorhandler(Exception)
    def handle_exception(e):
        if hasattr(e, 'code'):
            return jsonify({"error": str(e), "code": e.code}), e.code
        print(f"DEBUG: Unhandled Exception: {e}", flush=True)
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    # Global CORS/Headers
    @app.after_request
    def add_header(response):
        origin = request.headers.get('Origin')
        if origin and (origin.startswith('http://127.0.0.1') or origin.startswith('http://localhost')):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Private-Network'] = 'true'
        
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        
        # Handle Preflight OPTIONS
        if request.method == 'OPTIONS':
            response.status_code = 200
            
        return response

    return app

app = create_app()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
