from flask import Flask, redirect, url_for, render_template, request, flash, session
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin
from extensions import db, init_extensions
from config import Config
from models import User, Gathering, GatheringParticipant, Customisation, Message, Connection
import os
import re
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime

# Create a Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

# Initialize login manager before other extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Initialize other extensions after login manager
init_extensions(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        
        # Debug information
        print(f"Received POST data: bio={bio[:20]}..., interests={interests[:50]}...")
        print(f"Faculty: {faculty}, Course: {course}, Year: {year_of_study}")
        print(f"Profile picture: {profile_picture.filename if profile_picture else 'None'}")
        
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
            # Always redirect to customise after successful login
            return redirect(url_for('customise'))
        else:
            flash('Invalid student ID or password', 'error')
            return redirect(url_for('login'))
            
    return render_template('register.html')

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
@login_required
def jomgather():
    active_tab = request.args.get('tab', 'find-partners')
    search_performed = False
    students = []
    connected_partners = []
    
    # Fetch gatherings for My Gatherings tab
    my_hosted_gatherings = Gathering.query.filter_by(user_id=current_user.id).all()
    
    # Fetch gatherings user is participating in
    my_joined_gatherings = Gathering.query\
        .join(GatheringParticipant)\
        .filter(
            GatheringParticipant.user_id == current_user.id,
            GatheringParticipant.status == 'joined'
        ).all()

    # Fetch all available gatherings for Find Gatherings tab
    available_gatherings = Gathering.query.filter(
        Gathering.user_id != current_user.id,
        ~Gathering.id.in_([g.id for g in my_joined_gatherings])  # Exclude joined gatherings
    ).all()

    return render_template('jomgather.html',
                         students=students,
                         connected_partners=connected_partners,
                         active_tab=active_tab,
                         my_hosted_gatherings=my_hosted_gatherings,
                         my_joined_gatherings=my_joined_gatherings,
                         available_gatherings=available_gatherings)

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

@app.route('/create-gathering', methods=['POST'])
@login_required
def create_gathering():
    if request.method == 'POST':
        try:
            # Get form data
            new_gathering = Gathering(
                user_id=current_user.id,
                title=request.form.get('eventTitle'),
                gathering_type=request.form.get('eventType'),
                faculty=request.form.get('faculty'),
                year_semester=request.form.get('yearSemester'),
                date=datetime.strptime(request.form.get('eventDate'), '%Y-%m-%d').date(),
                time=datetime.strptime(request.form.get('eventTime'), '%H:%M').time(),
                location=request.form.get('eventLocation'),
                max_participants=int(request.form.get('maxAttendees')),
                description=request.form.get('eventDescription'),
                target_audience=request.form.get('targetAudience'),
                status='pending'
            )

            db.session.add(new_gathering)
            db.session.commit()

            flash('Gathering created successfully!', 'success')
            return redirect(url_for('jomgather', tab='my-gatherings'))

        except Exception as e:
            db.session.rollback()
            flash('Error creating gathering. Please try again.', 'error')
            print(f"Error: {str(e)}")
            return redirect(url_for('jomgather', tab='create-gathering'))

    return redirect(url_for('jomgather', tab='create-gathering'))

@app.route('/join-gathering/<int:gathering_id>', methods=['POST'])
@login_required
def join_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    
    if gathering.user_id == current_user.id:
        flash('You cannot join your own gathering!', 'error')
        return redirect(url_for('jomgather', tab='find-gatherings'))
        
    # Check if already joined
    existing_participant = GatheringParticipant.query.filter_by(
        gathering_id=gathering_id,
        user_id=current_user.id
    ).first()
    
    if existing_participant:
        flash('You have already joined this gathering!', 'info')
        return redirect(url_for('jomgather', tab='my-gatherings'))
    
    # Create new participant entry
    new_participant = GatheringParticipant(
        gathering_id=gathering_id,
        user_id=current_user.id
    )
    
    try:
        db.session.add(new_participant)
        db.session.commit()
        flash('Successfully joined the gathering!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error joining gathering!', 'error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('jomgather', tab='my-gatherings'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

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
