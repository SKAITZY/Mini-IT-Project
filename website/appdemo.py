import os
from flask import Flask, request, jsonify, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user, LoginManager
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database
with app.app_context():
    db.create_all()

# Utility: check allowed file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Get profile
@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate avatar URL if avatar exists
    avatar_url = None
    if user.avatar:
        avatar_url = url_for('get_avatar', filename=user.avatar, _external=True)

    return jsonify({
        'username': user.username,
        'bio': user.bio,
        'avatar': user.avatar,
        'avatar_url': avatar_url,
        'theme': user.theme,
        'layout': user.layout
    })

# Update profile
@app.route('/profile/<username>', methods=['PUT'])
@login_required  # Added login_required decorator for authentication
def update_profile(username):
    # Check if current user is updating their own profile
    if current_user.username != username:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    bio = request.form.get('bio')
    theme = request.form.get('theme')
    layout = request.form.get('layout')

    if bio: user.bio = bio
    if theme: user.theme = theme
    if layout: user.layout = layout

    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename != '':
            if allowed_file(file.filename):
                # Generate unique filename to prevent overwriting
                # Use user ID and timestamp for uniqueness
                import time
                filename = f"{user.id}_{int(time.time())}_{secure_filename(file.filename)}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                file.save(filepath)
                
                # Update user avatar field with the new filename
                user.avatar = filename
            else:
                return jsonify({
                    'error': 'Invalid file format. Allowed formats: ' + 
                    ', '.join(app.config['ALLOWED_EXTENSIONS'])
                }), 400

    db.session.commit()

    # Return profile data with avatar URL
    avatar_url = None
    if user.avatar:
        avatar_url = url_for('get_avatar', filename=user.avatar, _external=True)
    
    return jsonify({
        'message': 'Profile updated', 
        'username': user.username,
        'avatar_url': avatar_url
    })

# Serve avatar images
@app.route('/avatar/<filename>')
def get_avatar(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Serve user profile as HTML for testing
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'Unauthorized'}), 401

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)