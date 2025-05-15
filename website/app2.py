import os
from flask import Flask, request, jsonify, session
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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

    return jsonify({
        'username': user.username,
        'bio': user.bio,
        'avatar': user.avatar,
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
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            user.avatar = filename

    db.session.commit()

    return jsonify({'message': 'Profile updated', 'username': user.username})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)