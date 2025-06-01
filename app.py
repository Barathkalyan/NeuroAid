from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from supabase import create_client, Client
import bcrypt
import logging
import requests
from datetime import datetime, timedelta
import time
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = 'your-secret-key'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = 'https://kkzymljvdzbydqugbwuw.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrenltbGp2ZHpieWRxdWdid3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5OTcyMzgsImV4cCI6MjA2MDU3MzIzOH0.d6Xb4PrfYlcilkLOGWbPIG2WZ2c2rocZZEKCojwWfgs'
HF_API_KEY = "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"

def query_huggingface(model: str, payload: dict, retries=3, backoff_factor=1):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"https://api-inference.huggingface.co/models/{model}"
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt+1}/{retries})")
                time.sleep(wait_time)
                continue
            logger.error(f"HTTPError calling model '{model}': {e}, Response: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling model '{model}': {e}")
            return None
    logger.error(f"Failed to query model '{model}' after {retries} retries")
    return None

def simple_keyword_analysis(text):
    text = text.lower()
    emotions = []
    if any(word in text for word in ['sad', 'unhappy', 'down', 'depressed']):
        emotions.append({"label": "sadness", "score": 0.7})
    if any(word in text for word in ['angry', 'mad', 'frustrated', 'annoyed']):
        emotions.append({"label": "anger", "score": 0.7})
    if any(word in text for word in ['happy', 'joyful', 'great', 'amazing']):
        emotions.append({"label": "joy", "score": 0.7})
    if any(word in text for word in ['anxious', 'nervous', 'worried', 'scared']):
        emotions.append({"label": "anxiety", "score": 0.7})
    if not emotions:
        emotions.append({"label": "neutral", "score": 0.5})
    return emotions

def derive_mood_from_emotions(emotions):
    if not emotions:
        return 3, 0.5

    positive_emotions = ['joy', 'love', 'gratitude', 'hope', 'pride', 'amusement', 'optimism']
    negative_emotions = ['sadness', 'anger', 'fear', 'disgust', 'shame', 'frustration', 'anxiety', 'disappointment', 'annoyance', 'disapproval']
    neutral_emotions = ['neutral', 'confusion', 'surprise']

    top_emotion = max(emotions, key=lambda x: x['score'])
    emotion_label = top_emotion['label']
    confidence = top_emotion['score']

    if emotion_label in positive_emotions:
        mood_score = 5 if confidence > 0.7 else 4
    elif emotion_label in negative_emotions:
        mood_score = 1 if confidence > 0.7 else 2
    else:
        mood_score = 3
    return mood_score, confidence

def get_recent_emotions(supabase, user_id, days=7):
    start_date = (datetime.now(ZoneInfo("UTC")) - timedelta(days=days)).isoformat()
    try:
        query = supabase.table('journal_entries')\
            .select('analysis->emotions')\
            .eq('user_id', user_id)\
            .gt('created_at', start_date)\
            .limit(50)\
            .execute()
        all_emotions = []
        for entry in query.data:
            emotions = entry['emotions'] if 'emotions' in entry else []
            all_emotions.extend([e['label'] for e in emotions if e['score'] > 0.3])
        emotion_counts = {}
        for emotion in all_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        return emotion_counts
    except Exception as e:
        logger.error(f"Error fetching recent emotions: {str(e)}")
        return {}

def get_journaling_frequency(supabase, user_id, days=7):
    start_date = (datetime.now(ZoneInfo("UTC")) - timedelta(days=days)).isoformat()
    try:
        entries = supabase.table('journal_entries')\
            .select('created_at')\
            .eq('user_id', user_id)\
            .gt('created_at', start_date)\
            .execute()
        return len(entries.data)
    except Exception as e:
        logger.error(f"Error calculating journaling frequency: {str(e)}")
        return 0

def generate_suggestion(emotions, mood, supabase, user_id):
    if not emotions:
        return ["I’m here for you! Try writing a bit more to help me understand how you’re feeling."]

    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:2]
    primary_emotion = top_emotions[0]['label']
    primary_score = top_emotions[0]['score']
    secondary_emotion = top_emotions[1]['label'] if len(top_emotions) > 1 else None

    recent_emotions = get_recent_emotions(supabase, user_id)
    journaling_freq = get_journaling_frequency(supabase, user_id)

    tone = "I’m sorry to hear" if mood <= 2 else "I can see" if mood == 3 else "It’s great to hear"

    suggestions = []

    if primary_emotion in ['disappointment', 'sadness']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Maybe take a moment to write about what’s been challenging—it can help process those feelings.")
        if secondary_emotion in ['sadness', 'disappointment'] and primary_emotion != secondary_emotion:
            suggestions.append("It sounds like a mix of emotions. How about a gentle self-care activity, like listening to calming music or taking a warm shower?")
        elif secondary_emotion in ['anger', 'annoyance']:
            suggestions.append(f"With some {secondary_emotion.lower()} mixed in, you might find it helpful to channel that energy—maybe try a quick stretch or write down what’s frustrating you.")
        else:
            suggestions.append("Disappointment can be tough. How about doing something small that brings you comfort, like sipping a warm drink?")
    elif primary_emotion in ['anger', 'frustration', 'annoyance']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Let’s channel that energy—maybe take a few deep breaths or go for a quick walk to clear your mind.")
        if secondary_emotion in ['sadness', 'disappointment']:
            suggestions.append(f"I also sense some {secondary_emotion.lower()}. Writing about what’s upsetting you might help you feel lighter—want to try it?")
        else:
            suggestions.append("Sometimes putting your thoughts on paper can help. How about writing what’s been on your mind?")
    elif primary_emotion in ['fear', 'anxiety']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. A grounding exercise might help—try focusing on 5 things you can see around you right now.")
        if secondary_emotion in ['sadness', 'disappointment']:
            suggestions.append(f"With some {secondary_emotion.lower()} there too, maybe a comforting activity like wrapping up in a blanket could help soothe you.")
        else:
            suggestions.append("You’ve got this! Writing about what’s making you anxious might help untangle your thoughts.")
    elif primary_emotion in ['joy', 'gratitude', 'hope', 'love']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}! That’s so wonderful—keep it up by doing something you love, like enjoying a hobby or chatting with a friend.")
        suggestions.append("Let’s celebrate this moment! Why not share this feeling with someone close to you?")
    else:
        suggestions.append(f"{tone} you’re feeling a bit {primary_emotion.lower()}. Let’s explore that—maybe write about what’s on your mind to dig a little deeper.")
        suggestions.append("Taking a moment to breathe and reflect might help. Want to try it?")

    if recent_emotions:
        most_common_emotion = max(recent_emotions, key=recent_emotions.get)
        if recent_emotions[most_common_emotion] >= 3:
            if most_common_emotion in ['disappointment', 'sadness', 'anxiety', 'fear']:
                suggestions.append(f"I’ve noticed you’ve been feeling {most_common_emotion.lower()} a lot lately. It might help to talk to a trusted friend or try a new activity to lift your spirits.")
            elif most_common_emotion in ['joy', 'gratitude']:
                suggestions.append(f"You’ve been feeling {most_common_emotion.lower()} quite often lately—amazing! Keep nurturing those positive vibes.")

    if journaling_freq < 3:
        suggestions.append("You haven’t journaled much this week. Setting a small daily goal to write a few lines might help you feel more connected to your emotions.")
    elif journaling_freq > 10:
        suggestions.append("You’ve been journaling a lot lately—great job! Maybe take a moment to reflect on your entries and see if there’s a pattern in how you’re feeling.")

    if mood <= 2:
        suggestions.append("I’m here for you, and I believe things can get better. Tomorrow might bring a fresh perspective—hang in there!")

    return suggestions[:3]

def analyze_journal_entry(text, supabase, user_id):
    emotion_result = query_huggingface("SamLowe/roberta-base-go_emotions", {"inputs": text})

    emotions = []
    if emotion_result:
        if isinstance(emotion_result, list) and len(emotion_result) > 0:
            first = emotion_result[0]
            if isinstance(first, list):
                emotions = [{"label": e['label'], "score": e['score']} for e in first if isinstance(e, dict)]
            elif isinstance(first, dict):
                emotions = [{"label": first['label'], "score": first['score']}]
    else:
        logger.warning("Hugging Face API failed, falling back to keyword analysis")
        emotions = simple_keyword_analysis(text)

    mood_score, confidence = derive_mood_from_emotions(emotions)
    suggestions = generate_suggestion(emotions, mood_score, supabase, user_id)

    return {
        "mood": mood_score,
        "emotions": emotions,
        "suggestions": suggestions,
        "confidence": confidence
    }

def get_supabase():
    if 'supabase' not in g:
        g.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return g.supabase

@app.teardown_appcontext
def teardown_supabase(exception):
    if 'supabase' in g:
        g.pop('supabase')

@app.route('/api/mood_data', methods=['GET'])
def get_mood_data():
    if 'user' not in session:
        logger.warning("User not in session, returning Unauthorized.")
        return jsonify({'error': 'Unauthorized'}), 401
    supabase = get_supabase()
    user_id = session['user']
    start_date = (datetime.now(ZoneInfo("UTC")) - timedelta(days=7)).isoformat()
    try:
        entries = supabase.table('journal_entries')\
            .select('analysis, created_at')\
            .eq('user_id', user_id)\
            .gt('created_at', start_date)\
            .order('created_at', desc=False)\
            .execute()
        labels = []
        data = []
        # Calculate number of entries in the last 7 days
        num_entries = len(entries.data)
        logger.info(f"Fetched {num_entries} journal entries for user {user_id}")

        # Process entries for mood data
        for entry in entries.data:
            created_at = entry['created_at']
            try:
                if '.' in created_at:
                    created_at = created_at.split('.')[0] + '+00:00'
                else:
                    created_at = created_at.replace('Z', '+00:00')
                date = datetime.fromisoformat(created_at).replace(tzinfo=ZoneInfo("UTC"))
                labels.append(date.strftime('%a'))
                mood = entry['analysis'].get('mood', 3)  # Default to 3 if mood is missing
                data.append(mood)
                logger.info(f"Entry date: {date}, Mood: {mood}")
            except ValueError as e:
                logger.error(f"Error parsing created_at: {created_at}, Error: {str(e)}")
                continue
            except KeyError as e:
                logger.error(f"Error accessing analysis.mood in entry: {entry}, Error: {str(e)}")
                data.append(3)  # Fallback to neutral if analysis.mood is missing
                labels.pop()  # Remove the label to keep arrays in sync
                continue

        # Fallback if no entries
        if not labels:
            logger.warning(f"No valid entries found for user {user_id} in the last 7 days")
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            data = [3] * 7

        # Calculate streak
        # Fetch all entries for the user to calculate streak, ordered by date descending
        all_entries = supabase.table('journal_entries')\
            .select('created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        streak = 0
        current_date = datetime.now(ZoneInfo("UTC")).replace(hour=0, minute=0, second=0, microsecond=0)
        entry_dates = set()

        for entry in all_entries.data:
            created_at = entry['created_at']
            try:
                if '.' in created_at:
                    created_at = created_at.split('.')[0] + '+00:00'
                else:
                    created_at = created_at.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at).replace(tzinfo=ZoneInfo("UTC"))
                # Normalize to start of day
                entry_date = entry_date.replace(hour=0, minute=0, second=0, microsecond=0)
                entry_dates.add(entry_date)
            except ValueError as e:
                logger.error(f"Error parsing created_at for streak: {created_at}, Error: {str(e)}")
                continue

        # Check for consecutive days starting from today
        while True:
            if current_date in entry_dates:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

        logger.info(f"Calculated streak for user {user_id}: {streak} days")

        return jsonify({
            'labels': labels,
            'data': data,
            'numEntries': num_entries,
            'streak': streak
        })
    except Exception as e:
        logger.error(f"Error fetching mood data: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
                logger.info(f"User found: {user['id']}, {user['email']}")
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    session['user'] = str(user['id'])
                    session['user_email'] = user['email']
                    logger.info(f"User {user['email']} logged in successfully, user_id: {session['user']}")
                    return redirect(url_for('index'))
                else:
                    error = 'Invalid credentials.'
            else:
                error = 'Invalid credentials.'
        except Exception as e:
            error = 'Unable to log in right now. Please try again later.'
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
            logger.info(f"User {email} signed up successfully.")
            return redirect(url_for('login'))
        except Exception as e:
            if "duplicate key value" in str(e).lower():
                error = 'Email already exists.'
            else:
                error = 'Unable to sign up right now. Please try again later.'
            logger.error(f"Signup error: {str(e)}")
            return render_template('signup.html', error=error)

    return render_template('signup.html', error=error)

@app.route('/index')
def index():
    if 'user' not in session:
        logger.warning("User not in session, redirecting to login.")
        return redirect(url_for('login'))

    supabase = get_supabase()
    user_id = session['user']
    logger.info(f"Fetching data for user_id: {user_id}")

    # Current time in UTC and IST for debugging
    utc_now = datetime.now(ZoneInfo("UTC"))
    ist_now = utc_now.astimezone(ZoneInfo("Asia/Kolkata"))
    logger.info(f"Current UTC time: {utc_now}, IST time: {ist_now}")

    # Define today's start and end in UTC
    today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = utc_now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    logger.info(f"Today range (UTC): {today_start} to {today_end}")

    suggestions = None
    recent_entries_data = []

    try:
        # Fetch suggestions for today
        latest_entry_query = supabase.table('journal_entries')\
            .select('created_at, analysis')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)

        logger.info(f"Executing query for latest entry: {latest_entry_query}")
        latest_entry = latest_entry_query.execute()

        if latest_entry.data:
            logger.info(f"Latest entry: {latest_entry.data[0]}")
            # Handle different created_at formats
            created_at_str = latest_entry.data[0]['created_at']
            try:
                if '.' in created_at_str:
                    created_at_str = created_at_str.split('.')[0] + '+00:00'
                else:
                    created_at_str = created_at_str.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
            except ValueError as e:
                logger.error(f"Error parsing created_at: {created_at_str}, Error: {str(e)}")
                entry_date = None

            if entry_date:
                entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
                current_date_ist = ist_now.date()

                logger.info(f"Entry date (IST): {entry_date_ist.date()}, Current date (IST): {current_date_ist}")

                if entry_date_ist.date() == current_date_ist:
                    suggestions = latest_entry.data[0]['analysis'].get('suggestions', [])
                    logger.info(f"Suggestions found: {suggestions}")
                else:
                    suggestions = ["Write a journal entry for today to get personalized suggestions!"]
                    logger.info("No entry for today, prompting user to write a new entry.")
            else:
                suggestions = ["Unable to parse entry date. Please try writing a new journal entry!"]
                logger.info("Failed to parse entry date for suggestions.")
        else:
            suggestions = ["Write a journal entry to get personalized suggestions!"]
            logger.info("No journal entries found for user.")

        # Fetch the 3 most recent journal entries for preview
        recent_entries_query = supabase.table('journal_entries')\
            .select('id, content, created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(3)

        logger.info(f"Executing query for recent entries: {recent_entries_query}")
        recent_entries = recent_entries_query.execute()

        recent_entries_data = recent_entries.data if recent_entries.data else []
        logger.info(f"Recent entries fetched: {recent_entries_data}")

        # Format the created_at date for display
        for entry in recent_entries_data:
            created_at_str = entry['created_at']
            try:
                if '.' in created_at_str:
                    created_at_str = created_at_str.split('.')[0] + '+00:00'
                else:
                    created_at_str = created_at_str.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
                entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
                entry['created_at'] = entry_date_ist.strftime('%B %d, %Y')
            except ValueError as e:
                logger.error(f"Error parsing created_at for recent entry: {created_at_str}, Error: {str(e)}")
                entry['created_at'] = "Unknown Date"
            # Truncate content to 50 characters
            entry['content_snippet'] = (entry['content'][:50] + '…') if len(entry['content']) > 50 else entry['content']

    except Exception as e:
        logger.error(f"Error fetching data for index: {str(e)}")
        suggestions = ["Unable to load suggestions right now. Try writing a journal entry!"]
        recent_entries_data = []

    return render_template('index.html', suggestions=suggestions, recent_entries=recent_entries_data)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        logger.warning("User not in session, redirecting to login.")
        return redirect(url_for('login'))

    supabase = get_supabase()
    user_id = session['user']
    current_date = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata")).strftime('%B %d, %Y')

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            try:
                analysis = analyze_journal_entry(content, supabase, user_id)

                journal_data = {
                    'user_id': user_id,
                    'content': content,
                    'created_at': datetime.now(ZoneInfo("UTC")).isoformat(),
                    'analysis': analysis
                }

                supabase.table('journal_entries').insert(journal_data).execute()
                logger.info(f"Journal entry saved for user_id: {user_id}")
                return redirect(url_for('journal'))
            except Exception as e:
                logger.error(f"Journal save error: {str(e)}")
                return render_template('Journal.html', error="Failed to save journal entry. Please try again later.", current_date=current_date)

    try:
        entries = supabase.table('journal_entries')\
            .select('id, content, created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        for entry in entries.data:
            created_at_str = entry['created_at']
            try:
                if '.' in created_at_str:
                    created_at_str = created_at_str.split('.')[0] + '+00:00'
                else:
                    created_at_str = created_at_str.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
                entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
                entry['created_at'] = entry_date_ist.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                logger.error(f"Error parsing created_at in journal: {created_at_str}, Error: {str(e)}")
                entry['created_at'] = "Unknown Date"

        return render_template('Journal.html', entries=entries.data if entries.data else [], current_date=current_date)
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', error="Failed to load journal entries. Please try again later.", current_date=current_date)

@app.route('/delete_entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    if 'user' not in session:
        logger.warning("User not in session, returning Unauthorized.")
        return "Unauthorized", 401
    
    supabase = get_supabase()
    user_id = session['user']

    try:
        response = supabase.table('journal_entries').select('*').eq('id', entry_id).execute()
        if not response.data or response.data[0]['user_id'] != user_id:
            logger.warning(f"User {user_id} attempted to delete entry {entry_id} - Forbidden.")
            return "Forbidden", 403
        
        supabase.table('journal_entries').delete().eq('id', entry_id).execute()
        logger.info(f"Entry {entry_id} deleted by user {user_id}.")
        return "Deleted", 200
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return "Unable to delete entry. Please try again later.", 500
    
@app.route('/progress')
def progress():
    if 'user' not in session:
        logger.warning("User not in session, redirecting to login.")
        return redirect(url_for('login'))
    return render_template('progress.html')

@app.route('/profile')
def profile():
    if 'user' not in session:
        logger.warning("User not in session, redirecting to login.")
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/logout')
def logout():
    user_email = session.get('user_email', 'Unknown')
    session.pop('user', None)
    session.pop('user_email', None)
    logger.info(f"User {user_email} logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)