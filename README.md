# 🧠 **NeuroAid**

**A mental health journaling web application with emotion analysis and personalized support.**

---

## 🪷 **Overview**

**NeuroAid** is a full-stack mental wellness platform designed to empower users to enhance their mental health through reflective journaling, mood tracking, and AI-driven support...

By leveraging natural language processing (NLP) for emotion analysis, NeuroAid provides:
- Personalized self-care recommendations  
- Mood-based music suggestions  
- Gratitude logging to foster emotional well-being  

The platform prioritizes user security with robust authentication (including 2FA), and offers a seamless, customizable experience with features like theme toggling, multi-language support, and data portability.

> 🧘 Ideal for individuals seeking a private, supportive space to process emotions, set mental health goals, and build consistent journaling habits.

---

## ✨ **Features**

### 🔐 Secure Authentication
- Email verification and password reset functionality  
- Optional Two-Factor Authentication (2FA) using TOTP and QR code

---

### 📔 Journaling with Emotion Detection
- Real-time mood analysis powered by Hugging Face’s transformer model  
- Secure entry storage via Supabase  
- View and delete previous entries easily

---

### 📊 Mood Tracker
- 7-day mood chart to visualize emotional trends  
- Track journaling streaks to stay consistent  
- Access past mood history for deeper insights

---

### 💡 Personalized Suggestions
- Emotion-based self-care activity suggestions  
- Tailored by mood type, preferences, and time of day  
- Contextual support for nuanced emotional states

---

### 🎶 Mood-Based Music Recommendations
- Spotify playlist embeds matched to your emotional state  
- Language-based personalization (e.g., Tamil, English, Telugu)

---

### 🙏 Gratitude Journaling
- Log three daily gratitude entries  
- View past gratitude logs with formatted dates  
- Track gratitude streaks to reinforce positivity

---

### 🧑‍💻 Profile Management
- Add name, username, avatar, age, gender, and location  
- Set personal goals (e.g., reduce stress, build positivity)  
- Upload profile pictures (stored securely on Supabase)

---

### ⚙️ App Settings
- Light/dark theme toggling  
- Language selection: Tamil, Hindi, Telugu, Malayalam, Kannada, English  
- Email reminder configuration and notification preferences

---

### 📨 Scheduled Email Reminders
- Automated journaling reminders via email  
- Configurable schedule set by the user

---

### 🗃️ Data Portability & Deletion
- Export profile, preferences, and entries in JSON format  
- One-click account and data deletion

---

## 🧑‍💻 **Tech Stack**

| Layer              | Technologies                                                                 |
|--------------------|------------------------------------------------------------------------------|
| **Frontend**       | HTML, CSS, JavaScript (served via Flask templates)                           |
| **Backend**        | Flask (Python)                                                               |
| **Database**       | Supabase (PostgreSQL)                                                        |
| **Authentication** | bcrypt (password hashing), pyotp (2FA), qrcode (QR code generation)          |
| **Email Service**  | SMTP via `smtplib` (Gmail)                                                   |
| **Emotion AI**     | Hugging Face API (`j-hartmann/emotion-english-distilroberta-base`)           |
| **Music API**      | Spotify API (embedded playlists based on detected mood & language)           |
| **Other Libraries**| `python-dotenv`, `requests`, `schedule`, `storage3`, `uuid`, `secrets`       |

---

---

## 👨‍💻 Creators

**NeuroAid** is crafted with care by:

- **Barath Kalyan** – Full-stack developer, AI enthusiast!  
🔗 [GitHub](https://github.com/Barathkalyan) | 📫 tbarathkalyan@gmail.com

- **Krishnakumar** - Backend Developer, LLM Model tuner, Learner!!!
🔗 [GitHub](https://github.com/V-Krishnakumar) | 📫 drkrishnav06@gmail.com
 

We welcome contributions, feedback, or collaborations! Feel free to reach out or open an issue.





Built with ❤️ for mental wellness. Start your journey with NeuroAid today!
