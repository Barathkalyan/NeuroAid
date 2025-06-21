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
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://kkzymljvdzbydqugbwuw.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrenltbGp2ZHpieWRxdWdid3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5OTcyMzgsImV4cCI6MjA2MDU3MzIzOH0.d6Xb4PrfYlcilkLOGWbPIG2WZ2c2rocZZEKCojwWfgs')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrenltbGp2ZHpieWRxdWdid3V3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDk5NzIzOCwiZXhwIjoyMDYwNTczMjM4fQ.yuRT1q-FigehZoeFccdP_zk4m5sgHulpbg_us1IgpRw')  # Replace with actual service role key
HF_API_KEY = os.getenv('HF_API_KEY', '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')

# Initialize Supabase clients
supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_service: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

logger.info("Supabase clients initialized: anon_key and service_key")

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

def get_supabase(use_service_role=False):
    if use_service_role:
        if 'supabase_service' not in g:
            g.supabase_service = supabase_service
        return g.supabase_service
    else:
        if 'supabase_anon' not in g:
            g.supabase_anon = supabase_anon
        return g.supabase_anon
    
def get_user_dropdown_data(supabase, user_id):
    try:
        # Fetch email and created_date from users table
        user_data = supabase.table('users')\
            .select('email, created_date')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()
        
        # Fetch name from profiles table
        profile_data = supabase.table('profiles')\
            .select('name')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        user_name = profile_data.data[0]['name'] if profile_data.data and profile_data.data[0]['name'] else 'Unknown'
        email = user_data.data[0]['email'] if user_data.data else 'Not found'
        created_date = user_data.data[0]['created_date'] if user_data.data and user_data.data[0]['created_date'] else '2025-01-01'
        
        # Format created_date
        if created_date:
            if '.' in created_date:
                created_date = created_date.split('.')[0] + '+00:00'
            else:
                created_date = created_date.replace('Z', '+00:00')
            formatted_date = datetime.fromisoformat(created_date).astimezone(ZoneInfo("Asia/Kolkata")).strftime('%B %d, %Y')
        else:
            formatted_date = 'January 01, 2025'
        
        return {
            'user_name': user_name,
            'user_email': email,
            'joined_date': formatted_date
        }
    except Exception as e:
        logger.error(f"Error fetching dropdown data for user {user_id}: {str(e)}")
        return {
            'user_name': 'Unknown',
            'user_email': 'Not found',
            'joined_date': 'January 01, 2025'
        }

@app.teardown_appcontext
def teardown_supabase(exception):
    if 'supabase_anon' in g:
        g.pop('supabase_anon')
    if 'supabase_service' in g:
        g.pop('supabase_service')

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
            session.pop('two_factor_enabled', None)
            session.pop('2fa_verified', None)
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
            supabase.table('user_preferences').update({
                'two_factor_enabled': False,
                'two_factor_secret': None
            }).eq('user_id', user_id).execute()
            session['two_factor_enabled'] = False
            return render_template('setup_2fa.html', error="Failed to set up 2FA. Please try again.")
    
    try:
        preferences = supabase.table('user_preferences')\
            .select('two_factor_secret')\
            .eq('user_id', user_id)\
            .execute()
        
        if preferences.data and preferences.data[0].get('two_factor_secret'):
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
            
            if not preferences.data or not preferences.data[0].get('two_factor_secret'):
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
    
    try:
        preferences = supabase.table('user_preferences')\
            .select('two_factor_enabled, two_factor_secret')\
            .eq('user_id', user_id)\
            .execute()
        
        if not preferences.data or not preferences.data[0].get('two_factor_enabled') or not preferences.data[0].get('two_factor_secret'):
            supabase.table('user_preferences').update({
                'two_factor_enabled': False,
                'two_factor_secret': None
            }).eq('user_id', user_id).execute()
            session['two_factor_enabled'] = False
            return redirect(url_for('index'))
        
        return render_template('verify_2fa.html')
    except Exception as e:
        logger.error(f"Error checking 2FA status on verify: {str(e)}")
        return render_template('verify_2fa.html', error="Error checking 2FA status.")

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            error = 'Email and password are required.'
            return render_template('login.html', error=error), 400
        
        # Normalize email to lowercase for the query
        email = email.strip().lower()
        logger.info(f"Attempting login for email: {email}")
        
        # Use service role to bypass RLS for login
        supabase = get_supabase(use_service_role=True)
        try:
            user_response = supabase.table('users').select('id, email, password').eq('email', email).execute()
            logger.info(f"Supabase query response for email {email}: {user_response.data}")
            
            if not user_response.data:
                error = 'User not found.'
                return render_template('login.html', error=error), 401
            
            user = user_response.data[0]
            stored_password = user['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['user'] = str(user['id'])
                session['user_email'] = email
                session['last_activity'] = datetime.now(ZoneInfo("UTC")).isoformat()
                try:
                    preferences = supabase.table('user_preferences')\
                        .select('theme, two_factor_enabled, two_factor_secret')\
                        .eq('user_id', user['id'])\
                        .execute()
                    session['theme'] = preferences.data[0].get('theme', 'light') if preferences.data else 'light'
                    two_factor_enabled = preferences.data[0].get('two_factor_enabled', False) if preferences.data else False
                    two_factor_secret = preferences.data[0].get('two_factor_secret') if preferences.data else None
                    session['two_factor_enabled'] = two_factor_enabled
                    if two_factor_enabled and two_factor_secret:
                        return redirect(url_for('verify_2fa'))
                    logger.info(f"User {email} logged in successfully, user_id: {user['id']}, theme: {session['theme']}")
                    return redirect(url_for('index'))
                except Exception as e:
                    logger.error(f"Error fetching user preferences: {str(e)}")
                    session['theme'] = 'light'
                    session['two_factor_enabled'] = False
                    logger.info(f"User {email} logged in with default preferences, user_id: {user['id']}")
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

        # Normalize email to lowercase during signup
        email = email.strip().lower()
        logger.info(f"Attempting signup for email: {email}")

        # Use service role for signup to bypass RLS
        supabase = get_supabase(use_service_role=True)
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
    today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = utc_now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    suggestions = None
    recent_entries_data = []

    try:
        latest_entry_query = supabase.table('journal_entries')\
            .select('created_at, analysis')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)
        latest_entry = latest_entry_query.execute()

        if latest_entry.data:
            created_at_str = latest_entry.data[0]['created_at']
            if '.' in created_at_str:
                created_at_str = created_at_str.split('.')[0] + '+00:00'
            else:
                created_at_str = created_at_str.replace('Z', '+00:00')
            entry_date = datetime.fromisoformat(created_at_str).replace(tzinfo=ZoneInfo("UTC"))
            entry_date_ist = entry_date.astimezone(ZoneInfo("Asia/Kolkata"))
            current_date_ist = ist_now.date()

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
        recent_entries = recent_entries_query.execute()

        recent_entries_data = recent_entries.data if recent_entries.data else []
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

    # Fetch dropdown data
    dropdown_data = get_user_dropdown_data(supabase, user_id)

    return render_template('index.html', 
                          suggestions=suggestions, 
                          recent_entries=recent_entries_data, 
                          theme=session.get('theme', 'light'),
                          **dropdown_data)

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
                return render_template('Journal.html', 
                                      error="Failed to save entry.", 
                                      current_date=current_date, 
                                      theme=session.get('theme', 'light'),
                                      **get_user_dropdown_data(supabase, user_id))

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

        return render_template('Journal.html', 
                              entries=entries.data if entries.data else [], 
                              current_date=current_date, 
                              theme=session.get('theme', 'light'),
                              **get_user_dropdown_data(supabase, user_id))
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', 
                              error="Failed to load entries.", 
                              current_date=current_date, 
                              theme=session.get('theme', 'light'),
                              **get_user_dropdown_data(supabase, user_id))

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

    supabase = get_supabase()
    user_id = session['user']
    dropdown_data = get_user_dropdown_data(supabase, user_id)

    return render_template('progress.html', 
                          theme=session.get('theme', 'light'),
                          **dropdown_data)

@app.route('/vibe')
def vibe():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    supabase = get_supabase()
    user_id = session['user']
    dropdown_data = get_user_dropdown_data(supabase, user_id)

    return render_template('vibe.html', 
                          theme=session.get('theme', 'light'),
                          **dropdown_data)

@app.route('/gratitude')
def gratitude():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    supabase = get_supabase(use_service_role=True)  # Use service role to bypass RLS
    user_id = session['user']
    theme = session.get('theme', 'light')
    profile_info = {'profile_pic_url': None}

    try:
        # Fetch theme from user_preferences for consistency
        preferences_data = supabase.table('user_preferences')\
            .select('theme')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        if preferences_data.data:
            theme = preferences_data.data[0].get('theme', 'light')
            session['theme'] = theme  # Update session for consistency

        # Fetch profile data (for profile picture in dropdown)
        profile_data = supabase.table('profiles')\
            .select('profile_pic_url')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        if profile_data.data:
            profile_info['profile_pic_url'] = profile_data.data[0].get('profile_pic_url')
        else:
            logger.info(f"No profile found for user_id: {user_id}, creating a new profile")
            default_name = (session.get('user_email', 'user') or 'user').split('@')[0]
            supabase.table('profiles').insert({
                'user_id': user_id,
                'name': default_name,
                'username': f"@{default_name}"
            }).execute()

    except Exception as e:
        logger.error(f"Error fetching data for gratitude route for user_id {user_id}: {str(e)}")
        # Continue rendering with default values

    # Fetch dropdown data (includes user_name, user_email, joined_date)
    dropdown_data = get_user_dropdown_data(supabase, user_id)

    return render_template('gratitude.html',
                          theme=theme,
                          profile_data=profile_info,
                          **dropdown_data)

@app.route('/profile')
def profile():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return redirect(url_for('login'))

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return redirect(url_for('verify_2fa'))

    supabase = get_supabase()
    user_id = session['user']
    logger.info(f"Fetching profile for user_id: {user_id}")

    try:
        user_data = supabase.table('users')\
            .select('email')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()

        if not user_data.data:
            logger.error(f"No user found for user_id: {user_id}")
            return render_template('profile.html', 
                                  theme=session.get('theme', 'light'), 
                                  name='Unknown', 
                                  email='Not found', 
                                  username='@unknown', 
                                  profile_data={}, 
                                  completion_percentage=0, 
                                  completion_dasharray=0,
                                  **get_user_dropdown_data(supabase, user_id))

        user = user_data.data[0]
        email = user['email'] or 'Not found'

        profile_data = supabase.table('profiles')\
            .select('name, username, age, gender, location, preferred_language, primary_goal, engagement_frequency, preferred_activities, profile_pic_url')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()

        if profile_data.data:
            profile = profile_data.data[0]
            name = profile['name'] if profile['name'] else 'Unknown'
            username = profile['username'] if profile['username'] else '@unknown'
            profile_info = {
                'age': profile['age'],
                'gender': profile['gender'],
                'location': profile['location'],
                'preferred_language': profile['preferred_language'],
                'primary_goal': profile['primary_goal'],
                'engagement_frequency': profile['engagement_frequency'],
                'preferred_activities': profile['preferred_activities'] or [],
                'profile_pic_url': profile['profile_pic_url']
            }
        else:
            logger.info(f"No profile found for user_id: {user_id}, creating a new profile")
            default_name = email.split('@')[0]
            supabase.table('profiles').insert({'user_id': user_id, 'name': default_name, 'username': f"@{default_name}"}).execute()
            profile_data = supabase.table('profiles')\
                .select('name, username, age, gender, location, preferred_language, primary_goal, engagement_frequency, preferred_activities, profile_pic_url')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()
            profile = profile_data.data[0]
            name = profile['name']
            username = profile['username']
            profile_info = {
                'age': None,
                'gender': None,
                'location': None,
                'preferred_language': None,
                'primary_goal': None,
                'engagement_frequency': None,
                'preferred_activities': [],
                'profile_pic_url': None
            }

        required_fields = ['name', 'username', 'email']
        optional_fields = ['age', 'gender', 'location', 'preferred_language', 'primary_goal', 'engagement_frequency']
        activity_fields = ['preferred_activities']

        filled_required = 0
        for field in required_fields:
            value = locals().get(field)
            if field == 'email':
                if value and value != 'Not found':
                    filled_required += 1
            else:
                if value and value not in ['Unknown', '@unknown']:
                    filled_required += 1

        filled_optional = sum(1 for field in optional_fields if profile_info[field])
        filled_activities = 1 if profile_info['preferred_activities'] else 0
        total_fields = len(required_fields) + len(optional_fields) + len(activity_fields)
        filled_fields = filled_required + filled_optional + filled_activities
        completion_percentage = int((filled_fields / total_fields) * 100)
        completion_dasharray = round(276.46 * (completion_percentage / 100), 2)

        return render_template('profile.html', 
                              theme=session.get('theme', 'light'),
                              name=name,
                              email=email,
                              username=username,
                              profile_data=profile_info,
                              completion_percentage=completion_percentage,
                              completion_dasharray=completion_dasharray,
                              **get_user_dropdown_data(supabase, user_id))

    except Exception as e:
        logger.error(f"Error fetching profile data: {str(e)}")
        return render_template('profile.html', 
                              theme=session.get('theme', 'light'),
                              name='Unknown',
                              email='Not found',
                              username='@unknown',
                              profile_data={},
                              completion_percentage=0,
                              completion_dasharray=0,
                              **get_user_dropdown_data(supabase, user_id))


@app.route('/update_profile_field', methods=['POST'])
def update_profile_field():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    user_id = session['user']
    supabase = get_supabase()

    try:
        if field == 'email':
            # Update email in the users table
            response = supabase.table('users')\
                .update({'email': value})\
                .eq('id', user_id)\
                .execute()
            if response.data:
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': 'Failed to update email'}), 500
        elif field in ['name', 'username']:
            # Update name or username in the profiles table
            response = supabase.table('profiles')\
                .update({field: value})\
                .eq('user_id', user_id)\
                .execute()
            if response.data:
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': f'Failed to update {field}'}), 500
        else:
            return jsonify({'success': False, 'error': 'Invalid field'}), 400
    except Exception as e:
        logger.error(f"Error updating profile field {field}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    supabase = get_supabase()
    user_id = session['user']
    file = request.files.get('profile-pic')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    try:
        file_path = f"profiles/{user_id}/{uuid.uuid4()}.jpg"
        supabase.storage.from_('profile-pics').upload(file_path, file.read())
        url = supabase.storage.from_('profile-pics').get_public_url(file_path)
        supabase.table('profiles').update({'profile_pic_url': url}).eq('user_id', user_id).execute()
        return jsonify({'success': True, 'url': url}), 200
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/update_personal_details', methods=['POST'])
def update_personal_details():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    supabase = get_supabase()
    user_id = session['user']
    data = request.get_json()

    try:
        supabase.table('profiles').update({
            'age': data.get('age'),
            'gender': data.get('gender'),
            'location': data.get('location'),
            'preferred_language': data.get('preferred_language')
        }).eq('user_id', user_id).execute()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error updating personal details: {str(e)}")
        return jsonify({'error': 'Failed to update personal details'}), 500

@app.route('/update_mental_health_goals', methods=['POST'])
def update_mental_health_goals():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    supabase = get_supabase()
    user_id = session['user']
    data = request.get_json()

    try:
        supabase.table('profiles').update({
            'primary_goal': data.get('primary_goal'),
            'engagement_frequency': data.get('engagement_frequency'),
            'preferred_activities': data.get('preferred_activities')
        }).eq('user_id', user_id).execute()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error updating mental health goals: {str(e)}")
        return jsonify({'error': 'Failed to update mental health goals'}), 500


# Updated /settings route to use user_preferences table
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        return jsonify({'success': False, 'error': '2FA verification required'}), 401

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']
    profile_info = {
        'profile_pic_url': None,
        'two_factor_enabled': False,
        'theme': 'light',
        'reminder_time': '09:00',
        'notification_preference': 'email'
    }

    try:
        # Fetch user data
        user_data = supabase.table('users').select('email').eq('id', user_id).limit(1).execute()
        if not user_data.data:
            logger.error(f"No user found for user_id: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        email = user_data.data[0]['email']

        # Fetch profile data
        profile_data = supabase.table('profiles').select('name, profile_pic_url').eq('user_id', user_id).limit(1).execute()
        if profile_data.data:
            profile_info['profile_pic_url'] = profile_data.data[0].get('profile_pic_url')
        else:
            default_name = email.split('@')[0]
            supabase.table('profiles').insert({
                'user_id': user_id,
                'name': default_name,
                'username': f"@{default_name}"
            }).execute()

        # Fetch preferences
        preferences_data = supabase.table('user_preferences').select('two_factor_enabled, theme, reminder_time, notification_preference').eq('user_id', user_id).limit(1).execute()
        if preferences_data.data:
            profile_info.update(preferences_data.data[0])
        else:
            supabase.table('user_preferences').insert({
                'user_id': user_id,
                'language': 'tamil',
                'theme': 'light',
                'two_factor_enabled': False,
                'reminder_time': '09:00',
                'notification_preference': 'email'
            }).execute()

        if request.method == 'POST':
            try:
                new_email = request.form.get('email', email).strip().lower()
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                two_factor_enabled = request.form.get('two_factor_enabled') == 'on'
                theme = request.form.get('theme', profile_info['theme'])
                reminder_time = request.form.get('reminder_time', profile_info['reminder_time'])
                notification_preference = request.form.get('notification_preference', profile_info['notification_preference'])

                # Validate inputs
                if not new_email:
                    return jsonify({'success': False, 'error': 'Email is required'}), 400

                # Check if email already exists
                existing_user = supabase.table('users').select('id').eq('email', new_email).neq('id', user_id).execute()
                if existing_user.data:
                    return jsonify({'success': False, 'error': 'Email already exists'}), 400

                # Validate password
                if password and password != confirm_password:
                    return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

                # Update users table
                update_user_data = {'email': new_email}
                if password:
                    update_user_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                supabase.table('users').update(update_user_data).eq('id', user_id).execute()

                # Update preferences
                update_preferences_data = {
                    'two_factor_enabled': two_factor_enabled,
                    'theme': theme,
                    'reminder_time': reminder_time,
                    'notification_preference': notification_preference
                }
                supabase.table('user_preferences').update(update_preferences_data).eq('user_id', user_id).execute()

                # Update session
                session['user_email'] = new_email
                session['theme'] = theme
                session['two_factor_enabled'] = two_factor_enabled

                logger.info(f"Settings updated for user_id: {user_id}")
                return jsonify({'success': True, 'message': 'Settings updated successfully'})

            except Exception as e:
                logger.error(f"Error updating settings for user_id: {user_id}: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # GET request: Render template
        dropdown_data = get_user_dropdown_data(supabase, user_id)
        return render_template('settings.html',
                              email=email,
                              profile_data=profile_info,
                              two_factor_enabled=profile_info['two_factor_enabled'],
                              theme=profile_info['theme'],
                              reminder_time=profile_info['reminder_time'],
                              notification_preference=profile_info['notification_preference'],
                              error=None,
                              success=None,
                              **dropdown_data)

    except Exception as e:
        logger.error(f"Error in settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        # Fetch dropdown data
        dropdown_data = get_user_dropdown_data(supabase, user_id)

        # GET request or POST with error/success: Render the settings page
        return render_template('settings.html',
                              email=email,
                              profile_data=profile_info,
                              two_factor_enabled=profile_info['two_factor_enabled'],
                              theme=profile_info['theme'],
                              reminder_time=profile_info['reminder_time'],
                              notification_preference=profile_info['notification_preference'],
                              error=error,
                              success=success,
                              **dropdown_data)

    except Exception as e:
        logger.error(f"Error in settings: {str(e)}")
        return render_template('settings.html',
                              email='Not found',
                              profile_data=profile_info,
                              two_factor_enabled=False,
                              theme='light',
                              reminder_time='09:00',
                              notification_preference='email',
                              error='An error occurred while fetching settings',
                              success=None,
                              **get_user_dropdown_data(supabase, user_id))

# Updated /export_data route to include user_preferences
@app.route('/export_data', methods=['GET'])
def export_data():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']

    try:
        user_data = supabase.table('users')\
            .select('email')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()

        if not user_data.data:
            logger.error(f"No user found for user_id: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404

        profile_data = supabase.table('profiles')\
            .select('name, username, profile_pic_url, age, gender, location, preferred_language, primary_goal, engagement_frequency, preferred_activities, created_at, updated_at')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()

        preferences_data = supabase.table('user_preferences')\
            .select('language, theme, two_factor_enabled, reminder_time, notification_preference')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()

        export_data = {
            'user': {
                'email': user_data.data[0]['email'],
                'id': user_id
            },
            'profile': profile_data.data[0] if profile_data.data else {},
            'preferences': preferences_data.data[0] if preferences_data.data else {}
        }

        logger.info(f"Data exported for user_id: {user_id}")
        return jsonify({'success': True, 'data': export_data})

    except Exception as e:
        logger.error(f"Error exporting data for user_id: {user_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to export data'}), 500

# Updated /delete_account route to also delete user_preferences
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user' not in session:
        logger.info("User not logged in, redirecting to login.")
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']

    try:
        supabase.table('journal_entries').delete().eq('user_id', user_id).execute()
        supabase.table('gratitude_entries').delete().eq('user_id', user_id).execute()
        supabase.table('user_preferences').delete().eq('user_id', user_id).execute()
        supabase.table('profiles').delete().eq('user_id', user_id).execute()
        supabase.table('users').delete().eq('id', user_id).execute()

        session.clear()
        logger.info(f"Account deleted for user_id: {user_id}")
        return jsonify({'success': True, 'message': 'Account deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting account for user_id: {user_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete account'}), 500

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