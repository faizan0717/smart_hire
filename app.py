from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import cv2
import moviepy.editor as mp
import speech_recognition as sr
import pyaudio
import wave
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    questions = db.relationship('QuestionAnswer', backref='employer', lazy=True)

class QuestionAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class QuestionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)  # Assuming the user's name is stored here
    employer_id = db.Column(db.Integer, nullable=False)  # Storing employer ID
    sentiment_result = db.Column(db.Text, nullable=False)  # Storing the sentiment result as a text field
    question = db.Column(db.Text,nullable=False)
    number_of_people = db.Column(db.Integer,nullable=False)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['type']

        user = User.query.filter_by(username=username, password=password, type=user_type).first()
        print(user)
        if user:
            session['username'] = user.username
            session['type'] = user.type
            print(session['type'])
            return redirect(url_for('profile'))
        else:
            print("invalid")
            return render_template('login.html', error='Invalid username, password, or user type')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['type']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template('register.html', error='Username already exists')
        else:
            new_user = User(username=username, password=password, type=user_type)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            session['type'] = user_type
            return redirect(url_for('profile'))

    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if session['type'] == 'employee':
            return render_template('employee.html', username=session['username'], type=session['type'])
        elif session['type'] == 'employer':
            questions_answers = QuestionAnswer.query.filter_by(employer_id=user.id).all()
            return render_template('employer.html', username=session['username'], type=session['type'], questions_answers=questions_answers)
    return redirect(url_for('login'))

@app.route('/delete-question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'username' in session and session['type'] == 'employer':
        question = QuestionAnswer.query.get(question_id)
        if question:
            db.session.delete(question)
            db.session.commit()
    return redirect(url_for('profile'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('type', None)
    return redirect(url_for('index'))

@app.route('/employers')
def list_employers():
    if 'username' in session and session['type'] == 'employee':
        employers = User.query.filter_by(type='employer').all()
        return render_template('employers.html', username=session['username'], employers=employers)
    return redirect(url_for('login'))

@app.route('/show-questions/<int:employer_id>')
def show_questions(employer_id):
    if 'username' in session and session['type'] == 'employee':
        employer = User.query.filter_by(id=employer_id, type='employer').first()
        if employer:
            questions_answers = QuestionAnswer.query.filter_by(employer=employer).all()
            return render_template('show_questions.html', username=session['username'], employer_name=employer.username, questions_answers=questions_answers)
    return redirect(url_for('login'))

@app.route('/start-question/<int:question_id>', methods=['GET', 'POST'])
def start_question(question_id):
    if 'username' in session and session['type'] == 'employee':
        if request.method == 'POST':
            # Handle form submission
            return redirect(url_for('profile'))  # Redirect to profile after submitting answer
        else:
            question_answer = QuestionAnswer.query.get(question_id)
            if question_answer:
                return render_template('start_question.html', username=session['username'], question=question_answer.question)
    return redirect(url_for('login'))


@app.route('/start_questioning/<int:question_id>', methods=['POST'])
def handle_ajax_request(question_id):
    if 'username' in session and session['type'] == 'employee':
        question = QuestionAnswer.query.get(question_id)
        
        if question:
            employer_id = question.employer_id
            file_name = "recorded_video.avi"
            record_video_with_audio(file_name)
            transcription = video_to_text("extracted_audio.wav")
            number_of_people = count_people_in_video(file_name)
            print(number_of_people)
            if transcription:
                sentiment_result = analyze_sentiment(transcription)
                new_result = QuestionResult(user_name=session['username'], employer_id=employer_id, sentiment_result=json.dumps(sentiment_result),question=question.question,number_of_people=number_of_people)
                db.session.add(new_result)
                db.session.commit()
                
            return 'Function called successfully', 200
        else:
            return 'Question not found', 404
    else:
        return 'Unauthorized', 401

def count_people_in_video(video_path):
    try:
        # Load the pre-trained Haar Cascade classifier for pedestrian detection
        pedestrian_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
        print(pedestrian_cascade)
        # Load the video
        cap = cv2.VideoCapture(video_path)

        # Initialize variables
        total_people = 0

        # Loop through frames in the video
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect pedestrians in the frame
            pedestrians = pedestrian_cascade.detectMultiScale(gray, 1.1, 4)

            # Draw rectangles around detected pedestrians and count them
            for (x, y, w, h) in pedestrians:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                total_people += 1

        # Release video capture and close all windows
        cap.release()
        cv2.destroyAllWindows()

        # Return the total number of people detected
        return total_people

    except Exception as e:
        print("should not come here")
        print("Error:", e)
        return 0

@app.route('/view_employye_results/<int:employer_id>', methods=['POST'])
def view_employye_results(employer_id):
    results = QuestionResult.query.filter_by(employer_id=employer_id).all()
    
    # Group the results by user name
    results_by_user = {}
    for result in results:
        if result.user_name not in results_by_user : results_by_user.setdefault(result.user_name,[])
        results_by_user[result.user_name].append(result)
        print(result.number_of_people)
    return render_template('view_results.html', results_by_user=results_by_user)


def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(text)

    return sentiment_scores

def video_to_text(audio_path):
    try:
        # Extract audio from video
       

        # Write audio to a temporary file
        audio_temp_path = audio_path
        # audio_clip.write_audiofile(audio_temp_path)

        # Perform speech recognition on the audio
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_temp_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        return text
    except Exception as e:
        return f"Error: {str(e)}"

def record_video_with_audio(file_name, duration=10, frame_width=640, frame_height=480):
    # Initialize video capture from webcam
    video_capture = cv2.VideoCapture(0)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(file_name, fourcc, 20.0, (frame_width, frame_height))

    # Initialize audio recording
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        frames_per_buffer=1024)

    # Record video and audio for the specified duration
    start_time = cv2.getTickCount()
    frames = []
    while (cv2.getTickCount() - start_time) / cv2.getTickFrequency() < duration:
        # Record video frame
        ret, frame = video_capture.read()
        if ret:
            out.write(frame)
            cv2.imshow('Recording...', frame)
        else:
            break

        # Record audio frame
        audio_frame = stream.read(1024)
        frames.append(audio_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to stop recording
            break

    # Release video capture and writer objects
    video_capture.release()
    out.release()
    cv2.destroyAllWindows()

    # Stop audio stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save recorded audio to file
    save_audio("extracted_audio" + ".wav", frames)

    print("Finished recording.")

def save_audio(file_name, frames):
    wave_file = wave.open(file_name, 'wb')
    wave_file.setnchannels(1)
    wave_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(44100)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()

@app.route('/add-question-answer', methods=['POST'])
def add_question_answer():
    print("sdasdasdsadasdasdasd")
    if 'username' in session and session['type'] == 'employer':
        if request.method == 'POST':
            print("asdas asda sd asd €ds ad as d")
            question = request.form['question']
            answer = request.form['answer']
            employer_id = User.query.filter_by(username=session['username']).first().id

            new_question_answer = QuestionAnswer(question=question, answer=answer, employer_id=employer_id)
            db.session.add(new_question_answer)
            db.session.commit()
            return redirect(url_for('profile'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
