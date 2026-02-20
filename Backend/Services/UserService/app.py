from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import Config
from models import db, UserProfile

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

@app.route('/users/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    profile = UserProfile.query.filter_by(auth_user_id=user_id).first()
    
    if not profile:
        return jsonify({'message': 'Profile not found', 'user_id': user_id}), 404
        
    return jsonify({
        'user_id': profile.auth_user_id,
        'full_name': profile.full_name,
        'phone_number': profile.phone_number
    }), 200

@app.route('/users/me', methods=['POST', 'PUT'])
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    profile = UserProfile.query.filter_by(auth_user_id=user_id).first()
    if not profile:
        profile = UserProfile(auth_user_id=user_id)
        db.session.add(profile)
    
    if 'full_name' in data:
        profile.full_name = data['full_name']
    if 'phone_number' in data:
        profile.phone_number = data['phone_number']
        
    try:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)
