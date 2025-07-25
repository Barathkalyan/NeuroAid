import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from supabase import create_client, Client
import bcrypt
import requests
from datetime import datetime, timedelta
import time
from zoneinfo import ZoneInfo
import uuid
import pyotp
import qrcode
from io import BytesIO
import base64
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
from threading import Thread
from dotenv import load_dotenv
from storage3.utils import StorageException
import uuid
import secrets
from flask import flash, redirect, render_template
from dotenv import load_dotenv
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = [
    'FLASK_SECRET_KEY',
    'SUPABASE_URL',
    'SUPABASE_ANON_KEY',
    'SUPABASE_SERVICE_KEY',
    'EMAIL_SENDER',
    'EMAIL_PASSWORD',
    'HUGGINGFACE_API_KEY',
    'PUBLIC_URL'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
print("🚀 Flask app started!")
logger.info("🔧 Logger is working!")
app.logger.setLevel(logging.INFO)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize Supabase clients
supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_service: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
logger.info("Supabase clients initialized: anon_key and service_key")

def huggingface_emotion_analysis(text):
    try:
        api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not api_key:
            logger.error("Hugging Face API key not found.")
            return [{"label": "neutral", "score": 0.5}]

        api_url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": text[:512]}  # Truncate to avoid API token limits
        logger.info(f"Sending to HF API: {payload['inputs']}")

        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"HF API response: {result}")

        if isinstance(result, list) and result:
            emotion_mapping = {
                'anger': 'anger',
                'disgust': 'anger',
                'fear': 'anxiety',
                'joy': 'joy',
                'neutral': 'neutral',
                'sadness': 'sadness',
                'surprise': 'neutral'
            }
            emotions = []
            for emotion in result[0]:
                label = emotion_mapping.get(emotion['label'], 'neutral')
                score = min(float(emotion['score']), 0.9)  # Cap score for consistency
                logger.debug(f"Processing emotion: {emotion['label']} -> {label}, score: {score}")
                if score > 0.1:  # Filter low-confidence emotions
                    emotions.append({"label": label, "score": score})

            # Simplify: return top emotions without aggregation to preserve primary emotion
            if not emotions:
                logger.warning("No significant emotions detected.")
                return [{"label": "neutral", "score": 0.5}]
            return sorted(emotions, key=lambda x: x['score'], reverse=True)[:3]  # Return top 3 emotions
        else:
            logger.warning(f"Unexpected API response format: {result}")
            return [{"label": "neutral", "score": 0.5}]
    except requests.exceptions.RequestException as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        return [{"label": "neutral", "score": 0.5}]
    except Exception as e:
        logger.error(f"Unexpected error in emotion analysis: {str(e)}")
        return [{"label": "neutral", "score": 0.5}]
    
def derive_mood_from_emotions(emotions):
    if not emotions:
        return 3, 0.5  # neutral mood, medium confidence

    positive_emotions = ['joy']
    negative_emotions = ['sadness', 'anger', 'anxiety']
    neutral_emotions = ['neutral']

    top_emotion = max(emotions, key=lambda x: x['score'])
    emotion_label = top_emotion['label']
    confidence = top_emotion['score']  # model's confidence

    if emotion_label in positive_emotions:
        mood_score = 5 if confidence > 0.7 else 4
        # keep confidence as-is for positive emotions
    elif emotion_label in negative_emotions:
        mood_score = 1 if confidence > 0.7 else 2
        confidence = round(1 - confidence, 2)  # invert confidence
    elif emotion_label in neutral_emotions:
        mood_score = 3
        confidence = 0.5  # fixed mid value for neutrality
    else:
        mood_score = 3
        confidence = 0.5  # fallback

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

SUGGESTION_TEMPLATES = {
    'sadness': [
        "When {tone} you’re feeling {emotion}, try writing about a memory that brings you comfort.",
        "Sometimes {tone} you’re feeling {emotion}, a short walk can help clear your mind.",
        "If {tone} you’re feeling {emotion}, listening to calming {language} music might soothe you.",
        "Consider this: {tone} you’re feeling {emotion}. Reflecting on gratitude may help.",
        "Feeling {emotion}? {tone} you can pause and try a simple breathing exercise: inhale for 4, hold for 4, exhale for 4.",
        "On days like this, {tone} you’re feeling {emotion}, cuddle up in a blanket and write to your future self.",
        "To cope when {tone} you’re feeling {emotion}, watch a comforting {language} movie or show you love.",
        "Bring back some joy — {tone} you’re feeling {emotion}, so try looking at nostalgic photos.",
        "Draw what’s on your mind. Even abstract lines help when {tone} you’re feeling {emotion}.",
        "Connection matters. If {tone} you’re feeling {emotion}, message someone who truly listens.",
        "Create a calm space. {tone} you’re feeling {emotion} — light a scented candle and reflect in silence.",
        "Give yourself care. When {tone} you’re feeling {emotion}, journal three things that make you feel safe."
    ],
    'anger': [
        "Capture your thoughts. {tone} you’re feeling {emotion}, so write what’s frustrating you.",
        "To release energy, {tone} you’re feeling {emotion} — try stretching or a few jumping jacks.",
        "Redirect intensity — {tone} you’re feeling {emotion}, so blast an energetic {language} playlist.",
        "Writing helps. {tone} you’re feeling {emotion}, so draft a letter to let go of this moment.",
        "Calm your racing mind. {tone} you’re feeling {emotion}, count backward slowly from 10.",
        "Physical release can help — if {tone} you’re feeling {emotion}, punch a pillow safely or squeeze it tight.",
        "Shock your system gently — {tone} you’re feeling {emotion}, wash your face with cold water.",
        "Feel grounded. {tone} you’re feeling {emotion}, so walk outside and name 5 things you see.",
        "Put it on paper — {tone} you’re feeling {emotion}, try furiously doodling your energy out.",
        "Gain perspective — {tone} you’re feeling {emotion}, rewrite the situation from a third-person view.",
        "Express it verbally — if {tone} you’re feeling {emotion}, finish this sentence 3 times: 'I feel angry because...'",
        "Cool down with a sensory reset — {tone} you’re feeling {emotion}, so hold ice and breathe slowly."
    ],
    'anxiety': [
        "Start with grounding. {tone} you’re feeling {emotion}, so name five things you see around you.",
        "Calm your thoughts. {tone} you’re feeling {emotion}, so try a guided {language} meditation.",
        "Ease your mind — if {tone} you’re feeling {emotion}, write about a safe imaginary place.",
        "Slow down — {tone} you’re feeling {emotion}, focus on deep breaths for just one minute.",
        "Simplify the moment — when {tone} you’re feeling {emotion}, jot down one thing you can control.",
        "Center yourself. {tone} you’re feeling {emotion}, try the 3-3-3 rule: 3 sights, 3 sounds, 3 movements.",
        "Less is more. {tone} you’re feeling {emotion}, create a tiny to-do list — 1 or 2 things max.",
        "Use your body to connect — {tone} you’re feeling {emotion}, place your hand on your chest and feel your breath.",
        "Externalize the worry — when {tone} you’re feeling {emotion}, give your anxiety a name and write about it.",
        "Affirm your safety. {tone} you’re feeling {emotion}, so repeat: 'I am safe. I am grounded. I am okay.'",
        "Soothing touch helps — if {tone} you’re feeling {emotion}, hold a warm mug and notice the warmth.",
        "Stretch out the tension. {tone} you’re feeling {emotion}, move gently while focusing on breath."
    ],
    'joy': [
        "Celebrate it! {tone} you’re feeling {emotion}, so do something fun like {activity}.",
        "Hold onto this moment — {tone} you’re feeling {emotion}, journal what’s making you smile.",
        "Amplify your mood — {tone} you’re feeling {emotion}, play an upbeat {language} playlist.",
        "Dream a little — {tone} you’re feeling {emotion}, write about a goal you’re excited about.",
        "Channel your energy — {tone} you’re feeling {emotion}, do a joyful sketch or doodle.",
        "Create a memory — {tone} you’re feeling {emotion}, take a photo or short video right now.",
        "Spread the light — {tone} you’re feeling {emotion}, message someone a kind or fun note.",
        "Celebrate your progress — when {tone} you’re feeling {emotion}, reflect on recent wins.",
        "Feel the rhythm — {tone} you’re feeling {emotion}, dance to your favorite {language} track.",
        "Record the joy — {tone} you’re feeling {emotion}, write a letter to your future self.",
        "Spice things up — when {tone} you’re feeling {emotion}, try something spontaneous or new.",
        "Make a joy toolkit — {tone} you’re feeling {emotion}, list things that always lift your spirits."
    ],
    'neutral': [
        "Today feels balanced. {tone} you’re feeling neutral — explore a fresh {activity} idea.",
        "Use this calm to wander — {tone} you’re steady, write about something you’re curious about.",
        "Add something new — {tone} you’re feeling neutral, listen to a short {language} podcast.",
        "Reflect on progress — {tone} your mood is calm, so think about a small win this week.",
        "Set gentle goals — {tone} you’re feeling neutral, what intention can you set right now?",
        "Let curiosity lead — {tone} your energy is steady, try a new song, quote, or recipe and reflect.",
        "Observe with awareness — {tone} you’re feeling neutral, breathe deeply and look around.",
        "Design your day — {tone} your mind is calm, so journal your ideal 24 hours.",
        "Feed your mind — {tone} you’re feeling neutral, watch a short {language} video that interests you.",
        "Tidy your space — {tone} your mood is even, declutter a small area around you.",
        "Reconnect — {tone} you’re feeling neutral, reach out to a friend you haven’t spoken to lately.",
        "Find inspiration — {tone} your mind is steady, read a page from a book and reflect on one idea."
    ]
}


ACTIVITY_MAPPINGS = {
    'meditation': [
        'A Mindfulness Meditation',
        'A Guided Breathing Session',
        'A Calming Visualization',
        'A Body Scan Meditation',
        'A Gratitude-Focused Meditation',
        'A Sound Bath Session',
        'A Five-Minute Silence Sit'
    ],
    'exercise': [
        'A Quick Workout',
        'A Short Run',
        'Some Yoga Stretches',
        'A Walk In Nature',
        'A Dance Session In Your Room',
        'A 7-Minute HIIT Routine',
        'A Few Sets Of Jumping Jacks Or Squats'
    ],
    'writing': [
        'Writing A Short Story',
        'Penning A Poem',
        'Writing A Letter To Your Future Self',
        'Brain-Dumping Whatever’s On Your Mind',
        'Composing A Gratitude List',
        'Creating A Bucket List Or Vision Board Entry',
        'Exploring Your Emotions Through Journaling'
    ],
    'music': [
        'Listening To Music',
        'Playing An Instrument',
        'Singing Along To A Song',
        'Exploring A New {language} Playlist',
        'Humming A Favorite Melody',
        'Trying A Music-Making App Or Tool',
        'Sitting With Headphones And Closing Your Eyes'
    ],
    'reading': [
        'Reading A Favorite Book',
        'Exploring A New Article',
        'Diving Into A Novel',
        'Reading A Comic Or Graphic Story',
        'Skimming A Blog Or Newsletter',
        'Revisiting An Inspiring Quote Or Poem',
        'Learning Something New From A How-To Guide'
    ],
    'mood-speech': [
        'Expressing Your Feelings Through Speech',
        'Recording A Voice Note About Your Mood',
        'Talking Aloud To Process Your Emotions',
        'Practicing A Mood-Affirming Monologue',
        'Speaking Your Thoughts Into A Recorder',
        'Sharing Your Mood With A Trusted Friend',
        'Using Voice To Release Your Feelings'
    ],
    'mindfulness': [
        'A Short Mindfulness Break',
        'Practicing Mindful Breathing',
        'A Guided Mindfulness Session',
        'A Mindful Walk Outside',
        'A Moment Of Mindful Observation'
    ]
}



def get_user_preferences(supabase, user_id):
    try:
        preferences = supabase.table('profiles')\
            .select('preferred_activities, primary_goal')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        if preferences.data:
            prefs = preferences.data[0]
            valid_activities = list(ACTIVITY_MAPPINGS.keys())
            activities = [act for act in prefs.get('preferred_activities', []) if act in valid_activities]
            if not activities:
                logger.warning(f"No valid preferred activities for user {user_id}, using defaults")
                activities = ['writing', 'meditation']  # Default activities
            return {'preferred_activities': activities, 'primary_goal': prefs.get('primary_goal', None)}
        else:
            logger.warning(f"No preferences found for user {user_id}, using defaults")
            return {'preferred_activities': ['writing', 'meditation'], 'primary_goal': None}
    except Exception as e:
        logger.error(f"Error fetching user preferences: {str(e)}")
        return {'preferred_activities': ['writing', 'meditation'], 'primary_goal': None}
    
def generate_activity_suggestions(supabase, user_id, mood_score):
    user_prefs = get_user_preferences(supabase, user_id)
    preferred_activities = user_prefs.get('preferred_activities', ['writing', 'meditation'])
    
    # Set a deterministic seed based on user_id and current date
    current_date = datetime.now(ZoneInfo("UTC")).date().isoformat()
    seed_value = hash(user_id + current_date)
    random.seed(seed_value)
    
    # Adjust activity selection based on mood
    mood_activity_map = {
        1: ['meditation', 'writing', 'mindfulness'],  # Very low mood
        2: ['meditation', 'writing', 'mindfulness', 'exercise'],  # Low mood
        3: ['writing', 'reading', 'music', 'mindfulness'],  # Neutral mood
        4: ['exercise', 'music', 'writing', 'mood-speech'],  # Good mood
        5: ['exercise', 'music', 'mood-speech', 'writing']  # Great mood
    }
    
    available_activities = [act for act in preferred_activities if act in mood_activity_map.get(mood_score, preferred_activities)]
    if not available_activities:
        available_activities = mood_activity_map.get(mood_score, ['writing', 'meditation'])
    
    selected_activities = random.sample(available_activities, min(2, len(available_activities)))
    activity_suggestions = [
        random.choice(ACTIVITY_MAPPINGS.get(act, ['a relaxing activity'])) for act in selected_activities
    ]
    
    logger.info(f"[ACTIVITY_SUGGESTIONS] user_id: {user_id}, mood: {mood_score}, activities: {activity_suggestions}")
    return activity_suggestions
    
def generate_suggestion(emotions, mood, supabase, user_id):
    if not emotions:
        return ["Try writing more to help me understand your feelings.", "Consider jotting down your thoughts to explore your emotions."]

    user_prefs = get_user_preferences(supabase, user_id)
    primary_goal = user_prefs.get('primary_goal', 'general well-being')

    language_prefs = supabase.table('user_preferences')\
        .select('language')\
        .eq('user_id', user_id)\
        .execute()
    language = language_prefs.data[0]['language'] if language_prefs.data else 'tamil'

    current_hour = datetime.now(ZoneInfo("Asia/Kolkata")).hour
    time_context = 'morning' if 5 <= current_hour < 12 else 'afternoon' if 12 <= current_hour < 17 else 'evening'

    journaling_freq = get_journaling_frequency(supabase, user_id)

    top_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)[:2]
    primary_emotion = top_emotions[0]['label']
    primary_score = top_emotions[0]['score']
    secondary_emotion = top_emotions[1]['label'] if len(top_emotions) > 1 else None

    def get_tone(mood, score):
        if score > 0.7:
            return "it seems"
        elif score > 0.4:
            return "it looks like"
        else:
            return "perhaps"

    suggestions = []
    emotion_key = primary_emotion
    if primary_emotion in ['gratitude', 'hope']:
        emotion_key = 'joy'
    available_templates = SUGGESTION_TEMPLATES.get(emotion_key, SUGGESTION_TEMPLATES['neutral'])

    dropdown_data = get_user_dropdown_data(supabase, user_id)
    user_name = dropdown_data.get('user_name', 'friend')
    session['user_name'] = user_name

    if primary_score > 0.7:
        template_weights = {t: 2 if 'try' in t.lower() or 'reflect' in t.lower() else 1 for t in available_templates}
    else:
        template_weights = {t: 1 for t in available_templates}

    templates = list(template_weights.keys())
    weights = list(template_weights.values())
    unique_templates = random.sample(templates, k=2)

    secondary_influence = False
    if secondary_emotion and len(top_emotions) > 1 and top_emotions[1]['score'] > 0.4:
        secondary_influence = True
        secondary_emotion_key = secondary_emotion
        if secondary_emotion in ['gratitude', 'hope']:
            secondary_emotion_key = 'joy'
        secondary_templates = SUGGESTION_TEMPLATES.get(secondary_emotion_key, SUGGESTION_TEMPLATES['neutral'])
        unique_templates[1] = random.choice(secondary_templates)

    tone1 = get_tone(mood, primary_score)
    tone2 = get_tone(mood, primary_score if not secondary_influence else top_emotions[1]['score'])

    suggestion1 = unique_templates[0].format(
        tone=tone1,
        emotion=primary_emotion.lower(),
        name=user_name,
        language=language
    )
    suggestion2 = unique_templates[1].format(
        tone=tone2,
        emotion=primary_emotion.lower() if not secondary_influence else secondary_emotion.lower(),
        name=user_name,
        language=language
    )
    suggestions.extend([suggestion1, suggestion2])

    while len(set(suggestions)) < 2:
        tone2 = get_tone(mood, primary_score if not secondary_influence else top_emotions[1]['score'])
        unique_templates = random.sample(templates, k=2)
        if secondary_influence:
            unique_templates[1] = random.choice(secondary_templates)
        suggestion2 = unique_templates[1].format(
            tone=tone2,
            emotion=primary_emotion.lower() if not secondary_influence else secondary_emotion.lower(),
            name=user_name,
            language=language
        )
        suggestions[1] = suggestion2

    if primary_goal:
        goal_suggestions = {
            'stress management': f"Since your goal is {primary_goal.lower()}, try a {time_context} relaxation technique.",
            'improved mood': f"To support your goal of {primary_goal.lower()}, reflect on a positive moment today.",
            'better sleep': f"With your goal of {primary_goal.lower()}, consider a {time_context} routine like journaling before bed.",
            'self-discovery': f"Your goal is {primary_goal.lower()}. Reflect on a recent experience that taught you something new."
        }
        goal_suggestion = goal_suggestions.get(primary_goal.lower(), f"Your goal is {primary_goal.lower()}. Try reflecting to stay aligned.")
        if goal_suggestion not in suggestions and len(suggestions) < 2:
            suggestions.append(goal_suggestion)

    if journaling_freq < 3 and len(suggestions) < 2:
        freq_suggestion = f"Journaling helps with {primary_goal or 'self-reflection'}. Try writing daily this week!"
        if freq_suggestion not in suggestions:
            suggestions.append(freq_suggestion)

    random.shuffle(suggestions)
    logger.info(f"[SUGGESTIONS] user_id: {user_id}")
    logger.info(f"[SUGGESTIONS] final suggestions: {suggestions}")

    return suggestions[:2]

def analyze_journal_entry(text, supabase, user_id):
    print("🔍 analyze_journal_entry was called")
    emotions = huggingface_emotion_analysis(text)
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
        user_data = supabase.table('users')\
            .select('email, created_date')\
            .eq('id', user_id)\
            .limit(1)\
            .execute()
        
        profile_data = supabase.table('profiles')\
            .select('name, profile_pic_url')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        
        user_name = profile_data.data[0]['name'] if profile_data.data and profile_data.data[0]['name'] else None
        profile_pic_url = profile_data.data[0]['profile_pic_url'] if profile_data.data and profile_data.data[0].get('profile_pic_url') else 'https://randomuser.me/api/portraits/men/32.jpg'
        email = user_data.data[0]['email'] if user_data.data else 'Not found'
        created_date = user_data.data[0]['created_date'] if user_data.data and user_data.data[0]['created_date'] else '2025-01-01'
        
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
            'joined_date': formatted_date,
            'profile_pic_url': profile_pic_url
        }
    except Exception as e:
        logger.error(f"Error fetching dropdown data for user {user_id}: {str(e)}")
        return {
            'user_name': None,
            'user_email': 'Not found',
            'joined_date': 'January 01, 2025',
            'profile_pic_url': 'https://randomuser.me/api/portraits/men/32.jpg'
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
                mood = entry['analysis'].get('mood', 3) if entry.get('analysis') else 3
                confidence = entry['analysis'].get('confidence', 0.0) if entry.get('analysis') else 0.0
                date_map[date_str]['moods'].append(mood)
                date_map[date_str]['confidences'].append(confidence)

        for date_str in date_map:
            moods = date_map[date_str]['moods']
            confidences = date_map[date_str]['confidences']
            avg_mood = sum(moods) / len(moods) if moods else 3
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            mood_data.append(round(avg_mood, 2))
            confidence_data.append(round(avg_confidence, 2))

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

        while current_date in entry_dates:
            streak += 1
            current_date -= timedelta(days=1)

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
        return jsonify({
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'data': [3] * 7,
            'numEntries': 0,
            'streak': 0,
            'confidence': [0] * 7
        }), 200

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
                1: 'https://open.spotify.com/embed/playlist/7ttDLBXnJ3X9gVTNPevjsH',
                2: 'https://open.spotify.com/embed/playlist/1MydE04FsRKKs3dzFd3mmt',
                3: 'https://open.spotify.com/embed/playlist/2f8Jr34CAALmHJ6LY22GoJ',
                4: 'https://open.spotify.com/embed/playlist/5LCntABX1VKtTWtnj7TMLd',
                5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX0nA91dV2ts4'
            },
            'english': {
                1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX3rxVfibe1L0', 
                2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX4fpCWaHOned',  
                3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX70RN3TfWWJh',  
                4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXdPec7aLTmlC',  
                5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXaXB8fQg7xif',  
            },
            'telugu': {
                1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXLeA8Omikj7',
                2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXapHi7gXtXo2',
                3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXdbXrPNafg9d',
                4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXaKIA8E7WcJj',
                5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DWXi7h5CniH97'
            },
            'malayalam': {
                1: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXbL0D4VxV2FY',
                2: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX9d5Vq9NrTzR',
                3: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX9qNs32fujYe',
                4: 'https://open.spotify.com/embed/playlist/37i9dQZF1DX1SpT6G94GFC',
                5: 'https://open.spotify.com/embed/playlist/37i9dQZF1DXa2PvUpywmrr'
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
    if 'user' not in session or not session.get('wants_2fa'):
        return redirect(url_for('settings'))

    supabase = get_supabase()
    user_id = session['user']

    try:
        if request.method == 'POST':
            # Check if already exists
            preferences = supabase.table('user_preferences')\
                .select('two_factor_secret')\
                .eq('user_id', user_id)\
                .limit(1).execute()

            if preferences.data and preferences.data[0].get('two_factor_secret'):
                return jsonify({'success': False, 'error': '2FA already setup'})

            # Generate and save secret
            totp = pyotp.TOTP(pyotp.random_base32())
            secret = totp.secret
            supabase.table('user_preferences').update({
                'two_factor_secret': secret,
                'two_factor_enabled': True
            }).eq('user_id', user_id).execute()

            session['two_factor_enabled'] = True

            provisioning_uri = totp.provisioning_uri(
                name=session['user_email'],
                issuer_name='NeuroAid'
            )
            img = qrcode.make(provisioning_uri)
            buffered = BytesIO()
            img.save(buffered)
            qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return jsonify({'success': True, 'message': '2FA setup successfully', 'qr_code': qr_code, 'secret': secret})

        # GET request fallback
        preferences = supabase.table('user_preferences')\
            .select('two_factor_secret')\
            .eq('user_id', user_id)\
            .limit(1).execute()

        if preferences.data and preferences.data[0].get('two_factor_secret'):
            return redirect(url_for('verify_2fa'))

        return render_template('setup_2fa.html')

    except Exception as e:
        logger.error(f"Error setting up 2FA: {str(e)}")
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Failed to generate QR code'})
        return render_template('setup_2fa.html', error="Error checking 2FA setup.")



@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'user' not in session:
        logger.info(f"User not logged in, redirecting to login at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return redirect(url_for('login'))

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']

    try:
        preferences_data = supabase.table('user_preferences').select('two_factor_enabled, two_factor_secret, theme').eq('user_id', user_id).limit(1).execute()
        if not preferences_data.data or not preferences_data.data[0]['two_factor_enabled']:
            return redirect(url_for('index'))

        two_factor_secret = preferences_data.data[0]['two_factor_secret']
        theme = preferences_data.data[0].get('theme', session.get('theme', 'light'))  # Fallback to session or default 'light'

        if not two_factor_secret:
            return redirect(url_for('setup_2fa'))

        if request.method == 'POST':
            totp_code = request.form.get('totp_code')
            if not totp_code:
                return render_template('verify_2fa.html', error='Please enter a TOTP code.', theme=theme)

            totp = pyotp.TOTP(two_factor_secret)
            if totp.verify(totp_code):
                session['2fa_verified'] = True
                logger.info(f"2FA verified for user_id: {user_id}")

                # Check if user is disabling 2FA
                if session.pop('wants_to_disable_2fa', False):
                    supabase.table('user_preferences').update({
                        'two_factor_enabled': False,
                        'two_factor_secret': None
                    }).eq('user_id', user_id).execute()
                    session['two_factor_enabled'] = False
                    flash('Two-Factor Authentication has been disabled.', 'success')
                    return redirect(url_for('settings'))

                return redirect(url_for('index'))

            else:
                return render_template('verify_2fa.html', error='Invalid TOTP code.', theme=theme)

        return render_template('verify_2fa.html', error=None, success=None, theme=theme)
    

    except Exception as e:
        logger.error(f"Error in verify_2fa for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}: {str(e)}")
        return render_template('verify_2fa.html', error='Error checking 2FA status.', theme=session.get('theme', 'light'))

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            error = 'Email and password are required.'
            return render_template('login.html', error=error, success=success), 400
        
        email = email.strip().lower()
        logger.info(f"Attempting login for email: {email}")
        
        supabase = get_supabase(use_service_role=True)
        try:
            user_response = supabase.table('users').select('id, email, password, is_verified').eq('email', email).execute()
            logger.info(f"Supabase query response for email {email}: {user_response.data}")
            
            if not user_response.data:
                error = 'User not found.'
                return render_template('login.html', error=error, success=success), 401
            
            user = user_response.data[0]
            if not user['is_verified']:
                error = 'Please verify your email before logging in.'
                return render_template('login.html', error=error, success=success), 403

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
                return render_template('login.html', error=error, success=success), 401
        except Exception as e:
            error = 'Unable to log in right now. Please try again later.'
            logger.error(f"Login error: {str(e)}")
            return render_template('login.html', error=error, success=success), 500
    return render_template('login.html', error=error, success=success)

import traceback  # Ensure this is at the top of app.py

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            error = 'Email, password, and confirm password are required.'
            logger.error(f"Signup failed: Missing required fields for email: {email}")
            return render_template('signup.html', error=error, success=success), 400

        if password != confirm_password:
            error = 'Passwords do not match!'
            logger.error(f"Signup failed: Passwords do not match for email: {email}")
            return render_template('signup.html', error=error, success=success), 400

        email = email.strip().lower()
        logger.info(f"Attempting signup for email: {email}")

        supabase = get_supabase(use_service_role=True)
        try:
            # Check for existing user
            existing_user = supabase.table('users').select('id').eq('email', email).execute()
            logger.debug(f"Existing user check response: {existing_user.data}")
            if existing_user.data:
                error = 'Email already exists.'
                logger.error(f"Signup failed: Email already exists: {email}")
                return render_template('signup.html', error=error, success=success), 400

            user_id = str(uuid.uuid4())
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            verification_token = secrets.token_urlsafe(32)
            expires_at = (datetime.now(ZoneInfo("UTC")) + timedelta(hours=24)).isoformat()

            # Insert user
            user_data = {
                'id': user_id,
                'email': email,
                'password': hashed_password,
                'is_verified': False
            }
            logger.debug(f"Inserting user data: {user_data}")
            supabase.table('users').insert(user_data).execute()

            # Insert verification token
            verification_data = {
                'user_id': user_id,
                'token': verification_token,
                'expires_at': expires_at
            }
            logger.debug(f"Inserting verification data: {verification_data}")
            supabase.table('email_verifications').insert(verification_data).execute()

            # Send verification email
            base_url = os.getenv('PUBLIC_URL', request.url_root.rstrip('/'))
            verification_link = f"{base_url}/verify_email?token={verification_token}"
            logger.info(f"Generated verification link: {verification_link}")
            email_body = f"""
            Hi,

            Thank you for signing up with NeuroAid! Please verify your email by clicking the link below:
            {verification_link}

            This link will expire in 24 hours. If you didn't sign up, please ignore this email.

            Best,
            The NeuroAid Team
            """
            if send_email(email, "NeuroAid Email Verification", email_body):
                logger.info(f"Verification email sent to {email}")
                success = 'Signup successful! Please check your email to verify your account.'
                return render_template('signup.html', error=None, success=success), 200
            else:
                # Rollback user creation if email fails
                supabase.table('users').delete().eq('id', user_id).execute()
                error = 'Failed to send verification email. Please try again.'
                logger.error(f"Failed to send verification email to {email}")
                return render_template('signup.html', error=error, success=success), 500

            # Insert user preferences
            preferences_data = {
                'user_id': user_id,
                'two_factor_enabled': False,
                'two_factor_secret': None,
                'theme': 'light',
                'reminder_time': '09:00',
                'notification_preference': 'email',
                'language': 'tamil'
            }
            logger.debug(f"Inserting preferences data: {preferences_data}")
            supabase.table('user_preferences').insert(preferences_data).execute()

            logger.info(f"User {email} signed up successfully with user_id: {user_id}")
            return redirect(url_for('login'))
        except Exception as e:
            error = 'Unable to sign up right now. Please try again later.'
            logger.error(f"Signup error: {str(e)}, Type: {type(e).__name__}, Traceback: {traceback.format_exc()}")
            return render_template('signup.html', error=error, success=success), 400

    return render_template('signup.html', error=error, success=success)

@app.route('/verify_email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    error = None
    success = None
    if not token:
        error = 'Invalid or missing verification token.'
        return render_template('verify_email.html', error=error, success=success), 400

    supabase = get_supabase(use_service_role=True)
    try:
        verification = supabase.table('email_verifications')\
            .select('user_id, expires_at, verified')\
            .eq('token', token)\
            .execute()

        if not verification.data or verification.data[0]['verified']:
            error = 'Invalid or already used verification token.'
            return render_template('verify_email.html', error=error, success=success), 400

        expires_at = verification.data[0]['expires_at']
        if '.' in expires_at:
            expires_at = expires_at.split('.')[0] + '+00:00'
        else:
            expires_at = expires_at.replace('Z', '+00:00')
        expiry_date = datetime.fromisoformat(expires_at).replace(tzinfo=ZoneInfo("UTC"))
        if datetime.now(ZoneInfo("UTC")) > expiry_date:
            error = 'Verification token has expired.'
            return render_template('verify_email.html', error=error, success=success), 400

        user_id = verification.data[0]['user_id']
        supabase.table('users').update({'is_verified': True}).eq('id', user_id).execute()
        supabase.table('email_verifications').update({'verified': True}).eq('token', token).execute()

        logger.info(f"Email verified for user_id: {user_id}")
        success = 'Email verified successfully! You can now log in.'
        return render_template('verify_email.html', error=error, success=success)
    except Exception as e:
        logger.error(f"Error verifying email with token {token}: {str(e)}")
        error = 'Unable to verify email. Please try again later.'
        return render_template('verify_email.html', error=error, success=success), 500
    
@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    email = request.form.get('email')
    error = None
    success = None
    if not email:
        error = 'Email is required.'
        return render_template('login.html', error=error, success=success), 400

    email = email.strip().lower()
    supabase = get_supabase(use_service_role=True)
    try:
        user_response = supabase.table('users').select('id, is_verified').eq('email', email).execute()
        if not user_response.data:
            error = 'Email not found.'
            return render_template('login.html', error=error, success=success), 404

        user = user_response.data[0]
        if user['is_verified']:
            error = 'Email is already verified.'
            return render_template('login.html', error=error, success=success), 400

        user_id = user['id']
        verification_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(ZoneInfo("UTC")) + timedelta(hours=24)).isoformat()

        # Delete any existing verification tokens for this user
        supabase.table('email_verifications').delete().eq('user_id', user_id).execute()

        # Insert new verification token
        verification_data = {
            'user_id': user_id,
            'token': verification_token,
            'expires_at': expires_at
        }
        supabase.table('email_verifications').insert(verification_data).execute()

        # Send verification email
        base_url = os.getenv('PUBLIC_URL', request.url_root.rstrip('/'))
        verification_link = f"{base_url}/verify_email?token={verification_token}"
        logger.info(f"Generated verification link: {verification_link}")
        email_body = f"""
        Hi,

        Please verify your NeuroAid account by clicking the link below:
        {verification_link}

        This link will expire in 24 hours. If you didn't request this, please ignore this email.

        Best,
        The NeuroAid Team
        """
        if send_email(email, "NeuroAid Email Verification", email_body):
            logger.info(f"Verification email resent to {email}")
            success = 'Verification email resent. Please check your email.'
            return render_template('login.html', error=error, success=success), 200
        else:
            logger.error(f"Failed to resend verification email to {email}")
            error = 'Failed to resend verification email.'
            return render_template('login.html', error=error, success=success), 500
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        error = 'Unable to resend verification email.'
        return render_template('login.html', error=error, success=success), 500

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
    mood_description = "Neutral"
    activities = []

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
                analysis = latest_entry.data[0]['analysis']
                suggestions = analysis.get('suggestions', [])
                mood_score = analysis.get('mood', 3)
                mood_descriptions = {
                    1: "Very Low",
                    2: "Low",
                    3: "Neutral",
                    4: "Good",
                    5: "Great"
                }
                mood_description = mood_descriptions.get(mood_score, "Neutral")
                activities = generate_activity_suggestions(supabase, user_id, mood_score)
            else:
                suggestions = ["Write a journal entry for today!"]
                activities = generate_activity_suggestions(supabase, user_id, 3)  # Default to neutral mood
        else:
            suggestions = ["Write a journal entry to get suggestions!"]
            activities = generate_activity_suggestions(supabase, user_id, 3)  # Default to neutral mood

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
        activities = ["Try a relaxing activity.", "Consider a short mindfulness session."]
        recent_entries_data = []

    dropdown_data = get_user_dropdown_data(supabase, user_id)

    return render_template('index.html', 
                          suggestions=suggestions, 
                          recent_entries=recent_entries_data, 
                          theme=session.get('theme', 'light'),
                          mood_description=mood_description,
                          activities=activities,
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
    suggestions = []

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
                suggestions = analysis.get('suggestions', ["Write another entry to get more suggestions!"])
                # Redirect to avoid form resubmission, but pass suggestions via session or query
                session['latest_suggestions'] = suggestions
                return redirect(url_for('journal'))
            except Exception as e:
                logger.error(f"Journal save error: {str(e)}")
                return render_template('Journal.html', 
                                      error="Failed to save entry.", 
                                      current_date=current_date, 
                                      theme=session.get('theme', 'light'),
                                      entries=[],
                                      suggestions=[],
                                      **get_user_dropdown_data(supabase, user_id))

    try:
        # Fetch latest suggestions from session or database
        suggestions = session.pop('latest_suggestions', []) if 'latest_suggestions' in session else []
        if not suggestions:
            latest_entry_query = supabase.table('journal_entries')\
                .select('analysis->suggestions')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            if latest_entry_query.data and 'suggestions' in latest_entry_query.data[0]:
                suggestions = latest_entry_query.data[0]['suggestions']

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
                              suggestions=suggestions,
                              **get_user_dropdown_data(supabase, user_id))
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', 
                              error="Failed to load entries.", 
                              current_date=current_date, 
                              theme=session.get('theme', 'light'),
                              entries=[],
                              suggestions=[],
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

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']
    theme = session.get('theme', 'light')
    profile_info = {'profile_pic_url': None}

    try:
        preferences_data = supabase.table('user_preferences')\
            .select('theme')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        if preferences_data.data:
            theme = preferences_data.data[0].get('theme', 'light')
            session['theme'] = theme

        profile_data = supabase.table('profiles')\
            .select('profile_pic_url, name')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()
        if profile_data.data:
            profile_info['profile_pic_url'] = profile_data.data[0].get('profile_pic_url')
        else:
            logger.info(f"No profile found for user_id: {user_id}, creating a new profile")
            supabase.table('profiles').insert({
                'user_id': user_id,
                'name': None,
                'username': f"@{session.get('user_email', 'user').split('@')[0]}"
            }).execute()

    except Exception as e:
        logger.error(f"Error fetching data for gratitude route for user_id {user_id}: {str(e)}")

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

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user' not in session:
        logger.warning("Unauthorized access attempt to /upload_profile_pic")
        return jsonify({'error': 'Unauthorized'}), 401

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']
    file = request.files.get('profile-pic')

    if not file:
        logger.info(f"No file uploaded for user_id: {user_id}")
        return jsonify({'error': 'No file uploaded'}), 400

    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    max_size = 5 * 1024 * 1024  # 5MB limit
    if file.mimetype not in allowed_types:
        logger.info(f"Invalid file type {file.mimetype} for user_id: {user_id}")
        return jsonify({'error': 'Invalid file type. Only JPEG, PNG, GIF, and WEBP are allowed'}), 400

    file_content = file.read()
    if len(file_content) > max_size:
        logger.info(f"File size {len(file_content)} exceeds limit for user_id: {user_id}")
        return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400

    file_extension = file.mimetype.split('/')[-1]
    if file_extension == 'jpeg':
        file_extension = 'jpg'
    file_path = f"profiles/{user_id}/{uuid.uuid4()}.{file_extension}"

    try:
        supabase.storage.from_('profile-pics').upload(file_path, file_content, {'content-type': file.mimetype})
        file_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/profile-pics/{file_path}"
        supabase.table('profiles').update({'profile_pic_url': file_url}).eq('user_id', user_id).execute()

        logger.info(f"Profile picture uploaded successfully for user_id: {user_id}, url: {file_url}")
        return jsonify({'success': True, 'url': file_url}), 200
    except StorageException as e:
        logger.error(f"Storage error uploading profile picture for user_id: {user_id}: {str(e)}")
        if 'Bucket not found' in str(e):
            return jsonify({'error': 'Storage bucket not found. Contact support.'}), 500
        return jsonify({'error': 'Failed to upload profile picture due to storage error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error uploading profile picture for user_id: {user_id}: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

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
            response = supabase.table('users')\
                .update({'email': value})\
                .eq('id', user_id)\
                .execute()
            if response.data:
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': 'Failed to update email'}), 500
        elif field in ['name', 'username']:
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

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        logger.info(f"User not logged in, redirecting to login at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    if session.get('two_factor_enabled') and not session.get('2fa_verified'):
        if request.endpoint not in ['setup_2fa', 'verify_2fa', 'static']:
            return redirect(url_for('verify_2fa'))

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
        user_data = supabase.table('users').select('email').eq('id', user_id).limit(1).execute()
        if not user_data.data:
            logger.error(f"No user found for user_id: {user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        email = user_data.data[0]['email']

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

        preferences_data = supabase.table('user_preferences')\
            .select('two_factor_enabled, two_factor_secret, theme, reminder_time, notification_preference')\
            .eq('user_id', user_id).limit(1).execute()
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

        current_time_ist = datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%I:%M %p IST')

        if request.method == 'POST':
            try:
                new_email = request.form.get('email', email).strip().lower()
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                two_factor_enabled = request.form.get('two_factor_enabled') == 'on'
                theme = request.form.get('theme', profile_info['theme'])
                reminder_time = request.form.get('reminder_time', profile_info['reminder_time'])
                notification_preference = request.form.get('notification_preference', profile_info['notification_preference'])

                disable_2fa_requested = not two_factor_enabled and profile_info['two_factor_enabled']

                if not new_email:
                    return jsonify({'success': False, 'error': 'Email is required'}), 400

                existing_user = supabase.table('users').select('id').eq('email', new_email).neq('id', user_id).execute()
                if existing_user.data:
                    return jsonify({'success': False, 'error': 'Email already exists'}), 400

                if password and password != confirm_password:
                    return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

                update_user_data = {'email': new_email}
                if password:
                    update_user_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                supabase.table('users').update(update_user_data).eq('id', user_id).execute()

                update_preferences_data = {
                    'theme': theme,
                    'reminder_time': reminder_time,
                    'notification_preference': notification_preference
                }

                # Enable 2FA
                if two_factor_enabled and not profile_info['two_factor_enabled']:
                    session['wants_2fa'] = True
                    session['user_email'] = new_email
                    session['theme'] = theme
                    session['two_factor_enabled'] = True
                    return redirect(url_for('setup_2fa'))

                # Disable 2FA (with verification)
                if disable_2fa_requested:
                    submitted_totp = request.form.get('disable_2fa_code', '').strip()
                    secret_check = preferences_data.data[0].get('two_factor_secret')

                    if not submitted_totp:
                        return jsonify({'success': False, 'error': 'TOTP code is required to disable 2FA'}), 400
                    if not secret_check:
                        return jsonify({'success': False, 'error': '2FA secret not found'}), 400

                    totp = pyotp.TOTP(secret_check)
                    if not totp.verify(submitted_totp):
                        return jsonify({'success': False, 'error': 'Invalid TOTP code'}), 400

                    update_preferences_data['two_factor_enabled'] = False
                    update_preferences_data['two_factor_secret'] = None
                    session.pop('2fa_verified', None)
                    session['two_factor_enabled'] = False
                    flash('Two-factor authentication disabled successfully.', 'info')

                supabase.table('user_preferences').update(update_preferences_data).eq('user_id', user_id).execute()

                session['user_email'] = new_email
                session['theme'] = theme

                logger.info(f"Settings updated for user_id: {user_id} at {current_time_ist}")
                return jsonify({'success': True, 'message': 'Settings updated successfully'})

            except Exception as e:
                logger.error(f"Error updating settings for user_id: {user_id} at {current_time_ist}: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

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
                              current_time=current_time_ist,
                              **dropdown_data)

    except Exception as e:
        logger.error(f"Error in settings route: {str(e)}")
        dropdown_data = get_user_dropdown_data(supabase, user_id)
        return render_template('settings.html',
                              email='Not found',
                              profile_data=profile_info,
                              two_factor_enabled=False,
                              theme='light',
                              reminder_time='09:00',
                              notification_preference='email',
                              error='An error occurred while fetching settings',
                              success=None,
                              current_time=datetime.now(ZoneInfo("Asia/Kolkata")).strftime('%I:%M %p IST'),
                              **dropdown_data)


@app.route('/export_data', methods=['GET'])
def export_data():
    if 'user' not in session:
        logger.info(f"User not logged in, redirecting to login at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    supabase = get_supabase(use_service_role=True)
    user_id = session['user']

    try:
        user_data = supabase.table('users').select('email').eq('id', user_id).limit(1).execute()
        if not user_data.data:
            logger.error(f"No user found for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
            return jsonify({'success': False, 'error': 'User not found'}), 404

        profile_data = supabase.table('profiles').select('name, username, profile_pic_url, age, gender, location, preferred_language, primary_goal, engagement_frequency, preferred_activities, created_at, updated_at').eq('user_id', user_id).limit(1).execute()
        preferences_data = supabase.table('user_preferences').select('language, theme, two_factor_enabled, reminder_time, notification_preference').eq('user_id', user_id).limit(1).execute()

        export_data = {
            'user': {
                'email': user_data.data[0]['email'],
                'id': user_id
            },
            'profile': profile_data.data[0] if profile_data.data else {},
            'preferences': preferences_data.data[0] if preferences_data.data else {}
        }

        logger.info(f"Data exported for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return jsonify({'success': True, 'data': export_data})

    except Exception as e:
        logger.error(f"Error exporting data for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to export data'}), 500

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user' not in session:
        logger.info(f"User not logged in, redirecting to login at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
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
        logger.info(f"Account deleted for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return jsonify({'success': True, 'message': 'Account deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting account for user_id: {user_id} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete account'}), 500
    

scheduler= None

@app.route('/logout')
def logout():
    if 'user' in session:
        user_email = session.get('user_email', 'Unknown')
        logout_time = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST on %B %d, %Y')
        session.pop('user', None)
        session.pop('user_email', None)
        session.pop('last_activity', None)
        session.pop('theme', None)
        session.pop('2fa_verified', None)
        session.pop('two_factor_enabled', None)
        logger.info(f"User {user_email} logged out at {logout_time}")
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            error = 'Email is required.'
            return render_template('forgot_password.html', error=error, success=success), 400

        email = email.strip().lower()
        logger.info(f"Password reset requested for email: {email}")

        supabase = get_supabase(use_service_role=True)
        try:
            user_response = supabase.table('users').select('id, email').eq('email', email).execute()
            if not user_response.data:
                error = 'Email not found.'
                return render_template('forgot_password.html', error=error, success=success), 404

            user = user_response.data[0]
            reset_token = secrets.token_urlsafe(32)
            expires_at = (datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)).isoformat()

            supabase.table('password_resets').insert({
                'user_id': user['id'],
                'token': reset_token,
                'expires_at': expires_at
            }).execute()

            base_url = os.getenv('PUBLIC_URL', request.url_root.rstrip('/'))
            reset_link = f"{base_url}/reset_password/{reset_token}"
            logger.info(f"Generated password reset link: {reset_link}")
            email_body = f"""
            Hi,
            
            You requested a password reset for your NeuroAid account. Click the link below to reset your password:
            {reset_link}
            
            This link will expire in 1 hour. If you didn't request this, please ignore this email.
            
            Best,
            The NeuroAid Team
            """
            if send_email(email, "NeuroAid Password Reset", email_body):
                success = 'Password reset link sent to your email.'
                logger.info(f"Password reset email sent to {email}")
                return render_template('forgot_password.html', error=error, success=success), 200

            else:
                logger.error(f"Failed to send password reset email to {email}")
                error = 'Failed to send password reset email.'
                return render_template('forgot_password.html', error=error, success=success), 500

        except Exception as e:
            logger.error(f"Error processing password reset for {email}: {str(e)}")
            error = 'Unable to process request. Please try again later.'
            return render_template('forgot_password.html', error=error, success=success), 500

    return render_template('forgot_password.html', error=error, success=success)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    error = None
    success = None
    supabase = get_supabase(use_service_role=True)

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            error = 'New password and confirm password are required.'
            logger.error(f"Password reset failed: Missing required fields")
            return render_template('reset_password.html', error=error, success=success, token=token), 400

        if password != confirm_password:
            error = 'Passwords do not match.'
            logger.error(f"Password reset failed: Passwords do not match")
            return render_template('reset_password.html', error=error, success=success, token=token), 400

        try:
            # Verify the reset token
            reset_data = supabase.table('password_resets')\
                .select('user_id, expires_at, used')\
                .eq('token', token)\
                .execute()

            if not reset_data.data or reset_data.data[0]['used']:
                error = 'Invalid or already used reset token.'
                logger.error(f"Password reset failed: Invalid or used token: {token}")
                return render_template('reset_password.html', error=error, success=success, token=token), 400

            expires_at = reset_data.data[0]['expires_at']
            if '.' in expires_at:
                expires_at = expires_at.split('.')[0] + '+00:00'
            else:
                expires_at = expires_at.replace('Z', '+00:00')
            expiry_date = datetime.fromisoformat(expires_at).replace(tzinfo=ZoneInfo("UTC"))
            if datetime.now(ZoneInfo("UTC")) > expiry_date:
                error = 'Reset token has expired.'
                logger.error(f"Password reset failed: Expired token: {token}")
                return render_template('reset_password.html', error=error, success=success, token=token), 400

            user_id = reset_data.data[0]['user_id']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Update user password
            supabase.table('users').update({'password': hashed_password}).eq('id', user_id).execute()
            # Mark token as used
            supabase.table('password_resets').update({'used': True}).eq('token', token).execute()

            logger.info(f"Password reset successfully for user_id: {user_id}")
            success = 'Password reset successfully! You can now log in with your new password.'
            return render_template('reset_password.html', error=error, success=success, token=token)
        except Exception as e:
            error = 'Unable to reset password right now. Please try again later.'
            logger.error(f"Password reset error: {str(e)}, Type: {type(e).__name__}, Traceback: {traceback.format_exc()}")
            return render_template('reset_password.html', error=error, success=success, token=token), 500

    return render_template('reset_password.html', error=error, success=success, token=token)

# Load environment variables
load_dotenv()

def send_email(to_email, subject, body):
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')

    if not sender_email or not sender_password:
        logger.error(f"Email configuration missing: sender_email={sender_email}, sender_password={'set' if sender_password else 'not set'}")
        raise ValueError("Email sender or password not configured in environment variables")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to_email} at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication error sending email to {to_email}: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
        return False

def send_reminder_emails():
    global scheduler
    if scheduler and scheduler.running:
        logger.info("Scheduler already running, skipping initialization")
        return

    supabase = get_supabase(use_service_role=True)
   
    try:
        logger.info(f"Fetching users for reminder emails at {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%I:%M %p IST')}")
        users = supabase.table('user_preferences')\
            .select('user_id, reminder_time, notification_preference')\
            .eq('notification_preference', 'email')\
            .execute()
        
        for user in users.data:
            user_id = user['user_id']
            reminder_time = user['reminder_time']
            user_data = supabase.table('users').select('email').eq('id', user_id).limit(1).execute()
            if not user_data.data:
                logger.warning(f"No email found for user_id: {user_id}")
                continue
            email = user_data.data[0]['email']
            
            # Schedule email at the reminder time (adjusted for IST)
            schedule.every().day.at(reminder_time).do(
                send_email,
                to_email=email,
                subject="NeuroAid Daily Reminder",
                body="Hi! It's time to journal on NeuroAid. Reflect on your day and check your progress!"
            )
            logger.info(f"Scheduled email for {email} at {reminder_time} IST")
    except Exception as e:
        logger.error(f"Error scheduling emails: {str(e)}")

def run_scheduler():
    with app.app_context():
        send_reminder_emails()  # Initial setup
        while True:
            schedule.run_pending()
            time.sleep(1)

        
if __name__ == '__main__':
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000)
