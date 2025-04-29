from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jomgather.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100))
    program = db.Column(db.String(100))
    year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    profile_created = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    events_created = db.relationship('Event', backref='organizer', lazy='dynamic')
    gatherings_created = db.relationship('Gathering', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Academic Interests
    academic_interests = db.Column(db.Text)  # Comma-separated values
    
    # Study Preferences
    study_preferences = db.Column(db.Text)  # Comma-separated values
    
    # Sports & Fitness
    sports_interests = db.Column(db.Text)  # Comma-separated values
    
    # Arts & Entertainment
    arts_interests = db.Column(db.Text)  # Comma-separated values
    
    # Social Activities
    social_interests = db.Column(db.Text)  # Comma-separated values
    
    # Other Hobbies
    other_hobbies = db.Column(db.Text)  # Comma-separated values
    
    # Connection Purposes
    connection_purposes = db.Column(db.Text)  # Comma-separated values
    
    def get_all_interests(self):
        interests = []
        if self.academic_interests:
            interests.extend(self.academic_interests.split(','))
        if self.study_preferences:
            interests.extend(self.study_preferences.split(','))
        if self.sports_interests:
            interests.extend(self.sports_interests.split(','))
        if self.arts_interests:
            interests.extend(self.arts_interests.split(','))
        if self.social_interests:
            interests.extend(self.social_interests.split(','))
        if self.other_hobbies:
            interests.extend(self.other_hobbies.split(','))
        return [interest.strip() for interest in interests]

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendees = db.relationship('EventAttendee', backref='event', lazy='dynamic')
    
    def get_attendee_count(self):
        return self.attendees.count()

class EventAttendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Gathering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    gathering_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    participants = db.relationship('GatheringParticipant', backref='gathering', lazy='dynamic')
    
    def get_participant_count(self):
        return self.participants.count()

class GatheringParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gathering_id = db.Column(db.Integer, db.ForeignKey('gathering.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Flask-Login setup
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home2.html')

@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        student_id = request.form.get('student-id')
        email = request.form.get('signup-email')
        password = request.form.get('signup-password')
        confirm_password = request.form.get('confirm-password')
        
        # Form validation
        if not all([full_name, student_id, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register_page'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register_page'))
            
        # Check if user already exists
        existing_user = User.query.filter((User.email == email) | (User.student_id == student_id)).first()
        if existing_user:
            flash('Email or student ID already in use', 'danger')
            return redirect(url_for('register_page'))
            
        # Create new user
        new_user = User(
            full_name=full_name,
            student_id=student_id,
            email=email
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('register_page'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            print(e)
            return redirect(url_for('register_page'))
    
    return redirect(url_for('register_page'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email_or_id = request.form.get('login-email')
        password = request.form.get('login-password')
        remember_me = True if request.form.get('remember-me') else False
        
        # Find user by email or student ID
        user = User.query.filter((User.email == email_or_id) | (User.student_id == email_or_id)).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('home')
            flash('Logged in successfully!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email/student ID or password', 'danger')
            return redirect(url_for('register_page'))
    
    return redirect(url_for('register_page'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/customise.html')
@login_required
def customize_profile():
    return render_template('customise.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        # Update user basic info
        current_user.faculty = request.form.get('faculty')
        current_user.program = request.form.get('program')
        current_user.year = request.form.get('year')
        current_user.bio = request.form.get('bio')
        
        # Check if profile exists, create if not
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)
        
        # Update profile interests
        profile.academic_interests = request.form.get('academic-interests')
        profile.study_preferences = request.form.get('study-preferences')
        profile.sports_interests = request.form.get('sports-interests')
        profile.arts_interests = request.form.get('arts-interests')
        profile.social_interests = request.form.get('social-interests')
        profile.other_hobbies = request.form.get('other-hobbies')
        profile.connection_purposes = request.form.get('connection-purposes')
        
        # Mark profile as created
        current_user.profile_created = True
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            print(e)
        
        return redirect(url_for('customize_profile'))

@app.route('/jomgather.html')
def jomgather_page():
    return render_template('jomgather.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    faculty = request.args.get('faculty')
    program = request.args.get('program')
    interest = request.args.get('interest')
    purpose = request.args.get('purpose')
    
    # Start with all users who have profiles
    query = User.query.filter_by(profile_created=True)
    
    # Apply filters if provided
    if faculty:
        query = query.filter_by(faculty=faculty)
    
    if program:
        query = query.filter_by(program=program)
    
    # Get all matching users
    users = query.all()
    
    # Further filter by interest and purpose
    if interest or purpose:
        filtered_users = []
        for user in users:
            if user.profile:
                # Filter by interest
                if interest:
                    interests = user.profile.get_all_interests()
                    if not any(interest.lower() in i.lower() for i in interests):
                        continue
                
                # Filter by purpose
                if purpose and user.profile.connection_purposes:
                    purposes = [p.strip() for p in user.profile.connection_purposes.split(',')]
                    if not any(purpose.lower() in p.lower() for p in purposes):
                        continue
                
                filtered_users.append(user)
        users = filtered_users
    
    # Format results
    result = []
    for user in users:
        if user.profile:
            interests = user.profile.get_all_interests()[:3]  # Get top 3 interests
            result.append({
                'id': user.id,
                'name': user.full_name,
                'program': f"{user.program}, Year {user.year}" if user.program and user.year else "",
                'interests': interests,
                'bio': user.bio or ""
            })
    
    return jsonify(result)

@app.route('/api/events', methods=['GET'])
def get_events():
    event_type = request.args.get('event_type')
    date = request.args.get('date')
    location = request.args.get('location')
    
    # Start with all events
    query = Event.query
    
    # Apply filters if provided
    if event_type:
        query = query.filter_by(event_type=event_type)
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter_by(date=filter_date)
        except ValueError:
            pass
    
    if location:
        query = query.filter_by(location=location)
    
    # Order by date (upcoming first)
    query = query.order_by(Event.date.asc(), Event.start_time.asc())
    
    events = query.all()
    
    # Format results
    result = []
    for event in events:
        organizer = User.query.get(event.organizer_id)
        result.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date.strftime('%B %d, %Y'),
            'time': f"{event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}",
            'location': event.location,
            'attending': event.get_attendee_count(),
            'organizer': organizer.full_name if organizer else "Unknown"
        })
    
    return jsonify(result)

@app.route('/create_event', methods=['POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('event-title')
        description = request.form.get('event-description')
        event_type = request.form.get('event-type')
        date_str = request.form.get('event-date')
        start_time_str = request.form.get('event-start-time')
        end_time_str = request.form.get('event-end-time')
        location = request.form.get('event-location')
        capacity = request.form.get('event-capacity')
        
        try:
            # Parse date and time
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            new_event = Event(
                title=title,
                description=description,
                event_type=event_type,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                capacity=int(capacity) if capacity else None,
                organizer_id=current_user.id
            )
            
            db.session.add(new_event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            print(e)
        
        return redirect(url_for('jomgather_page'))

@app.route('/create_gathering', methods=['POST'])
@login_required
def create_gathering():
    if request.method == 'POST':
        title = request.form.get('gathering-title')
        description = request.form.get('gathering-description')
        gathering_type = request.form.get('gathering-type')
        date_str = request.form.get('gathering-date')
        start_time_str = request.form.get('gathering-start-time')
        end_time_str = request.form.get('gathering-end-time')
        location = request.form.get('gathering-location')
        capacity = request.form.get('gathering-capacity')
        
        try:
            # Parse date and time
            gathering_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            new_gathering = Gathering(
                title=title,
                description=description,
                gathering_type=gathering_type,
                date=gathering_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                capacity=int(capacity) if capacity else None,
                creator_id=current_user.id
            )
            
            db.session.add(new_gathering)
            db.session.commit()
            flash('Gathering created successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            print(e)
        
        return redirect(url_for('jomgather_page'))

@app.route('/attend_event/<int:event_id>', methods=['POST'])
@login_required
def attend_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if already attending
    existing = EventAttendee.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already registered for this event', 'info')
        return redirect(url_for('jomgather_page'))
    
    # Check capacity
    if event.capacity and event.get_attendee_count() >= event.capacity:
        flash('This event is at full capacity', 'danger')
        return redirect(url_for('jomgather_page'))
    
    attendee = EventAttendee(
        event_id=event_id,
        user_id=current_user.id
    )
    
    try:
        db.session.add(attendee)
        db.session.commit()
        flash('You are now attending this event!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(e)
    
    return redirect(url_for('jomgather_page'))

@app.route('/join_gathering/<int:gathering_id>', methods=['POST'])
@login_required
def join_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    
    # Check if already joined
    existing = GatheringParticipant.query.filter_by(
        gathering_id=gathering_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already participating in this gathering', 'info')
        return redirect(url_for('jomgather_page'))
    
    # Check capacity
    if gathering.capacity and gathering.get_participant_count() >= gathering.capacity:
        flash('This gathering is at full capacity', 'danger')
        return redirect(url_for('jomgather_page'))
    
    participant = GatheringParticipant(
        gathering_id=gathering_id,
        user_id=current_user.id
    )
    
    try:
        db.session.add(participant)
        db.session.commit()
        flash('You have joined this gathering!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(e)
    
    return redirect(url_for('jomgather_page'))

@app.route('/connect/<int:user_id>', methods=['POST'])
@login_required
def connect_with_user(user_id):
    if user_id == current_user.id:
        flash('You cannot connect with yourself', 'danger')
        return redirect(url_for('jomgather_page'))
    
    # Check if connection already exists
    existing = Connection.query.filter(
        ((Connection.requester_id == current_user.id) & (Connection.recipient_id == user_id)) |
        ((Connection.requester_id == user_id) & (Connection.recipient_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == 'pending':
            flash('Connection request already sent', 'info')
        elif existing.status == 'accepted':
            flash('You are already connected with this user', 'info')
        elif existing.status == 'rejected':
            flash('Connection request was previously rejected', 'info')
        return redirect(url_for('jomgather_page'))
    
    connection = Connection(
        requester_id=current_user.id,
        recipient_id=user_id,
        status='pending'
    )
    
    try:
        db.session.add(connection)
        db.session.commit()
        flash('Connection request sent!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(e)
    
    return redirect(url_for('jomgather_page'))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    content = request.form.get('message_content')
    
    if not recipient_id or not content:
        flash('Message and recipient are required', 'danger')
        return redirect(url_for('jomgather_page'))
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=int(recipient_id),
        content=content
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(e)
    
    return redirect(url_for('jomgather_page'))

@app.route('/my_connections')
@login_required
def my_connections():
    # Get accepted connections
    connections = Connection.query.filter(
        (((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id)) &
         (Connection.status == 'accepted'))
    ).all()
    
    connection_users = []
    for conn in connections:
        other_id = conn.recipient_id if conn.requester_id == current_user.id else conn.requester_id
        user = User.query.get(other_id)
        if user:
            connection_users.append(user)
    
    return render_template('my_connections.html', connections=connection_users)

@app.route('/connection_requests')
@login_required
def connection_requests():
    # Get pending connection requests received
    requests = Connection.query.filter_by(
        recipient_id=current_user.id,
        status='pending'
    ).all()
    
    request_users = []
    for req in requests:
        user = User.query.get(req.requester_id)
        if user:
            request_users.append({
                'user': user,
                'connection_id': req.id
            })
    
    return render_template('connection_requests.html', requests=request_users)

@app.route('/respond_to_connection/<int:connection_id>/<string:action>', methods=['POST'])
@login_required
def respond_to_connection(connection_id, action):
    connection = Connection.query.get_or_404(connection_id)
    
    # Verify current user is the recipient
    if connection.recipient_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('connection_requests'))
    
    if action == 'accept':
        connection.status = 'accepted'
        flash('Connection accepted!', 'success')
    elif action == 'reject':
        connection.status = 'rejected'
        flash('Connection rejected', 'info')
    else:
        flash('Invalid action', 'danger')
        return redirect(url_for('connection_requests'))
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(e)
    
    return redirect(url_for('connection_requests'))

@app.route('/my_messages')
@login_required
def my_messages():
    # Get all messages for current user
    received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Mark received messages as read
    for msg in received_messages:
        if not msg.read:
            msg.read = True
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    return render_template(
        'my_messages.html', 
        received_messages=received_messages,
        sent_messages=sent_messages
    )

@app.route('/my_events')
@login_required
def my_events():
    # Events user is attending
    attending = EventAttendee.query.filter_by(user_id=current_user.id).all()
    attending_events = [Event.query.get(a.event_id) for a in attending]
    attending_events = [e for e in attending_events if e is not None]
    
    # Events user has created
    created_events = Event.query.filter_by(organizer_id=current_user.id).all()
    
    return render_template(
        'my_events.html',
        attending_events=attending_events,
        created_events=created_events
    )

@app.route('/my_gatherings')
@login_required
def my_gatherings():
    # Gatherings user is participating in
    participating = GatheringParticipant.query.filter_by(user_id=current_user.id).all()
    participating_gatherings = [Gathering.query.get(p.gathering_id) for p in participating]
    participating_gatherings = [g for g in participating_gatherings if g is not None]
    
    # Gatherings user has created
    created_gatherings = Gathering.query.filter_by(creator_id=current_user.id).all()
    
    return render_template(
        'my_gatherings.html',
        participating_gatherings=participating_gatherings,
        created_gatherings=created_gatherings
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)