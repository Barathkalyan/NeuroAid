🧠 NeuroAid
A mental health journaling web application with emotion analysis and personalized support.

🪷 Overview
NeuroAid is a full-stack mental wellness platform designed to empower users to enhance their mental health through reflective journaling, mood tracking, and AI-driven support. By leveraging natural language processing (NLP) for emotion analysis, NeuroAid provides personalized self-care recommendations, mood-based music suggestions, and gratitude logging to foster emotional well-being. The platform prioritizes user security with robust authentication, including two-factor authentication (2FA), and offers a seamless, customizable experience with features like theme toggling, multi-language support, and data portability.
NeuroAid is perfect for individuals seeking a private, supportive space to process emotions, set mental health goals, and build consistent journaling habits.

✨ Features

🔐 Secure Authentication  

Sign up and log in with email verification and password reset functionality.  
Optional Two-Factor Authentication (2FA) using TOTP (Time-based One-Time Password) with QR code setup.


📔 Journaling with Emotion Detection  

Write journal entries and receive real-time mood analysis powered by Hugging Face’s transformer model (j-hartmann/emotion-english-distilroberta-base).  
Entries are stored securely in Supabase, with options to view or delete them.


📊 Mood Tracker  

Visualize weekly mood trends with a 7-day mood chart.  
Track journaling streaks to encourage consistent engagement.  
Review emotional history to gain insights into patterns.


💡 Personalized Suggestions  

Receive tailored self-care activity suggestions based on detected emotions, user preferences, and time of day.  
Suggestions adapt to primary emotions (e.g., joy, sadness, anxiety) and secondary influences for nuanced support.


🎶 Mood-Based Music Recommendations  

Get Spotify playlist embeds matched to your mood and preferred language (e.g., Tamil, English, Telugu, Malayalam).


🙏 Gratitude Journaling  

Log three things you’re grateful for daily to promote positivity.  
Track gratitude streaks and view past entries with formatted dates.


🧑‍💻 Profile Management  

Customize your profile with a name, username, avatar, age, gender, location, and preferred language.  
Set mental health goals (e.g., stress management, improved mood) and preferred activities (e.g., meditation, writing).  
Upload profile pictures stored securely in Supabase’s storage.


⚙️ App Settings  

Toggle between light and dark themes for a personalized UI.  
Select preferred languages (e.g., Tamil, Hindi, Telugu, Malayalam, Kannada, English).  
Configure daily reminder times and notification preferences (e.g., email).


📨 Scheduled Email Reminders  

Receive automated daily emails to encourage journaling, scheduled based on user-defined times.


🗃️ Data Portability & Deletion  

Export all user data (profile, preferences, journal entries) in JSON format.  
Delete your account and all associated data with a single request.




🧑‍💻 Tech Stack



Layer
Technologies



Frontend
HTML, CSS, JavaScript (served via Flask templates)


Backend
Flask (Python)


Database
Supabase (PostgreSQL-based)


Authentication
bcrypt (password hashing), pyotp (2FA), qrcode (QR code generation)


Email Service
SMTP via smtplib (Gmail) for verification and reminder emails


Emotion AI
Hugging Face API (j-hartmann/emotion-english-distilroberta-base)


Music API
Spotify API (embedded playlists for mood-based recommendations)


Other Libraries
python-dotenv, requests, schedule, storage3, uuid, secrets



🚀 Getting Started
Follow these steps to set up and run NeuroAid locally on your machine.
📦 Installation

Clone the Repository  
git clone https://github.com/Barathkalyan/NeuroAid.git
cd NeuroAid


Set Up a Virtual Environment (recommended)  
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install DependenciesEnsure you have Python 3.8+ installed, then run:  
pip install flask supabase bcrypt pyotp qrcode pillow python-dotenv requests schedule storage3

(Note: Create a requirements.txt file with these dependencies for easier installation: pip install -r requirements.txt.)

Set Up Supabase  

Create a Supabase project at supabase.com.  
Set up the following tables: users, profiles, user_preferences, journal_entries, gratitude_entries, email_verifications, password_resets.  
Create a storage bucket named profile-pics for profile picture uploads.  
Obtain your SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_KEY from the Supabase dashboard.


Configure Email Service  

Set up a Gmail account or another SMTP-compatible email service.  
Generate an app-specific password for Gmail (if using Gmail) in your Google Account settings.


Obtain Hugging Face API Key  

Sign up at huggingface.co and generate an API key for accessing the emotion analysis model.




⚙️ Environment Variables
Create a .env file in the project root with the following variables:  
FLASK_SECRET_KEY=your-secure-flask-secret-key
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
EMAIL_SENDER=your-email-address
EMAIL_PASSWORD=your-email-password-or-app-specific-password
HUGGINGFACE_API_KEY=your-huggingface-api-key


FLASK_SECRET_KEY: A secure, random string for Flask session security (e.g., generate with secrets.token_hex(16)).  
SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY: Credentials from your Supabase project.  
EMAIL_SENDER, EMAIL_PASSWORD: SMTP credentials for sending emails (e.g., Gmail app-specific password).  
HUGGINGFACE_API_KEY: API key for Hugging Face emotion analysis.


🏃‍♂️ Running the Project Locally

Ensure the .env File is ConfiguredVerify that all required environment variables are set in the .env file.

Start the Flask Application  
python app.py


Access the ApplicationOpen your browser and navigate to http://localhost:5000.  

Sign up with a valid email address to create an account.  
Verify your email via the link sent to your inbox.  
Log in and explore journaling, mood tracking, and other features.




🛠️ Project Structure
NeuroAid/
├── app.py                  # Main Flask application
├── templates/              # HTML templates (e.g., login.html, index.html, journal.html)
├── .env                   # Environment variables (not committed)
├── requirements.txt        # Python dependencies (create manually)
├── static/                 # Static assets (CSS, JS, images)
└── README.md               # Project documentation


📋 Database Schema
The application uses Supabase (PostgreSQL) with the following tables:

users: Stores user credentials (id, email, password, is_verified).  
profiles: Stores user profile data (user_id, name, username, age, gender, location, preferred_language, primary_goal, engagement_frequency, preferred_activities, profile_pic_url).  
user_preferences: Stores user settings (user_id, language, theme, two_factor_enabled, two_factor_secret, reminder_time, notification_preference).  
journal_entries: Stores journal entries (id, user_id, content, created_at, analysis).  
gratitude_entries: Stores gratitude entries (user_id, thing1, thing2, thing3, created_at).  
email_verifications: Stores email verification tokens (user_id, token, expires_at, verified).  
password_resets: Stores password reset tokens (user_id, token, expires_at, used).


🔐 Security Features

Password Hashing: Uses bcrypt for secure password storage.  
Two-Factor Authentication: Implements TOTP-based 2FA with pyotp and QR code generation via qrcode.  
Session Management: Enforces session expiration after 30 minutes of inactivity.  
Secure Email Verification: Uses time-limited tokens for email verification and password resets.  
File Upload Validation: Restricts profile picture uploads to JPEG, PNG, GIF, and WEBP with a 5MB size limit.


🌟 Contributing
We welcome contributions to NeuroAid! To contribute:  

Fork the repository.  
Create a new branch (git checkout -b feature/your-feature).  
Make your changes and commit (git commit -m "Add your feature").  
Push to your branch (git push origin feature/your-feature).  
Open a pull request with a clear description of your changes.

Please ensure your code follows PEP 8 guidelines and includes appropriate tests.

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

📬 Contact
For questions or support, reach out to the NeuroAid team at support@neuroaid.com or open an issue on GitHub.

Built with ❤️ for mental wellness. Start your journey with NeuroAid today!
