from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from supabase import create_client, Client
import bcrypt
import logging
import requests
from datetime import datetime, timedelta
import time
from zoneinfo import ZoneInfo
import uuid
import pyotp
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

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
    negative_emotions = ['sadness', 'anger', 'fear', 'disgust', 'shame', 'frustration', 'anxiety']
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
        return ["Try writing more to help me understand your feelings."]

    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:2]
    primary_emotion = top_emotions[0]['label']
    primary_score = top_emotions[0]['score']
    secondary_emotion = top_emotions[1]['label'] if len(top_emotions) > 1 else None

    recent_emotions = get_recent_emotions(supabase, user_id)
    journaling_freq = get_journaling_frequency(supabase, user_id)

    tone = "I’m sorry to hear" if mood <= 2 else "I can see" if mood == 3 else "It’s great to hear"

    suggestions = []

    if primary_emotion in ['disappointment', 'sadness']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Write about what’s been challenging.")
        if secondary_emotion in ['anger', 'annoyance']:
            suggestions.append(f"Try a quick stretch to channel that {secondary_emotion.lower()}.")
    elif primary_emotion in ['anger', 'frustration', 'annoyance']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Take a few deep breaths.")
    elif primary_emotion in ['fear', 'anxiety']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Focus on 5 things you can see.")
    elif primary_emotion in ['joy', 'gratitude', 'hope', 'love']:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}! Do something you love.")
    else:
        suggestions.append(f"{tone} you’re feeling {primary_emotion.lower()}. Write more to explore.")

    if journaling_freq < 3:
        suggestions.append("Journal daily to connect with your emotions.")
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
        logger.warning("Hugging Face API failed, using keyword analysis")
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

@app.before_request
def make_session_permanent():
    session.permanent = True
    if 'user' in session and 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if (datetime.now(ZoneInfo("UTC")) - last_activity) > app.config['PERMANENT_SESSION_LIFETIME']:
            session.pop('user', None)
            session.pop('user_email', None)
            session.pop('access_token', None)
            session.pop('last_activity', None)
            logger.info("Session expired, user logged out.")
            return redirect(url_for('login'))
    if 'user' in session:
        session['last_activity'] = datetime.now(ZoneInfo("UTC")).isoformat()

@app.route('/api/mood_data', methods=['GET'])
def get_mood_data():
    if 'user' not in session:
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
        logger.info(f"Fetched {len(entries.data)} journal entries for user {user_id}")

        end_date = datetime.now(ZoneInfo("UTC")).replace(hour=23, minute=59, second=59, microsecond=999999)
        current_date = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        labels = []
        mood_data = []
        confidence_data = []
        date_map = {}

        for i in range(7):
            date_str = current_date.strftime('%Y-%m-%d')
            labels.append(current_date.strftime('%b %d'))
            date_map[date_str] = {'moods': [], 'confidences': []}
            current_date += timedelta(days=1)

        for entry in entries.data:
            created_at = entry['created_at']
            if '.' in created_at:
                created_at = created_at.split('.')[0] + '+00:00'
            else:
                created_at = created_at.replace('Z', '+00:00')
            date = datetime.fromisoformat(created_at).replace(tzinfo=ZoneInfo("UTC"))
            date_str = date.strftime('%Y-%m-%d')
            if date_str in date_map:
                mood = entry['analysis'].get('mood', 3)
                confidence = entry['analysis'].get('confidence', 0.0)
                date_map[date_str]['moods'].append(mood)
                date_map[date_str]['confidences'].append(confidence)
                logger.info(f"Entry date: {date}, Mood: {mood}, Confidence: {confidence}")

        for date_str in date_map:
            moods = date_map[date_str]['moods']
            confidences = date_map[date_str]['confidences']
            avg_mood = sum(moods) / len(moods) if moods else 0
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            mood_data.append(round(avg_mood, 2))
            confidence_data.append(round(avg_confidence, 2))

        if not any(mood_data):
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            mood_data = [3] * 7
            confidence_data = [0] * 7

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
            if '.' in created_at:
                created_at = created_at.split('.')[0] + '+00:00'
            else:
                created_at = created_at.replace('Z', '+00:00')
            entry_date = datetime.fromisoformat(created_at).replace(tzinfo=ZoneInfo("UTC"))
            entry_date = entry_date.replace(hour=0, minute=0, second=0, microsecond=0)
            entry_dates.add(entry_date)

        while True:
            if current_date in entry_dates:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

        logger.info(f"Calculated journal streak for user {user_id}: {streak} days")

        return jsonify({
            'labels': labels,
            'data': mood_data,
            'numEntries': len(entries.data),
            'streak': streak,
            'confidence': confidence_data
        })
    except Exception as e:
        logger.error(f"Error fetching mood data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gratitude', methods=['GET', 'POST'])
def handle_gratitude():
    if 'user' not in session:
        logger.warning("User not authenticated for /api/gratitude")
        return jsonify({'error': 'Unauthorized'}), 401

    supabase = get_supabase()
    user_id = session['user']

    if request.method == 'POST':
        try:
            data = request.get_json()
            thing1 = data.get('thing1')
            thing2 = data.get('thing2')
            thing3 = data.get('thing3')

            if not thing1 or not thing2 or not thing3:
                return jsonify({'success': False, 'error': 'All fields are required'}), 400

            gratitude_entry = {
                'user_id': user_id,
                'thing1': thing1,
                'thing2': thing2,
                'thing3': thing3,
                'created_at': datetime.now(ZoneInfo("UTC")).isoformat()
            }

            supabase.table('gratitude_entries').insert(gratitude_entry).execute()
            logger.info(f"Gratitude entry saved for user_id: {user_id}")
            return jsonify({'success': True}), 200
        except Exception as e:
            logger.error(f"Error saving gratitude entry: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    else:
        try:
            entries = supabase.table('gratitude_entries')\
                .select('thing1, thing2, thing3, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()

            formatted_entries = []
            for entry in entries.data:
                created_at_str = entry['created_at']
                if '.' in created_at_str:
                    created_at_str = created_at_str.split('.')[0] + '+00:00'
                else:
                    created_at_str = created_at_str.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
                entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
                formatted_entries.append({
                    'thing1': entry['thing1'],
                    'thing2': entry['thing2'],
                    'thing3': entry['thing3'],
                    'date': entry_date_ist.strftime('%B %d, %Y')
                })

            all_entries = supabase.table('gratitude_entries')\
                .select('created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()

            streak = 0
            current_date = datetime.now(ZoneInfo("UTC")).replace(hour=0, minute=0, second=0, microsecond=0)
            entry_dates = set()

            for entry in all_entries.data:
                created_at = entry['created_at']
                if '.' in created_at:
                    created_at = created_at.split('.')[0] + '+00:00'
                else:
                    created_at = created_at.replace('Z', '+00:00')
                entry_date = datetime.fromisoformat(created_at).replace(tzinfo=ZoneInfo("UTC"))
                entry_date = entry_date.replace(hour=0, minute=0, second=0, microsecond=0)
                entry_dates.add(entry_date)

            while True:
                if current_date in entry_dates:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

            logger.info(f"Calculated gratitude streak for user {user_id}: {streak} days")

            return jsonify({
                'entries': formatted_entries,
                'streak': streak
            })
        except Exception as e:
            logger.error(f"Error fetching gratitude entries: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/recommend_music', methods=['GET'])
def recommend_music():
    if 'user' not in session:
        logger.warning("User not authenticated for /api/recommend_music")
        return jsonify({'error': 'Unauthorized'}), 401

    supabase = get_supabase()
    user_id = session['user']
    date = request.args.get('date')

    try:
        query = supabase.table('journal_entries')\
            .select('analysis->mood')\
            .eq('user_id', user_id)
        
        if date:
            try:
                start_date = datetime.fromisoformat(date.replace('Z', '+00:00')).replace(tzinfo=ZoneInfo("UTC"))
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat())
            except ValueError:
                logger.error(f"Invalid date format: {date}")
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        query = query.order('created_at', desc=True).limit(1)
        entries = query.execute()
        
        mood = entries.data[0]['mood'] if entries.data else 3
        
        preferences = supabase.table('user_preferences')\
            .select('language')\
            .eq('user_id', user_id)\
            .execute()
        language = preferences.data[0]['language'] if preferences.data else 'tamil'

        MOOD_PLAYLISTS = {
    'tamil': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWX3SoTqhs2rq',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWVV27DiNWxkR',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXz6ZFxA5jKQ',
        4: 'https://open.spotify.com/embed/playlist/2Yra1CyIYaJ2YNz49yjh4i',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWUnAwRxD2pxH'
    },
    'english': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX9sIqqvKsjG8',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX3rxVfibe1L0',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX0BcQWzuB7ZO',
        4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWUa8ZRTfalSI'
    },
    'hindi': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWYkaDif7Ztbp',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWUVpAXiEPK8P',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX4dyzvuaRJ0n',
        4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX4SBhb3fqCJd',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX4ZrmoTDh6zJ'
    },
    'telugu': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXLeA8Omikj7',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXapHi7gXtXo2',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXdbXrPNafg9d',
        4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXaKIA8E7WcJj',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXi7h5CniH97'
    },
    'malayalam': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWWhB4HOWKFQc',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX6KYgZMe25iS',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXbqXxdO1a3nX',
        4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWZz8QXaU2aX5',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWVoDnLC9PqaD'
    },
    'kannada': {
        1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXh3XHYZ7Sx1',
        2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX33aWnYYWvdf',
        3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWVXaB8Ox0zRJ',
        4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXe3a8d5bfgGk',
        5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWUTJW8w3JNz2'
    }
}

        playlist_url = MOOD_PLAYLISTS.get(language, MOOD_PLAYLISTS['tamil']).get(mood)
        
        if not playlist_url:
            logger.error(f"No playlist found for mood {mood} and language {language}")
            return jsonify({'error': 'No playlist available for this mood and language'}), 404

        return jsonify({'embedUrl': playlist_url, 'mood': mood}), 200

    except Exception as e:
        logger.error(f"Error recommending Spotify playlist: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/update_language', methods=['GET', 'POST'])
def update_language():
    if 'user' not in session:
        logger.warning("User not authenticated for /api/update_language")
        return jsonify({'error': 'Unauthorized'}), 401

    supabase = get_supabase()
    user_id = session['user']

    if request.method == 'GET':
        try:
            preferences = supabase.table('user_preferences')\
                .select('language')\
                .eq('user_id', user_id)\
                .execute()
            language = preferences.data[0]['language'] if preferences.data else 'tamil'
            return jsonify({'language': language}), 200
        except Exception as e:
            logger.error(f"Error fetching user language: {str(e)}")
            return jsonify({'error': 'Failed to fetch language'}), 500
                                  
    try:
        data = request.get_json()
        language = data.get('language', 'tamil')
        valid_languages = ['tamil', 'hindi', 'telugu', 'malayalam', 'kannada', 'english']
        if language not in valid_languages:
            return jsonify({'error': 'Invalid language'}), 400

        supabase.table('user_preferences').update({'language': language}).eq('user_id', user_id).execute()
        logger.info(f"Language updated to {language} for user {user_id}")
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error updating language: {str(e)}")
        return jsonify({'error': 'Failed to update language'}), 500

@app.route('/setup_2fa', methods=['GET', 'POST'])
def setup_2fa():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    supabase = get_supabase()
    user_id = session['user']
    
    if request.method == 'POST':
        try:
            totp = pyotp.TOTP(pyotp.random_base32())
            secret = totp.secret
            supabase.table('user_preferences').update({
                'two_factor_secret': secret,
                'two_factor_enabled': True
            }).eq('user_id', user_id).execute()
            
            provisioning_uri = totp.provisioning_uri(
                name=session['user_email'],
                issuer_name='NeuroAid'
            )
            
            img = qrcode.make(provisioning_uri)
            buffered = BytesIO()
            img.save(buffered)
            qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return render_template('setup_2fa.html', qr_code=qr_code, secret=secret)
        except Exception as e:
            logger.error(f"Error setting up 2FA: {str(e)}")
            return render_template('setup_2fa.html', error="Failed to set up 2FA.")
    
    try:
        preferences = supabase.table('user_preferences')\
            .select('two_factor_secret')\
            .eq('user_id', user_id)\
            .execute()
        
        if preferences.data and preferences.data[0]['two_factor_secret']:
            return redirect(url_for('verify_2fa'))
        
        return render_template('setup_2fa.html')
    except Exception as e:
        logger.error(f"Error checking 2FA setup: {str(e)}")
        return render_template('setup_2fa.html', error="Error checking 2FA status.")

@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    supabase = get_supabase()
    user_id = session['user']
    
    if request.method == 'POST':
        try:
            code = request.form.get('code')
            preferences = supabase.table('user_preferences')\
                .select('two_factor_secret')\
                .eq('user_id', user_id)\
                .execute()
            
            if not preferences.data or not preferences.data[0]['two_factor_secret']:
                return render_template('verify_2fa.html', error="2FA not set up.")
            
            secret = preferences.data[0]['two_factor_secret']
            totp = pyotp.TOTP(secret)
            
            if totp.verify(code):
                session['2fa_verified'] = True
                return redirect(url_for('index'))
            else:
                return render_template('verify_2fa.html', error="Invalid 2FA code.")
        except Exception as e:
            logger.error(f"Error verifying 2FA: {str(e)}")
            return render_template('verify_2fa.html', error="Error verifying 2FA code.")
    
    return render_template('verify_2fa.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            error = 'Email and password are required.'
            return render_template('login.html', error=error), 400
        supabase = get_supabase()
        try:
            user_response = supabase.table('users').select('id, email, password').eq('email', email).execute()
            if not user_response.data:
                error = 'User not found.'
                return render_template('login.html', error=error), 401
            user = user_response.data[0]
            stored_password = user['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user'] = str(user['id'])
                session['user_email'] = email
                session['last_activity'] = datetime.now(ZoneInfo("UTC")).isoformat()
                preferences = supabase.table('user_preferences')\
                    .select('theme, two_factor_enabled, two_factor_secret')\
                    .eq('user_id', user['id'])\
                    .execute()
                session['theme'] = preferences.data[0]['theme'] if preferences.data else 'light'
                if preferences.data and preferences.data[0]['two_factor_enabled'] and preferences.data[0]['two_factor_secret']:
                    return redirect(url_for('verify_2fa'))
                logger.info(f"User {email} logged in successfully, user_id: {user['id']}, theme: {session['theme']}")
                return redirect(url_for('index'))
            else:
                error = 'Invalid credentials.'
                return render_template('login.html', error=error), 401
        except Exception as e:
            error = 'Unable to log in right now. Please try again later.'
            logger.error(f"Login error: {str(e)}")
            return render_template('login.html', error=error), 500
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
            return render_template('signup.html', error=error), 400

        if password != confirm_password:
            error = 'Passwords do not match!'
            return render_template('signup.html', error=error), 400

        supabase = get_supabase()
        try:
            existing_user = supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                error = 'Email already exists.'
                return render_template('signup.html', error=error), 400

            user_id = str(uuid.uuid4())
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_data = {'id': user_id, 'email': email, 'password': hashed_password}
            supabase.table('users').insert(user_data).execute()

            preferences_data = {
                'user_id': user_id,
                'two_factor_enabled': False,
                'two_factor_secret': None,
                'theme': 'light',
                'reminder_time': '09:00',
                'notification_preference': 'email'
            }
            supabase.table('user_preferences').insert(preferences_data).execute()

            logger.info(f"User {email} signed up successfully with user_id: {user_id}")
            return redirect(url_for('login'))
        except Exception as e:
            error = 'Unable to sign up right now. Please try again later.'
            logger.error(f"Signup error: {str(e)}")
            return render_template('signup.html', error=error), 400

    return render_template('signup.html', error=error)

@app.route('/index')
def index():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    supabase = get_supabase()
    user_id = session['user']
    logger.info(f"Fetching data for user_id: {user_id}")

    utc_now = datetime.now(ZoneInfo("UTC"))
    ist_now = utc_now.astimezone(ZoneInfo("Asia/Kolkata"))
    logger.info(f"Current UTC time: {utc_now}, IST time: {ist_now}")

    today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = utc_now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    logger.info(f"Today range (UTC): {today_start} to {today_end}")

    suggestions = None
    recent_entries_data = []

    try:
        latest_entry_query = supabase.table('journal_entries')\
            .select('created_at, analysis')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)

        logger.info(f"Executing query for latest entry: {latest_entry_query}")
        latest_entry = latest_entry_query.execute()

        if latest_entry.data:
            logger.info(f"Latest entry: {latest_entry.data[0]}")
            created_at_str = latest_entry.data[0]['created_at']
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0] + '+00:00'
            else:
                created_at_str = created_at_str.replace('Z', '+00:00')
            entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
            entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
            current_date_ist = ist_now.date()

            logger.info(f"Entry date (IST): {entry_date_ist.date()}, Current date (IST): {current_date_ist}")

            if entry_date_ist.date() == current_date_ist:
                suggestions = latest_entry.data[0]['analysis'].get('suggestions', [])
            else:
                suggestions = ["Write a journal entry for today!"]
        else:
            suggestions = ["Write a journal entry to get suggestions!"]

        recent_entries_query = supabase.table('journal_entries')\
            .select('id, content, created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(3)

        logger.info(f"Executing query for recent entries: {recent_entries_query}")
        recent_entries = recent_entries_query.execute()

        recent_entries_data = recent_entries.data if recent_entries.data else []
        entries_summary = [{'id': entry['id'], 'created_at': entry['created_at']} for entry in recent_entries_data]
        logger.info(f"Recent entries fetched: {entries_summary}")
        logger.debug(f"Full recent entries: {recent_entries_data}")

        for entry in recent_entries_data:
            created_at_str = entry['created_at']
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0] + '+00:00'
            else:
                created_at_str = created_at_str.replace('Z', '+00:00')
            entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
            entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
            entry['created_at'] = entry_date_ist.strftime('%B %d, %Y')
            entry['content_snippet'] = (entry['content'][:50] + '…') if len(entry['content']) > 50 else entry['content']

    except Exception as e:
        logger.error(f"Error fetching data for index: {str(e)}")
        suggestions = ["Unable to load suggestions. Try writing!"]
        recent_entries_data = []

    return render_template('index.html', suggestions=suggestions, recent_entries=recent_entries_data, theme=session.get('theme', 'light'))

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

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
                return render_template('Journal.html', error="Failed to save entry.", current_date=current_date, theme=session.get('theme', 'light'))

    try:
        entries = supabase.table('journal_entries')\
            .select('id, content, created_at')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        for entry in entries.data:
            created_at_str = entry['created_at']
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0] + '+00:00'
            else:
                created_at_str = created_at_str.replace('Z', '+00:00')
            entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
            entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
            entry['created_at'] = entry_date_ist.strftime('%Y-%m-%d %H:%M:%S')

        return render_template('Journal.html', entries=entries.data if entries.data else [], current_date=current_date, theme=session.get('theme', 'light'))
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', error="Failed to load entries.", current_date=current_date, theme=session.get('theme', 'light'))

@app.route('/delete_entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return "Unauthorized", 401
    
    supabase = get_supabase()
    user_id = session['user']

    try:
        response = supabase.table('journal_entries').select('*').eq('id', entry_id).execute()
        if not response.data or response.data[0]['user_id'] != user_id:
            return "Forbidden", 403
        
        supabase.table('journal_entries').delete().eq('id', entry_id).execute()
        logger.info(f"Entry {entry_id} deleted by user {user_id}.")
        return "Deleted", 200
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return "Unable to delete entry.", 500
    
@app.route('/progress')
def progress():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    return render_template('progress.html', theme=session.get('theme', 'light'))

@app.route('/vibe')
def vibe():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    return render_template('vibe.html', theme=session.get('theme', 'light'))

@app.route('/gratitude')
def gratitude():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    return render_template('gratitude.html', theme=session.get('theme', 'light'))

@app.route('/profile')
def profile():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    return render_template('profile.html', theme=session.get('theme', 'light'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    supabase = get_supabase()
    user_id = session['user']
    error = None
    success = None

    if request.method == 'POST':
        try:
            new_email = request.form.get('email')
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if new_email or new_password:
                if new_password and new_password != confirm_password:
                    error = "Passwords do not match!"
                    return render_template('settings.html', error=error, success=success, theme=session.get('theme', 'light'))

                user_update = {}
                if new_email:
                    existing_user = supabase.table('users').select('id').eq('email', new_email).neq('id', user_id).execute()
                    if existing_user.data:
                        error = "Email already in use by another account."
                        return render_template('settings.html', error=error, success=success, theme=session.get('theme', 'light'))
                    user_update['email'] = new_email
                    session['user_email'] = new_email

                if new_password:
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    user_update['password'] = hashed_password

                if user_update:
                    supabase.table('users').update(user_update).eq('id', user_id).execute()
                    logger.info(f"User {user_id} updated email/password.")

            two_factor_enabled = request.form.get('two_factor_enabled') == 'on'
            theme = request.form.get('theme')
            reminder_time = request.form.get('reminder_time')
            notification_preference = request.form.get('notification_preference')

            preferences_update = {
                'two_factor_enabled': two_factor_enabled,
                'theme': theme,
                'reminder_time': reminder_time,
                'notification_preference': notification_preference
            }
            supabase.table('user_preferences').update(preferences_update).eq('user_id', user_id).execute()
            logger.info(f"Preferences updated for user {user_id}: {preferences_update}")

            session['theme'] = theme
            session['two_factor_enabled'] = two_factor_enabled

            if two_factor_enabled:
                preferences = supabase.table('user_preferences')\
                    .select('two_factor_secret')\
                    .eq('user_id', user_id)\
                    .execute()
                if not preferences.data or not preferences.data[0]['two_factor_secret']:
                    return redirect(url_for('setup_2fa'))

            success = "Settings updated successfully!"
        except Exception as e:
            error = "Failed to update settings. Please try again."
            logger.error(f"Settings update error: {str(e)}")

    try:
        user_data = supabase.table('users').select('email').eq('id', user_id).execute()
        preferences_data = supabase.table('user_preferences')\
            .select('two_factor_enabled, theme, reminder_time, notification_preference')\
            .eq('user_id', user_id)\
            .execute()

        if not user_data.data or not preferences_data.data:
            error = "Unable to load settings."
            return render_template('settings.html', error=error, success=success, theme=session.get('theme', 'light'))

        user = user_data.data[0]
        preferences = preferences_data.data[0]
    except Exception as e:
        error = "Unable to load settings."
        logger.error(f"Settings load error: {str(e)}")
        return render_template('settings.html', error=error, success=success, theme=session.get('theme', 'light'))

    return render_template(
        'settings.html',
        email=user['email'],
        two_factor_enabled=preferences['two_factor_enabled'],
        reminder_time=preferences['reminder_time'],
        notification_preference=preferences['notification_preference'],
        error=error,
        success=success,
        theme=session.get('theme', 'light')
    )

@app.route('/logout')
def logout():
    if 'user' in session:
        user_email = session.get('user_email', 'Unknown')
        session.pop('user', None)
        session.pop('user_email', None)
        session.pop('last_activity', None)
        session.pop('theme', None)
        session.pop('2fa_verified', None)
        session.pop('two_factor_enabled', None)
        logger.info(f"User {user_email} logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)