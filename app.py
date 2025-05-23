from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager, csrf, init_extensions
from config import Config
import os
import re
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random

# Create a Flask app instance (only once)
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
init_extensions(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import models after db is initialized
from models import User, Customisation, Connection, Message

# Add timedelta to Jinja globals
app.jinja_env.globals.update(timedelta=timedelta)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    return re.match(pattern, password) is not None

def validate_student_id(student_id):
    # Student ID should be 8-12 alphanumeric characters
    pattern = r'^[A-Za-z0-9]{8,12}$'
    return re.match(pattern, student_id) is not None

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect')
def connect():
    return render_template('connect.html')

@app.route('/customise', methods=['GET', 'POST'])
@login_required
def customise():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Ensure the user has a customisation record
    if not hasattr(current_user, 'customisation') or current_user.customisation is None:
        new_customisation = Customisation(user_id=current_user.id)
        db.session.add(new_customisation)
        db.session.commit()
        
    if request.method == 'POST':
        # Get form data
        bio = request.form.get('bio')
        interests = request.form.get('interests')
        faculty = request.form.get('faculty')
        course = request.form.get('course')
        year_of_study = request.form.get('year_of_study')
        profile_picture = request.files.get('profile_picture')
        name = request.form.get('name')  # Get the name field
        
        # Debug information
        print(f"Received POST data: bio={bio[:20] if bio else 'None'}..., interests={interests[:50] if interests else 'None'}...")
        print(f"Faculty: {faculty}, Course: {course}, Year: {year_of_study}")
        print(f"Profile picture: {profile_picture.filename if profile_picture else 'None'}")
        print(f"Name: {name}")
        
        # Process profile picture if uploaded
        if profile_picture and profile_picture.filename:
            # Create static/uploads directory if it doesn't exist
            static_upload_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(static_upload_dir, exist_ok=True)
            
            # Save the file to both locations to ensure it's accessible
            filename = secure_filename(profile_picture.filename)
            
            # Save to app.config['UPLOAD_FOLDER'] (as defined in config.py)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(upload_path)
            print(f"Saved profile picture to: {upload_path}")
            
            # Also save to static/uploads for web access
            static_path = os.path.join(static_upload_dir, filename)
            # Need to seek to beginning of file since we already read it once
            profile_picture.seek(0)
            profile_picture.save(static_path)
            print(f"Saved profile picture to: {static_path}")
            
            # Update user's profile picture in database
            current_user.customisation.profile_picture = filename
        
        # Update user data
        current_user.customisation.bio = bio
        current_user.customisation.interests = interests
        current_user.customisation.faculty = faculty
        current_user.customisation.course = course
        
        # Update username if name field is provided
        if name and name.strip():
            current_user.username = name.strip()
        
        # Convert year_of_study to integer if it has a value
        if year_of_study:
            try:
                current_user.customisation.year_of_study = int(year_of_study)
            except ValueError:
                current_user.customisation.year_of_study = None
        else:
            current_user.customisation.year_of_study = None
        
        # Save changes to database
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customise'))
    
    return render_template('customise.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('customise'))
        
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        if not student_id or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('login'))
            
        user = User.query.filter_by(student_id=student_id).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.update_last_login()
            return redirect(url_for('customise'))
        else:
            flash('Invalid student ID or password', 'error')
            return redirect(url_for('login'))
            
    return render_template('register.html')  # Changed back to register.html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        student_id = request.form.get('student_id')
        
        # Validation
        if not all([username, email, password, student_id]):
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
            
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('register.html')
            
        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, and numbers', 'error')
            return render_template('register.html')
            
        if not validate_student_id(student_id):
            flash('Student ID must be 8-12 alphanumeric characters', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(student_id=student_id).first():
            flash('Student ID already registered', 'error')
            return render_template('register.html')
            
        try:
            # Create new user
            new_user = User(username=username, email=email, password=password, student_id=student_id)
            db.session.add(new_user)
            db.session.flush()  # This will get us the new user's ID
            
            # Create a Customisation record for the new user
            new_customisation = Customisation(user_id=new_user.id)
            db.session.add(new_customisation)
            
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}. Please try again.', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/jomgather')
def jomgather():
    # If user is not authenticated, redirect to register/login page
    if not current_user.is_authenticated:
        flash('Please login to access JomGather features', 'info')
        return redirect(url_for('register'))
        
    # Get all faculties, courses, and years for filter dropdowns
    faculties = db.session.query(Customisation.faculty).filter(Customisation.faculty.isnot(None)).distinct().all()
    faculties = [faculty[0] for faculty in faculties if faculty[0]]
    
    courses = db.session.query(Customisation.course).filter(Customisation.course.isnot(None)).distinct().all()
    courses = [course[0] for course in courses if course[0]]
    
    # Determine which tab is active
    active_tab = request.args.get('tab', 'find-partners')
    
    # Check if search was performed
    search_performed = any([
        request.args.get('faculty'), 
        request.args.get('course'), 
        request.args.get('year'), 
        request.args.get('interests')
    ])
    
    students = []
    connected_partners = []
    
    # Only search for students if in find-partners tab to avoid duplicate display
    if current_user.is_authenticated and active_tab == 'find-partners':
        # Initialize filters
        faculty_filter = request.args.get('faculty', '')
        course_filter = request.args.get('course', '')
        year_filter = request.args.get('year', '')
        interests_filter = request.args.get('interests', '')
        
        # Start with all users
        query = User.query.join(Customisation).filter(User.id != current_user.id)
        
        # Only apply filters if they're not empty
        if faculty_filter:
            query = query.filter(Customisation.faculty == faculty_filter)
        
        if course_filter:
            query = query.filter(Customisation.course == course_filter)
        
        if year_filter and year_filter.isdigit():
            query = query.filter(Customisation.year_of_study == int(year_filter))
        
        if interests_filter:
            # Search for interests as substring
            interest_terms = interests_filter.lower().split(',')
            for term in interest_terms:
                term = term.strip()
                if term:
                    query = query.filter(Customisation.interests.ilike(f'%{term}%'))
        
        # Execute query
        students = query.all()
    
    # Fetch connected partners if in my-partners tab
    elif current_user.is_authenticated and active_tab == 'my-partners':
        # Initialize filters
        faculty_filter = request.args.get('faculty', '')
        course_filter = request.args.get('course', '')
        year_filter = request.args.get('year', '')
        interests_filter = request.args.get('interests', '')
        
        # Get all accepted connections where the current user is involved
        connections_made = Connection.query.filter_by(user_id=current_user.id, status='accepted').all()
        connections_received = Connection.query.filter_by(connected_user_id=current_user.id, status='accepted').all()
        
        # Get the users involved in these connections
        partner_ids = []
        
        for conn in connections_made:
            partner_ids.append(conn.connected_user_id)
            
        for conn in connections_received:
            partner_ids.append(conn.user_id)
        
        # Query for partners with filters
        if partner_ids:
            query = User.query.join(Customisation).filter(User.id.in_(partner_ids))
            
            # Apply filters if specified
            if faculty_filter:
                query = query.filter(Customisation.faculty == faculty_filter)
            
            if course_filter:
                query = query.filter(Customisation.course == course_filter)
            
            if year_filter and year_filter.isdigit():
                query = query.filter(Customisation.year_of_study == int(year_filter))
            
            if interests_filter:
                # Search for interests as substring
                interest_terms = interests_filter.lower().split(',')
                for term in interest_terms:
                    term = term.strip()
                    if term:
                        query = query.filter(Customisation.interests.ilike(f'%{term}%'))
            
            # Execute query
            connected_partners = query.all()
    
    return render_template('jomgather.html', 
                           students=students,
                           connected_partners=connected_partners,
                           faculties=faculties,
                           courses=courses,
                           search_performed=search_performed,
                           active_tab=active_tab)

@app.route('/find_students', methods=['GET', 'POST'])
@login_required
def find_students():
    # Redirect to jomgather route with the same query parameters
    return redirect(url_for('jomgather', **request.args))

@app.route('/connect/<int:user_id>', methods=['POST'])
@login_required
def connect_with_user(user_id):
    # Check if the user exists
    user_to_connect = User.query.get_or_404(user_id)
    
    # Check if a connection already exists
    existing_connection = Connection.query.filter(
        ((Connection.user_id == current_user.id) & (Connection.connected_user_id == user_id)) |
        ((Connection.user_id == user_id) & (Connection.connected_user_id == current_user.id))
    ).first()
    
    if existing_connection:
        flash('You already have a connection with this user', 'info')
    else:
        # Create a new connection
        new_connection = Connection(
            user_id=current_user.id,
            connected_user_id=user_id,
            status='pending'
        )
        db.session.add(new_connection)
        try:
            db.session.commit()
            flash('Connection request sent!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
    
    # Redirect back to where the request came from
    return redirect(request.referrer or url_for('jomgather'))

@app.route('/connections', endpoint='view_connections')
@login_required
def view_connections():
    # Get all connections where the current user is involved
    connections_made = Connection.query.filter_by(user_id=current_user.id).all()
    connections_received = Connection.query.filter_by(connected_user_id=current_user.id).all()
    
    # Get the users involved in these connections
    connected_users = []
    
    for conn in connections_made:
        user = User.query.get(conn.connected_user_id)
        if user:
            connected_users.append({
                'connection_id': conn.id,
                'user': user,
                'status': conn.status,
                'initiator': True,
                'created_at': conn.created_at
            })
            
    for conn in connections_received:
        user = User.query.get(conn.user_id)
        if user:
            connected_users.append({
                'connection_id': conn.id,
                'user': user,
                'status': conn.status,
                'initiator': False,
                'created_at': conn.created_at
            })
    
    # Sort by most recent
    connected_users.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('connections.html', connections=connected_users)

@app.route('/connection/<int:connection_id>/accept', methods=['POST'])
@login_required
def accept_connection(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Ensure the current user is the one receiving the request
    if connection.connected_user_id != current_user.id:
        flash('You are not authorized to accept this connection', 'error')
        return redirect(url_for('view_connections'))
    
    connection.status = 'accepted'
    db.session.commit()
    flash('Connection accepted!', 'success')
    
    # Redirect to chat with the user who sent the request
    return redirect(url_for('chat', user_id=connection.user_id))

@app.route('/connection/<int:connection_id>/reject', methods=['POST'])
@login_required
def reject_connection(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Ensure the current user is the one receiving the request
    if connection.connected_user_id != current_user.id:
        flash('You are not authorized to reject this connection', 'error')
        return redirect(url_for('view_connections'))
    
    # Instead of marking as rejected, delete the connection
    db.session.delete(connection)
    db.session.commit()
    flash('Connection request rejected', 'success')
    return redirect(url_for('view_connections'))

@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    # Find the other user
    other_user = User.query.get_or_404(user_id)
    
    # Find the connection between the users
    connection = Connection.query.filter(
        ((Connection.user_id == current_user.id) & (Connection.connected_user_id == user_id)) |
        ((Connection.user_id == user_id) & (Connection.connected_user_id == current_user.id))
    ).first()
    
    if not connection or connection.status != 'accepted':
        flash('You must be connected with this user to chat', 'error')
        return redirect(url_for('view_connections'))
    
    # Get all messages in this connection
    messages = Message.query.filter_by(connection_id=connection.id).order_by(Message.created_at).all()
    
    # Mark all messages from the other user as read
    unread_messages = Message.query.filter_by(
        connection_id=connection.id,
        sender_id=other_user.id,
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return render_template('chat.html', other_user=other_user, connection=connection, messages=messages)

@app.route('/chat/<int:connection_id>/send', methods=['POST'])
@login_required
def send_message(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Ensure the current user is part of this connection
    if connection.user_id != current_user.id and connection.connected_user_id != current_user.id:
        flash('You are not authorized to send messages in this chat', 'error')
        return redirect(url_for('view_connections'))
    
    # Ensure the connection is accepted
    if connection.status != 'accepted':
        flash('This connection has not been accepted yet', 'error')
        return redirect(url_for('view_connections'))
    
    # Get the message content
    content = request.form.get('message', '').strip()
    
    if not content:
        flash('Message cannot be empty', 'error')
        
        # Determine which user to redirect to for the chat
        other_user_id = connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
        return redirect(url_for('chat', user_id=other_user_id))
    
    # Create the new message
    new_message = Message(
        connection_id=connection_id,
        sender_id=current_user.id,
        content=content
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Determine which user to redirect to for the chat
    other_user_id = connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
    return redirect(url_for('chat', user_id=other_user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/pass', endpoint='pass_page')
def password_reset_page():
    return render_template('pass.html')

@app.route('/update-password', methods=['POST'])
def update_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # 使用正确的字段名 (student_id)
        student_id = data.get('student_id')
        new_password = data.get('new_password')

        # 验证字段
        if not all([student_id, new_password]):
            return jsonify({'success': False, 'error': 'Missing student ID or new password'}), 400

        # 查找用户
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Student ID not found'}), 404

        # 更新密码
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        # 记录成功日志
        app.logger.info(f"Password updated for student_id: {student_id}")
        
        return jsonify({
            'success': True,
            'message': 'Password updated successfully!'
        })

    except Exception as e:
        db.session.rollback()
        # 记录详细错误信息
        app.logger.error(f"Password update failed for {student_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update password. Please try again.'
        }), 500

@app.route('/match')
def match():
    if not current_user.is_authenticated:
        flash('Please login to access matching features', 'info')
        return redirect(url_for('login'))
    
    # 获取所有院系用于筛选
    faculties = db.session.query(Customisation.faculty).filter(Customisation.faculty.isnot(None)).distinct().all()
    faculties = [faculty[0] for faculty in faculties if faculty[0]]
    
    return render_template('match.html', faculties=faculties)

@app.route('/api/match/<match_type>')
@login_required
def match_users(match_type):
    try:
        # 获取筛选条件
        faculty = request.args.get('faculty')
        year = request.args.get('year')
        
        # 基础查询
        query = User.query.filter(
            User.id != current_user.id,
            User.is_active == True
        ).join(Customisation)
        
        # 应用筛选
        if faculty:
            query = query.filter(Customisation.faculty == faculty)
        if year:
            query = query.filter(Customisation.year_of_study == int(year))
        
        if match_type == 'random':
            # 随机匹配
            available_users = query.all()
            if not available_users:
                return jsonify({'success': False, 'error': 'no match user'})
            
            matched_user = random.choice(available_users)
            return jsonify({
                'success': True,
                'user': format_user(matched_user)
            })
            
        elif match_type == 'smart':
            # 智能匹配（基于共同兴趣）
            current_interests = set()
            if current_user.customisation and current_user.customisation.interests:
                current_interests = set(current_user.customisation.interests.split(','))
            
            best_match = None
            highest_score = 0
            
            for user in query.all():
                user_interests = set()
                if user.customisation and user.customisation.interests:
                    user_interests = set(user.customisation.interests.split(','))
                
                # 计算匹配分数
                common_interests = current_interests & user_interests
                score = len(common_interests)
                
                # 相同院系加分
                if (current_user.customisation and user.customisation and 
                    current_user.customisation.faculty == user.customisation.faculty):
                    score += 2
                
                if score > highest_score:
                    highest_score = score
                    best_match = user
            
            if best_match:
                result = format_user(best_match)
                result['common_interests'] = list(common_interests)
                return jsonify({'success': True, 'user': result})
            else:
                return jsonify({'success': False, 'error': 'no suitable match found'}), 404
                
        else:
            return jsonify({'success': False, 'error': 'invalid match type'}), 400
            
    except Exception as e:
        app.logger.error(f"Match error: {str(e)}")
        return jsonify({'success': False, 'error': 'server error'}), 500

def format_user(user):
    """格式化用户数据"""
    return {
        'id': user.id,
        'username': user.username,
        'faculty': user.customisation.faculty if user.customisation else None,
        'interests': user.customisation.interests.split(',') if user.customisation and user.customisation.interests else [],
        'avatar': url_for('static', filename=f"uploads/{user.customisation.profile_picture}") if user.customisation and user.customisation.profile_picture else None
    }

@app.errorhandler(404)
@app.errorhandler(500)
def handle_api_errors(e):
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': str(e.description) if hasattr(e, 'description') else 'An error occurred'
        }), e.code
    return e

# Run the app if this file is executed
if __name__ == '__main__':
    with app.app_context():
        # Check if tables need to be created
        db.create_all()
        print("Database tables created or confirmed to exist.")
        print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # List the tables that were created
        print(f"Tables created: {', '.join(db.metadata.tables.keys())}")
    app.run(debug=True)