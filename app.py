from flask import Flask, redirect, url_for, render_template, request, flash, session
from extensions import db
from config import Config
import os

# Create a Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import models after db is initialized
from models import User

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect')
def connect():
    return render_template('connect.html')

@app.route('/customise')
def customise():
    return render_template('customise.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        student_id = request.form.get('student_id')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password or not student_id:
            flash('All fields are required', 'error')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
            
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
            
        if User.query.filter_by(student_id=student_id).first():
            flash('Student ID already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, student_id=student_id)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration', 'error')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(student_id=student_id, email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid student ID, email, or password', 'error')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/jomgather')
def jomgather():
    return render_template('jomgather.html')

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
        db.create_all()  # Create database tables
    app.run(debug=True)
    