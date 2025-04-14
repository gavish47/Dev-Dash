from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime
import matplotlib.pyplot as plt
import os
import time
import threading
import webbrowser
import logging
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devdash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Float, nullable=True)
    git_commits = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Session {self.project_name}>"

REMINDER_MESSAGE = "⏰ Time to start your DevDash session!"
DEV_DASH_URL = "http://127.0.0.1:5000/"

def show_reminder():
    while True:
        print(REMINDER_MESSAGE)
        webbrowser.open(DEV_DASH_URL)
        time.sleep(300)  

@app.route('/')
def index():
    sessions = Session.query.order_by(Session.start_time.desc()).all()
    return render_template('index.html', sessions=sessions)

@app.route('/start', methods=['POST'])
def start_session():
    project_name = request.form['project_name']
    notes = request.form.get('notes', '')
    
    if not project_name:
        return "Project name is required", 400  # Ensure project name is provided
    
    new_session = Session(project_name=project_name, notes=notes)
    
    try:
        db.session.add(new_session)
        db.session.commit()
        return redirect(url_for('index'))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        return "There was an issue starting the session.", 500

@app.route('/end', methods=['POST'])
def end_session():
    session_id = request.form['session_id']
    session = Session.query.get_or_404(session_id)

    session.end_time = datetime.datetime.utcnow()
    session.duration = (session.end_time - session.start_time).total_seconds() / 60  # in minutes
    
    try:
        git_commits_raw = request.form.get('git_commits', '0')
        session.git_commits = int(git_commits_raw) if git_commits_raw.isdigit() else 0
    except ValueError:
        session.git_commits = 0

    try:
        db.session.commit()
        return redirect(url_for('index'))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        return "There was an issue ending the session.", 500

@app.route('/refresh')
def refresh_sessions():
    sessions = Session.query.order_by(Session.start_time.desc()).all()
    return render_template('index.html', sessions=sessions)

@app.route('/analytics')
def analytics():
    sessions = Session.query.all()

    if not sessions:
        return render_template('analytics.html', no_data=True)

    total_duration = sum(s.duration for s in sessions if s.duration) or 0
    durations = [s.duration for s in sessions if s.duration is not None]
    avg_duration = total_duration / len(durations) if durations else 0
    total_commits = sum(s.git_commits for s in sessions if s.git_commits is not None)

    project_time = {}
    for session in sessions:
        if session.project_name not in project_time:
            project_time[session.project_name] = 0
        if session.duration:
            project_time[session.project_name] += session.duration

    labels = list(project_time.keys())
    sizes = list(project_time.values())
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    
    chart_path = os.path.join('static', 'project_distribution.png')
    try:
        plt.savefig(chart_path)
        plt.close()
    except Exception as e:
        logging.error(f"Error generating pie chart: {e}")
        chart_path = None

    return render_template(
        'analytics.html',
        total_duration=total_duration,  
        avg_duration=avg_duration,
        total_commits=total_commits,
        chart_path=chart_path,
        no_data=False,
        project_names=labels,
        project_times=sizes,
        durations=durations
    )

if __name__ == '__main__':
    reminder_thread = threading.Thread(target=show_reminder)
    reminder_thread.daemon = True  
    reminder_thread.start()

    with app.app_context():
        db.create_all()

    # Run the Flask app
    app.run(debug=True)
