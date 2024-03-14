from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

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

        if user:
            session['username'] = user.username
            session['type'] = user.type
            return redirect(url_for('profile'))
        else:
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
            if request.method == 'POST':
                # Add new question and answer
                question = request.form['question']
                answer = request.form['answer']
                new_question_answer = QuestionAnswer(question=question, answer=answer, employer=user)
                db.session.add(new_question_answer)
                db.session.commit()
                return redirect(url_for('profile'))
            else:
                # Fetch previously added questions and answers
                questions_answers = QuestionAnswer.query.filter_by(employer=user).all()
                return render_template('employer.html', username=session['username'], type=session['type'], questions_answers=questions_answers)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('type', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

