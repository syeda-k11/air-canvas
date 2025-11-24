import cv2
import numpy as np
import mediapipe as mp
import base64
from flask import Flask, render_template, Response, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from utils.gesture_utils import GestureRecognizer
from utils.canvas_utils import Canvas

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aircanvas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Add base64 filter to Jinja2
@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    drawings = db.relationship('Drawing', backref='user', lazy=True)

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Initialize canvas and gesture recognizer
canvas = Canvas()
gesture_recognizer = GestureRecognizer()
cap = None

def generate_frames():
    global cap
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame with MediaPipe Hands
        results = hands.process(rgb_frame)
        
        # Clear canvas if gesture detected
        if gesture_recognizer.is_clear_canvas_gesture(results, h, w):
            canvas.clear()
        
        # Check for color change gesture
        new_color = gesture_recognizer.get_color_change_gesture(results, h, w)
        if new_color:
            canvas.change_color(new_color)
        
        # Check for eraser mode
        if gesture_recognizer.is_eraser_gesture(results, h, w):
            canvas.set_eraser(True)
        else:
            canvas.set_eraser(False)
        
        # Draw on canvas if index finger is up
        if gesture_recognizer.is_drawing_gesture(results, h, w):
            landmarks = results.multi_hand_landmarks[0].landmark
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            canvas.add_point((int(index_tip.x * w), int(index_tip.y * h)))
        
        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        # Overlay canvas on frame
        canvas_overlay = canvas.get_canvas_overlay(h, w)
        frame = cv2.addWeighted(frame, 0.7, canvas_overlay, 0.3, 0)
        
        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('canvas_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('canvas_page'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('canvas_page'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('canvas_page'))
        
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    global cap
    if cap:
        cap.release()
        cap = None
    session.clear()
    return redirect(url_for('login'))

@app.route('/canvas')
@login_required
def canvas_page():
    canvas.clear()
    return render_template('canvas.html', username=session.get('user_name'))

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/save_drawing', methods=['POST'])
@login_required
def save_drawing():
    # Get the current canvas image
    canvas_img = canvas.get_canvas_overlay(480, 640)
    _, img_encoded = cv2.imencode('.png', canvas_img)
    
    # Save to database
    new_drawing = Drawing(
        user_id=session['user_id'],
        image_data=img_encoded.tobytes()
    )
    db.session.add(new_drawing)
    db.session.commit()
    
    return '', 204

@app.route('/drawings')
@login_required
def get_drawings():
    drawings = Drawing.query.filter_by(user_id=session['user_id']).order_by(Drawing.timestamp.desc()).all()
    return render_template('drawings.html', drawings=drawings)

@app.route('/download/<int:drawing_id>')
@login_required
def download_drawing(drawing_id):
    drawing = Drawing.query.get_or_404(drawing_id)
    if drawing.user_id != session['user_id']:
        return redirect(url_for('login'))
    
    return Response(
        drawing.image_data,
        mimetype='image/png',
        headers={'Content-Disposition': f'attachment;filename=drawing_{drawing_id}.png'}
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)