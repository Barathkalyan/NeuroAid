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
                journal_data = {
                    'user_id': user_id,
                    'content': content
                }
                supabase.table('journal_entries').insert(journal_data).execute()
                return redirect(url_for('journal'))
            except Exception as e:
                logger.error(f"Journal save error: {str(e)}")
                return render_template('Journal.html', error=f"Failed to save journal: {str(e)}")

    try:
        entries = supabase.table('journal_entries').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return render_template('Journal.html', entries=entries.data if entries.data else [])
    except Exception as e:
        logger.error(f"Journal fetch error: {str(e)}")
        return render_template('Journal.html', error=f"Failed to fetch journals: {str(e)}")

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