from flask import Flask, render_template, request, redirect, url_for, session, g
from supabase import create_client, Client
import bcrypt
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = 'https://kkzymljvdzbydqugbwuw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrenltbGp2ZHpieWRxdWdid3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5OTcyMzgsImV4cCI6MjA2MDU3MzIzOH0.d6Xb4PrfYlcilkLOGWbPIG2WZ2c2rocZZEKCojwWfgs'

import requests

HF_API_KEY = "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"  # Replace with your actual Hugging Face API key

def query_huggingface(model: str, payload: dict):
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError calling model '{model}': {e}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error calling model '{model}': {e}")
        return None

import re

def clean_html(raw_html):
    """Remove HTML tags and some weird Hugging Face artifacts."""
    cleanr = re.compile('<.*?>')  # remove HTML tags
    cleaned = re.sub(cleanr, '', raw_html)
    cleaned = re.sub(r'style:.*?(?=\.|$)', '', cleaned)  # remove style artifacts
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # normalize spaces
    return cleaned


def generate_suggestion(mood, emotions):
    """Generate suggestions based on mood and emotions."""
    if mood == "NEGATIVE":
        if "sadness" in emotions:
            return "Try writing about what made you feel sad and see if there's a pattern."
        if "anger" in emotions:
            return "Taking a short walk or deep breaths might help you cool off."
        if "fear" in emotions:
            return "Consider writing about what you’re afraid of and how you might face it."
        return "Take it slow today and give yourself some space to feel and recover."

    elif mood == "POSITIVE":
        return "That's great! Keep doing what uplifts you and celebrate the little wins."

    elif mood == "NEUTRAL":
        return "Reflecting on small details might help you discover hidden highs and lows."

    return "Keep journaling daily to track your progress and feelings!"

def analyze_journal_entry(text):
    """Analyze a journal entry using Hugging Face models."""
    sentiment = query_huggingface("distilbert/distilbert-base-uncased-finetuned-sst-2-english", {"inputs": text})
    emotion = query_huggingface("j-hartmann/emotion-english-distilroberta-base", {"inputs": text})
    summary = query_huggingface("sshleifer/distilbart-cnn-12-6", {"inputs": text})

    # Extract mood
    mood = "Unknown"
    if isinstance(sentiment, list) and len(sentiment) > 0:
        candidates = sentiment if isinstance(sentiment[0], dict) else sentiment[0]
        if isinstance(candidates, list):
            best = max(candidates, key=lambda x: x.get('score', 0))
            mood = best.get('label', "Unknown")
        elif isinstance(candidates, dict):
            mood = candidates.get('label', "Unknown")

    # Extract emotions
    emotions = []
    if isinstance(emotion, list) and len(emotion) > 0:
        first = emotion[0]
        if isinstance(first, list):
            emotions = [e.get('label', 'Unknown') for e in first if isinstance(e, dict)]
        elif isinstance(first, dict):
            emotions = [first.get('label', 'Unknown')]

    # Clean and extract summary
    summary_text = ""
    if isinstance(summary, list) and len(summary) > 0 and isinstance(summary[0], dict):
        raw_summary = summary[0].get('summary_text', "")
        summary_text = clean_html(raw_summary)

    return {
        "mood": mood,
        "emotions": emotions,
        "summary": summary_text,
        "suggestions": generate_suggestion(mood, emotions)
    }


def get_supabase():
    if 'supabase' not in g:
        g.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return g.supabase

@app.teardown_appcontext
def teardown_supabase(exception):
    if 'supabase' in g:
        g.pop('supabase')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            error = 'Email and password are required.'
            return render_template('login.html', error=error)

        supabase = get_supabase()
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                user = response.data[0]
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    session['user'] = str(user['id'])  # Ensure UUID is stored as a string
                    session['user_email'] = user['email']
                    return redirect(url_for('index'))
                else:
                    error = 'Invalid credentials.'
            else:
                error = 'Invalid credentials.'
        except Exception as e:
            error = f'Login failed: {str(e)}'
            logger.error(f"Login error: {str(e)}")

    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            error = 'Email, password, and confirm password are required.'
            return render_template('signup.html', error=error)

        if password != confirm_password:
            error = 'Passwords do not match!'
            return render_template('signup.html', error=error)

        supabase = get_supabase()
        try:
            response = supabase.table('users').select('email').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                error = 'Email already exists.'
                return render_template('signup.html', error=error)

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_data = {'email': email, 'password': hashed_password}
            response = supabase.table('users').insert(user_data).execute()
            return redirect(url_for('login'))
        except Exception as e:
            if "duplicate key value" in str(e).lower():
                error = 'Email already exists.'
            else:
                error = f'Signup failed: {str(e)}'
            logger.error(f"Signup error: {str(e)}")
            return render_template('signup.html', error=error)

    return render_template('signup.html', error=error)

@app.route('/index')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

from datetime import datetime  # ✅ Add this at the top of app.py
import logging                 # ✅ For logger
logger = logging.getLogger(__name__)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        return redirect(url_for('login'))

    supabase = get_supabase()
    user_id = session['user']  # user_id is a UUID string

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            try:
                # 🧠 Analyze the journal text using Hugging Face
                analysis = analyze_journal_entry(content)

                journal_data = {
                    'user_id': user_id,
                    'content': content,
                    'created_at': datetime.utcnow().isoformat(),  # ✅ Add timestamp
                    'analysis': analysis  # ✅ Save analysis
                }

                supabase.table('journal_entries').insert(journal_data).execute()
                return redirect(url_for('journal'))
            except Exception as e:
                logger.error(f"Journal save error: {str(e)}")
                return render_template('Journal.html', error=f"Failed to save journal: {str(e)}")

    try:
        entries = supabase.table('journal_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        return render_template('Journal.html', entries=entries.data if entries.data else [])
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', error=f"Failed to fetch journals: {str(e)}")


@app.route('/delete_entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    if 'user' not in session:
        return "Unauthorized", 401
    
    supabase = get_supabase()
    user_id = session['user']

    try:
        # Check if the entry belongs to the logged-in user
        response = supabase.table('journal_entries').select('*').eq('id', entry_id).execute()
        if not response.data or response.data[0]['user_id'] != user_id:
            return "Forbidden", 403
        
        # Delete the entry
        supabase.table('journal_entries').delete().eq('id', entry_id).execute()
        return "Deleted", 200
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return "Internal Server Error", 500

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)