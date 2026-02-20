from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import db, AuthUser

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# OAuth Setup
from authlib.integrations.flask_client import OAuth

print(f"DEBUG: GOOGLE_CLIENT_ID loaded: {bool(app.config['GOOGLE_CLIENT_ID'])}")
print(f"DEBUG: GOOGLE_CLIENT_SECRET loaded: {bool(app.config['GOOGLE_CLIENT_SECRET'])}")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
         return jsonify({'message': 'Failed to fetch user info from Google'}), 400

    google_id = user_info['sub']
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0]) # Use name or fallback to part of email

    # 1. Check if user exists by google_id
    user = AuthUser.query.filter_by(google_id=google_id).first()

    if not user:
        # 2. Check if email exists (link account)
        user = AuthUser.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id # Link existing account
        else:
            # 3. Create new user
            user = AuthUser(
                username=name.replace(" ", "_"), # Simple username generation
                email=email,
                google_id=google_id,
                role='USER' 
            )
            db.session.add(user)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Database error: {str(e)}'}), 500

    # Generate JWT
    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role, 'email': user.email, 'username': user.username})
    print(f"DEBUG: Generated Google token for user {user.username}: {access_token[:20]}...")
    
    # Return standard login response
    return jsonify({
        'access_token': access_token, 
        'role': user.role, 
        'user_id': user.id,
        'username': user.username,
        'email': user.email
    }), 200


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing fields'}), 400

    if AuthUser.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400

    new_user = AuthUser(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'USER') 
    )
    new_user.set_password(data['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully', 'user_id': new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = AuthUser.query.filter_by(username=data.get('username')).first()

    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role, 'email': user.email, 'username': user.username})
    print(f"DEBUG: Generated token for user {user.username}: {access_token[:20]}...")
    return jsonify({'access_token': access_token, 'role': user.role, 'user_id': user.id}), 200

@app.route('/auth/verify', methods=['POST'])
@jwt_required()
def verify():
    current_user_id = get_jwt_identity()
    return jsonify({'valid': True, 'user_id': current_user_id}), 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)
