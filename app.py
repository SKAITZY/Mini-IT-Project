from flask import Flask, redirect, url_for, render_template, request, flash, session, jsonify, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager, csrf, init_extensions
from config import Config
import os
import re
import click
from flask.cli import with_appcontext
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random
import pyotp  # 确保你已经安装 pyotp: pip install pyotp
from flask_migrate import Migrate
from models import User, Customisation, Connection, Message




# Create a Flask app instance (only once)
app = Flask(__name__)
app.config.from_object(Config)
migrate = Migrate(app, db)  # ✅ 加这行

# Initialize extensions
init_extensions(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import models after db is initialized
from models import User, Customisation, Connection, Message, Gathering, GatheringParticipant, GatheringMessage

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
        email = request.form.get('email')  # Get the email field
        
        # Debug information
        print(f"Received POST data: bio={bio[:20] if bio else 'None'}..., interests={interests[:50] if interests else 'None'}...")
        print(f"Faculty: {faculty}, Course: {course}, Year: {year_of_study}")
        print(f"Profile picture: {profile_picture.filename if profile_picture else 'None'}")
        print(f"Name: {name}, Email: {email}")
        
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
        
        # Update email if email field is provided and valid
        if email and email.strip():
            # Check if the email is already in use by another user
            existing_user = User.query.filter(User.email == email.strip(), User.id != current_user.id).first()
            if existing_user:
                flash('Email already in use by another account', 'error')
            elif validate_email(email.strip()):
                current_user.email = email.strip()
            else:
                flash('Invalid email format', 'error')
        
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

@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    # Get the user's ID
    user_id = current_user.id
    
    try:
        # Delete user's connections (sent and received)
        Connection.query.filter((Connection.user_id == user_id) | 
                              (Connection.connected_user_id == user_id)).delete()
        
        # Delete user's messages
        Message.query.filter(Message.sender_id == user_id).delete()
        
        # Delete gathering participants records
        GatheringParticipant.query.filter_by(user_id=user_id).delete()
        
        # Delete gathering messages
        GatheringMessage.query.filter_by(user_id=user_id).delete()
        
        # Delete gatherings created by the user
        gatherings = Gathering.query.filter_by(user_id=user_id).all()
        for gathering in gatherings:
            # First delete all participants of this gathering
            GatheringParticipant.query.filter_by(gathering_id=gathering.id).delete()
            # Then delete all messages of this gathering
            GatheringMessage.query.filter_by(gathering_id=gathering.id).delete()
            # Now delete the gathering itself
            db.session.delete(gathering)
        
        # Delete user's customisation
        Customisation.query.filter_by(user_id=user_id).delete()
        
        # Finally, delete the user
        User.query.filter_by(id=user_id).delete()
        
        # Commit all changes
        db.session.commit()
        
        # Log the user out
        logout_user()
        
        flash('Your account has been permanently deleted.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting your account: {str(e)}. Please try again.', 'error')
        return redirect(url_for('customise'))

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
        request.args.get('interests'),
        request.args.get('location')
    ])
    
    students = []
    connected_partners = []
    my_gatherings = []
    all_gatherings = []
    
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
    
    # Fetch gatherings for the "My Gatherings" tab
    elif current_user.is_authenticated and active_tab == 'my-gatherings':
        # Get gatherings created by the user that are not canceled
        created_gatherings = Gathering.query.filter_by(
            user_id=current_user.id
        ).filter(Gathering.status != 'canceled').all()
        
        # Get gatherings the user is participating in but didn't create
        participant_gatherings_ids = db.session.query(GatheringParticipant.gathering_id)\
            .filter(GatheringParticipant.user_id == current_user.id)\
            .filter(GatheringParticipant.status == 'joined').all()
        
        participant_gatherings_ids = [g[0] for g in participant_gatherings_ids]
        
        # Exclude gatherings created by user to avoid duplicates, and exclude canceled gatherings
        attending_gatherings = Gathering.query.filter(
            Gathering.id.in_(participant_gatherings_ids),
            Gathering.user_id != current_user.id,
            Gathering.status != 'canceled'
        ).all()
        
        # Combine the gatherings with a flag to indicate if user is host
        for gathering in created_gatherings:
            participants_count = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id, 
                status='joined'
            ).count()
            
            creator = User.query.get(gathering.user_id)
            
            # Get all participants for this gathering
            participants_query = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id,
                status='joined'
            ).all()
            
            participants = []
            for participant in participants_query:
                participant_user = User.query.get(participant.user_id)
                if participant_user:
                    participants.append(participant_user)
            
            # Debug: Print participants
            print(f"Gathering {gathering.id} - {gathering.title} participants:")
            for p in participants:
                print(f"  - User ID: {p.id}, Username: {p.username}")
            
            my_gatherings.append({
                'gathering': gathering,
                'is_host': True,
                'participants_count': participants_count,
                'creator': creator,
                'participants': participants
            })
            
        for gathering in attending_gatherings:
            participants_count = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id, 
                status='joined'
            ).count()
            
            creator = User.query.get(gathering.user_id)
            
            # Get all participants for this gathering
            participants_query = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id,
                status='joined'
            ).all()
            
            participants = []
            for participant in participants_query:
                participant_user = User.query.get(participant.user_id)
                if participant_user:
                    participants.append(participant_user)
            
            # Debug: Print participants
            print(f"Gathering {gathering.id} - {gathering.title} participants:")
            for p in participants:
                print(f"  - User ID: {p.id}, Username: {p.username}")
            
            my_gatherings.append({
                'gathering': gathering,
                'is_host': False,
                'participants_count': participants_count,
                'creator': creator,
                'participants': participants
            })
            
        # Sort by date (most recent first)
        my_gatherings.sort(key=lambda x: x['gathering'].date, reverse=False)
    
    # Fetch gatherings for the "Find Gatherings" tab
    elif current_user.is_authenticated and active_tab == 'find-gatherings':
        # Get all active gatherings
        query = Gathering.query.filter(Gathering.status == 'active')
        
        # Apply basic filters if specified in the URL
        gathering_type = request.args.get('faculty', '')  # Using faculty as gathering_type in original UI
        faculty_filter = request.args.get('course', '')   # Using course as faculty in original UI
        year_semester = request.args.get('yearSemester', '')
        event_date = request.args.get('eventDate', '')
        event_time = request.args.get('eventTime', '')
        location = request.args.get('eventLocation', '')
        
        # Apply gathering type filter
        if gathering_type and gathering_type != 'other':
            query = query.filter(Gathering.gathering_type == gathering_type)
            
        # Apply faculty filter
        if faculty_filter and faculty_filter != 'other':
            # Map from the form values to actual faculty names
            faculty_mapping = {
                'study': 'Faculty of Multimedia',
                'project': 'Faculty of Computing Informatics',
                'social': 'Faculty of Management',
                'sports': 'Faculty of Engineering',
                'gaming': 'Faculty of Applied Communication',
                'other': 'Other'
            }
            
            if faculty_filter in faculty_mapping:
                query = query.filter(Gathering.faculty == faculty_mapping[faculty_filter])
        
        # Apply year/semester filter
        if year_semester:
            query = query.filter(Gathering.year_semester.ilike(f'%{year_semester}%'))
            
        # Apply location filter
        if location:
            query = query.filter(Gathering.location.ilike(f'%{location}%'))
            
        # Apply date filter
        if event_date:
            try:
                date_filter = datetime.strptime(event_date, '%Y-%m-%d').date()
                query = query.filter(Gathering.date == date_filter)
            except ValueError:
                # If date format is invalid, ignore this filter
                pass
                
        # Apply time filter
        if event_time:
            try:
                time_filter = datetime.strptime(event_time, '%H:%M').time()
                query = query.filter(Gathering.time == time_filter)
            except ValueError:
                # If time format is invalid, ignore this filter
                pass
            
        # Execute query and prepare results
        gatherings = query.all()
        
        for gathering in gatherings:
            participants_count = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id, 
                status='joined'
            ).count()
            
            creator = User.query.get(gathering.user_id)
            
            # Get all participants for this gathering
            participants_query = GatheringParticipant.query.filter_by(
                gathering_id=gathering.id,
                status='joined'
            ).all()
            
            participants = []
            for participant in participants_query:
                participant_user = User.query.get(participant.user_id)
                if participant_user:
                    participants.append(participant_user)
            
            # Debug: Print participants
            print(f"Gathering {gathering.id} - {gathering.title} participants:")
            for p in participants:
                print(f"  - User ID: {p.id}, Username: {p.username}")
            
            all_gatherings.append({
                'gathering': gathering,
                'participants_count': participants_count,
                'creator': creator,
                'participants': participants
            })
            
        # Sort by date (soonest first)
        all_gatherings.sort(key=lambda x: x['gathering'].date)
    
    return render_template('jomgather.html', 
                           students=students,
                           connected_partners=connected_partners,
                           faculties=faculties,
                           courses=courses,
                           search_performed=search_performed,
                           active_tab=active_tab,
                           my_gatherings=my_gatherings,
                           all_gatherings=all_gatherings)

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
        if request.accept_mimetypes.accept_json:
            return jsonify({
                'success': False,
                'error': 'You already have a connection with this user'
            })
        else:
            flash('You already have a connection with this user', 'info')
            return redirect(url_for('jomgather'))
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
            if request.accept_mimetypes.accept_json:
                return jsonify({
                    'success': True,
                    'message': 'Connection request sent!'
                })
            else:
                flash('Connection request sent!', 'success')
                return redirect(url_for('jomgather'))
        except Exception as e:
            db.session.rollback()
            if request.accept_mimetypes.accept_json:
                return jsonify({
                    'success': False,
                    'error': f'An error occurred: {str(e)}'
                }), 500
            else:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('jomgather'))

@app.route('/guidelines', endpoint='view_guidelines')
def view_guidelines():
    return render_template('guidelines.html')

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

@app.route('/api/chat/<int:connection_id>/messages')
@login_required
def get_chat_messages(connection_id):
    """API endpoint to get new messages for real-time chat"""
    connection = Connection.query.get_or_404(connection_id)
    
    # Ensure the current user is part of this connection
    if connection.user_id != current_user.id and connection.connected_user_id != current_user.id:
        return {'error': 'Unauthorized'}, 403
    
    # Get the last message timestamp from query parameter
    last_timestamp = request.args.get('last_timestamp')
    
    if last_timestamp:
        try:
            from datetime import datetime
            last_dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            # Get messages newer than the last timestamp
            messages = Message.query.filter(
                Message.connection_id == connection_id,
                Message.created_at > last_dt
            ).order_by(Message.created_at).all()
        except ValueError:
            # If timestamp is invalid, get all messages
            messages = Message.query.filter_by(connection_id=connection_id).order_by(Message.created_at).all()
    else:
        # Get all messages if no timestamp provided
        messages = Message.query.filter_by(connection_id=connection_id).order_by(Message.created_at).all()
    
    # Mark new messages from other user as read
    other_user_id = connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
    unread_messages = Message.query.filter_by(
        connection_id=connection_id,
        sender_id=other_user_id,
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    # Convert messages to JSON format
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender_id,
            'created_at': msg.created_at.isoformat(),
            'is_current_user': msg.sender_id == current_user.id
        })
    
    return {'messages': messages_data}

@app.route('/chat/<int:connection_id>/send', methods=['POST'])
@login_required
def send_message(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Ensure the current user is part of this connection
    if connection.user_id != current_user.id and connection.connected_user_id != current_user.id:
        if is_ajax:
            return {'error': 'You are not authorized to send messages in this chat'}, 403
        flash('You are not authorized to send messages in this chat', 'error')
        return redirect(url_for('view_connections'))
    
    # Ensure the connection is accepted
    if connection.status != 'accepted':
        if is_ajax:
            return {'error': 'This connection has not been accepted yet'}, 400
        flash('This connection has not been accepted yet', 'error')
        return redirect(url_for('view_connections'))
    
    # Get the message content
    content = request.form.get('message', '').strip()
    
    if not content:
        if is_ajax:
            return {'error': 'Message cannot be empty'}, 400
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
    
    # If it's an AJAX request, return JSON response
    if is_ajax:
        return {
            'success': True,
            'message': {
                'id': new_message.id,
                'content': new_message.content,
                'sender_id': new_message.sender_id,
                'created_at': new_message.created_at.isoformat(),
                'is_current_user': True
            }
        }
    
    # Determine which user to redirect to for the chat (for non-AJAX requests)
    other_user_id = connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
    return redirect(url_for('chat', user_id=other_user_id))

@app.route('/create_gathering', methods=['POST'])
@login_required
def create_gathering():
    try:
        # Get form data and print for debugging
        title = request.form.get('eventTitle')
        gathering_type = request.form.get('eventType')
        faculty = request.form.get('facultyFocus')
        year_semester = request.form.get('yearSemester')
        event_date = request.form.get('eventDate')
        event_time = request.form.get('eventTime')
        location = request.form.get('eventLocation')
        max_attendees = request.form.get('maxAttendees')
        description = request.form.get('eventDescription')
        target_audience = request.form.get('targetAudience')
        
        # Log received form data for debugging
        print(f"Form data received:")
        print(f"Title: {title}")
        print(f"Type: {gathering_type}")
        print(f"Faculty: {faculty}")
        print(f"Year/Semester: {year_semester}")
        print(f"Date: {event_date}")
        print(f"Time: {event_time}")
        print(f"eventLocation: {location}")
        print(f"Max Participants: {max_attendees}")
        print(f"Description: {description}")
        print(f"Target Audience: {target_audience}")
        
        # Validate required fields
        if not all([title, gathering_type, faculty, year_semester, event_date, event_time, location, max_attendees, description]):
            missing_fields = []
            if not title: missing_fields.append("Title")
            if not gathering_type: missing_fields.append("Gathering Type")
            if not faculty: missing_fields.append("Faculty")
            if not year_semester: missing_fields.append("Year & Semester")
            if not event_date: missing_fields.append("Date")
            if not event_time: missing_fields.append("Time")
            if not location: missing_fields.append("eventLocation")
            if not max_attendees: missing_fields.append("Maximum Participants")
            if not description: missing_fields.append("Description")
            
            print(f"Missing required fields: {', '.join(missing_fields)}")
            flash(f"Please fill in all required fields: {', '.join(missing_fields)}", 'error')
            return redirect(url_for('jomgather', tab='create-gathering'))
        
        # Parse date and time
        try:
            date = datetime.strptime(event_date, '%Y-%m-%d').date()
            time = datetime.strptime(event_time, '%H:%M').time()
        except ValueError as e:
            print(f"Date/time parsing error: {str(e)}")
            flash('Invalid date or time format', 'error')
            return redirect(url_for('jomgather', tab='create-gathering'))
        
        # Parse max participants
        try:
            max_participants = int(max_attendees)
            if max_participants <= 0:
                raise ValueError("Maximum participants must be greater than 0")
        except ValueError as e:
            print(f"Max participants parsing error: {str(e)}")
            flash('Maximum participants must be a positive number', 'error')
            return redirect(url_for('jomgather', tab='create-gathering'))

        # Create new gathering
        new_gathering = Gathering(
            user_id=current_user.id,
            title=title,
            gathering_type=gathering_type,
            faculty=faculty,
            year_semester=year_semester,
            date=date,
            time=time,
            location=location,
            max_participants=max_participants,
            description=description,
            target_audience=target_audience,
            status='active'
        )

        # Add to database
        db.session.add(new_gathering)
        db.session.commit()

        # Add creator as first participant
        participant = GatheringParticipant.query.filter_by(
            gathering_id=new_gathering.id,
            user_id=current_user.id,
            status='joined'
        ).first()
        
        if not participant:
            participant = GatheringParticipant(
                gathering_id=new_gathering.id,
                user_id=current_user.id,
                status='joined'
            )
            db.session.add(participant)
            db.session.commit()

        flash('Gathering created successfully!', 'success')
        return redirect(url_for('jomgather', tab='my-gatherings'))

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating gathering: {str(e)}")
        print(f"Detailed error: {error_details}")
        db.session.rollback()
        flash(f'Error creating gathering: {str(e)}', 'error')
        return redirect(url_for('jomgather', tab='create-gathering'))

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

        student_id = data.get('student_id')
        new_password = data.get('new_password')

        if not all([student_id, new_password]):
            return jsonify({'success': False, 'error': 'Missing student ID or new password'}), 400

        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'Student ID not found'}), 404

        # Check password strength
        if not validate_password(new_password):
            return jsonify({
                'success': False,
                'error': 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'
            }), 400

        # Check 2FA status
        if user.is_2fa_enabled:
            # Store hashed password in session for verification
            session['pending_password'] = generate_password_hash(new_password)
            session['pending_student_id'] = student_id
            return jsonify({
                'success': False, 
                'require_2fa': True,
                'message': '2FA verification required'
            })

        # No 2FA - update directly and log in
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Password updated successfully!'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Password update failed for {student_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update password. Please try again.'
        }), 500

@app.route('/match')
@login_required
def match():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  # Silent redirect
    
    faculties = db.session.query(Customisation.faculty).filter(Customisation.faculty.isnot(None)).distinct().all()
    return render_template('match.html', faculties=[f[0] for f in faculties if f[0]])

@app.route('/api/match/<match_type>')
@login_required
def match_users(match_type):
    try:
        # Get filtering criteria
        faculty = request.args.get('faculty')
        year = request.args.get('year')
        
        # Basic query
        query = User.query.filter(
            User.id != current_user.id,
            User.is_active == True
        ).join(Customisation)
        
        # Apply filters
        if faculty:
            query = query.filter(Customisation.faculty == faculty)
        if year:
            query = query.filter(Customisation.year_of_study == int(year))
        
        if match_type == 'random':
            # Random match
            available_users = query.all()
            if not available_users:
                return jsonify({'success': False, 'error': 'no match user'})
            
            matched_user = random.choice(available_users)
            return jsonify({
                'success': True,
                'user': format_user(matched_user)
            })
            
        elif match_type == 'smart':
            # Smart match (based on common interests)
            current_interests = set()
            if current_user.customisation and current_user.customisation.interests:
                current_interests = set(current_user.customisation.interests.split(','))
            
            best_match = None
            highest_score = 0
            
            for user in query.all():
                user_interests = set()
                if user.customisation and user.customisation.interests:
                    user_interests = set(user.customisation.interests.split(','))
                
                # Calculate match score
                common_interests = current_interests & user_interests
                score = len(common_interests)
                
                # Extra points for same faculty
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
    """format user data"""
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

@app.route('/join_gathering/<int:gathering_id>', methods=['POST'])
@login_required
def join_gathering(gathering_id):
    try:
        # Check if the gathering exists
        gathering = Gathering.query.get_or_404(gathering_id)
        
        # Check if the gathering is still active
        if gathering.status != 'active':
            flash('This gathering is no longer active', 'error')
            return redirect(url_for('jomgather', tab='find-gatherings'))
        
        # Check if the user is already a participant
        existing_participant = GatheringParticipant.query.filter_by(
            gathering_id=gathering_id,
            user_id=current_user.id
        ).first()
        
        if existing_participant:
            flash('You are already a participant in this gathering', 'info')
            return redirect(url_for('jomgather', tab='my-gatherings'))
            
        # Check if the gathering is full
        participants_count = GatheringParticipant.query.filter_by(
            gathering_id=gathering_id,
            status='joined'
        ).count()
        
        if participants_count >= gathering.max_participants:
            flash('This gathering is already full', 'error')
            return redirect(url_for('jomgather', tab='find-gatherings'))
            
        # Add the user as a participant
        new_participant = GatheringParticipant(
            gathering_id=gathering_id,
            user_id=current_user.id,
            status='joined'
        )
        
        db.session.add(new_participant)
        db.session.commit()
        
        flash('You have successfully joined the gathering!', 'success')
        return redirect(url_for('jomgather', tab='my-gatherings'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error joining gathering: {str(e)}', 'error')
        return redirect(url_for('jomgather', tab='find-gatherings'))

@app.route('/edit_gathering/<int:gathering_id>', methods=['GET', 'POST'])
@login_required
def edit_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    
    # Check if the current user is the creator of this gathering
    if gathering.user_id != current_user.id:
        flash('You can only edit gatherings you created', 'error')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    if request.method == 'POST':
        try:
            # Update gathering details
            gathering.title = request.form.get('eventTitle')
            gathering.gathering_type = request.form.get('eventType')
            gathering.faculty = request.form.get('facultyFocus')
            gathering.year_semester = request.form.get('yearSemester')
            
            event_date = request.form.get('eventDate')
            event_time = request.form.get('eventTime')
            
            # Parse date and time
            if event_date:
                gathering.date = datetime.strptime(event_date, '%Y-%m-%d').date()
            if event_time:
                gathering.time = datetime.strptime(event_time, '%H:%M').time()
                
            gathering.location = request.form.get('eventLocation')
            
            max_attendees = request.form.get('maxAttendees')
            if max_attendees and max_attendees.isdigit():
                max_participants = int(max_attendees)
                # Check if new max is less than current participants
                current_participants = GatheringParticipant.query.filter_by(
                    gathering_id=gathering_id, 
                    status='joined'
                ).count()
                
                if max_participants < current_participants:
                    flash(f'Cannot reduce maximum participants below current count ({current_participants})', 'error')
                    return redirect(url_for('edit_gathering', gathering_id=gathering_id))
                    
                gathering.max_participants = max_participants
                
            gathering.description = request.form.get('eventDescription')
            gathering.target_audience = request.form.get('targetAudience')
            
            db.session.commit()
            flash('Gathering updated successfully!', 'success')
            return redirect(url_for('jomgather', tab='my-gatherings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating gathering: {str(e)}', 'error')
    
    # Pre-fill the form with current gathering data
    return render_template('edit_gathering.html', gathering=gathering)

@app.route('/cancel_gathering/<int:gathering_id>', methods=['POST'])
@login_required
def cancel_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    
    # Check if the current user is the creator of this gathering
    if gathering.user_id != current_user.id:
        flash('You can only cancel gatherings you created', 'error')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    try:
        # Update the status to canceled
        gathering.status = 'canceled'
        db.session.commit()
        flash('Gathering has been canceled', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error canceling gathering: {str(e)}', 'error')
        
    return redirect(url_for('jomgather', tab='my-gatherings'))

@app.route('/leave_gathering/<int:gathering_id>', methods=['POST'])
@login_required
def leave_gathering(gathering_id):
    # Check if the user is a participant
    participant = GatheringParticipant.query.filter_by(
        gathering_id=gathering_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        flash('You are not a participant in this gathering', 'error')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    # Check if the user is the creator
    gathering = Gathering.query.get(gathering_id)
    if gathering.user_id == current_user.id:
        flash('As the creator, you cannot leave your own gathering. You can cancel it instead.', 'error')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    try:
        # Remove the participant
        db.session.delete(participant)
        db.session.commit()
        flash('You have left the gathering', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error leaving gathering: {str(e)}', 'error')
        
    return redirect(url_for('jomgather', tab='my-gatherings'))

@app.route('/message_gathering/<int:gathering_id>', methods=['GET', 'POST'])
@login_required
def message_gathering(gathering_id):
    # Check if the gathering exists
    gathering = Gathering.query.get_or_404(gathering_id)
    
    # Check if user is a participant or creator
    is_participant = False
    
    # Check if user created the gathering
    if gathering.user_id == current_user.id:
        is_participant = True
    else:
        # Check if user is a participant
        participant = GatheringParticipant.query.filter_by(
            gathering_id=gathering_id,
            user_id=current_user.id
        ).first()
        
        if participant:
            is_participant = True
    
    if not is_participant:
        flash('You must be a participant to message this gathering', 'error')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    # Handle POST request for sending a message
    if request.method == 'POST':
        message_content = request.form.get('message')
        if message_content and message_content.strip():
            # Create a new message
            new_message = GatheringMessage(
                gathering_id=gathering_id,
                user_id=current_user.id,
                content=message_content.strip()
            )
            db.session.add(new_message)
            db.session.commit()
            
            flash('Message sent!', 'success')
        
        # Redirect to avoid form resubmission
        return redirect(url_for('message_gathering', gathering_id=gathering_id))
    
    # Get all participants for this gathering
    participants = GatheringParticipant.query.filter_by(
        gathering_id=gathering_id,
        status='joined'
    ).all()
    
    participant_users = []
    for p in participants:
        user = User.query.get(p.user_id)
        if user:
            participant_users.append(user)
    
    # Also add the gathering creator if not already in the list
    creator = User.query.get(gathering.user_id)
    if creator and creator not in participant_users:
        participant_users.append(creator)
    
    # Get all messages for this gathering
    messages = GatheringMessage.query.filter_by(
        gathering_id=gathering_id
    ).order_by(GatheringMessage.created_at).all()
    
    # For now, render a simple chat interface for the gathering
    return render_template('gathering_chat.html', 
                          gathering=gathering, 
                          participants=participant_users,
                          messages=messages,
                          current_user=current_user)


@app.route('/2fa', methods=['GET', 'POST'])
def two_factor_auth():
    source = request.args.get('source')
    
    # Handle password reset case
    if source == 'reset':
        student_id = session.get('pending_student_id')
        if not student_id:
            flash("Session expired. Please try again.", "error")
            return redirect(url_for('pass_page'))
            
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            flash("User not found", "error")
            return redirect(url_for('pass_page'))
            
        if request.method == 'POST':
            otp = request.form.get('otp', '').strip()
            
            if not otp or len(otp) != 6 or not otp.isdigit():
                flash("Invalid OTP format. Must be 6 digits.", "error")
                return redirect(request.url)
            
            totp = pyotp.TOTP(user.two_fa_secret)
            if totp.verify(otp, valid_window=1):
                # Update password from session storage
                new_password_hash = session.pop('pending_password', None)
                student_id = session.pop('pending_student_id', None)
                
                if new_password_hash and student_id:
                    user.password_hash = new_password_hash
                    db.session.commit()
                    
                    # Log the user in automatically
                    login_user(user)
                    flash("Password updated successfully! You have been logged in.", "success")
                    return redirect(url_for('customise'))
                else:
                    flash("Password reset session expired", "error")
                    return redirect(url_for('pass_page'))
            else:
                flash("Incorrect OTP. Please try again.", "error")
                return redirect(request.url)
                
        return render_template('2fa.html', source=source, user=user)
    
    # Handle 2FA enable case from customise
    elif source == 'customise':
        user_id = session.get('2fa_user_id')
        if not user_id:
            flash("Session expired. Please try again.", "error")
            return redirect(url_for('customise'))
            
        user = User.query.get(user_id)
        
        if request.method == 'GET':
            if not user.two_fa_secret:
                flash("2FA setup error. Please try again.", "error")
                return redirect(url_for('customise'))
                
            otp_uri = pyotp.TOTP(user.two_fa_secret).provisioning_uri(
                name=user.email or user.username,
                issuer_name="JomGather"
            )
            qr_url = f'https://api.qrserver.com/v1/create-qr-code/?data={otp_uri}&size=200x200'
            
            return render_template('2fa.html', source=source, qr_url=qr_url, user=user)
        
        elif request.method == 'POST':
            user.is_2fa_enabled = True
            db.session.commit()
            session.pop('2fa_user_id', None)
            flash("Two-Factor Authentication has been successfully enabled!", "success")
            return redirect(url_for('customise'))
    
    return redirect(url_for('customise'))


@app.route('/toggle-2fa', methods=['POST'])
@login_required
def toggle_2fa():
    action = request.form.get('action')
    user = current_user

    if action == 'enable':
        # 生成2FA密钥(如果不存在)
        if not user.two_fa_secret:
            user.two_fa_secret = pyotp.random_base32()
            db.session.commit()
        
        # 存储用户ID在session中供2FA页面使用
        session['2fa_user_id'] = user.id
        session['2fa_source'] = 'customise'
        
        return redirect(url_for('two_factor_auth', source='customise'))
    
    elif action == 'disable':
        user.is_2fa_enabled = False
        db.session.commit()
        flash("2FA has been disabled.", "success")
        return redirect(url_for('customise'))
    
    flash("Invalid action", "error")
    return redirect(url_for('customise'))

# Run the app if this file is executed
if __name__ == '__main__':
    with app.app_context():
        # Check if tables need to be created
        db.create_all()

        from models import User
        for user in User.query.all():
            if user.is_2fa_enabled is None:
                print(f"Fixing user: {user.username}")
                user.is_2fa_enabled = False
        db.session.commit()
        print("✔ All users patched: null is_2fa_enabled → False")

        print("Database tables created or confirmed to exist.")
        print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # List the tables that were created
        print(f"Tables created: {', '.join(db.metadata.tables.keys())}")
    app.run(debug=True, use_reloader=True, host='0.0.0.0')


@app.route('/api/check-2fa/<student_id>')
def check_2fa_status(student_id):
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'require_2fa': False})

    is_verified = session.get('2fa_verified_for') == student_id
    return jsonify({'require_2fa': user.is_2fa_enabled, 'verified': is_verified})


@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.create_all()

app.cli.add_command(create_tables)

# This should be the last thing in the file
# This should be the last thing in the file
#print(app.url_map)

@app.route('/pre-check-2fa', methods=['POST'])
def pre_check_2fa():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        new_password = data.get('new_password')
        
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # 暂存新密码到session(加密)
        session['pending_password'] = generate_password_hash(new_password)
        session['pending_user_id'] = user.id
        
        if user.is_2fa_enabled:
            return jsonify({
                'success': True,
                'require_2fa': True,
                'message': '2FA verification required'
            })
        
        # 无2FA直接更新密码
        user.password_hash = session['pending_password']
        db.session.commit()
        login_user(user)  # 自动登录
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    # test sftp

