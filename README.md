# 🧠 NeuroAid

<p align="center">
  <b>AI-Powered Mental Wellness Journaling Platform</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-Flask-3776AB?style=for-the-badge&labelColor=111827" />
  <img src="https://img.shields.io/badge/Supabase-Backend-22C55E?style=for-the-badge&labelColor=111827" />
  <img src="https://img.shields.io/badge/HuggingFace-Emotion_AI-F59E0B?style=for-the-badge&labelColor=111827" />
  <img src="https://img.shields.io/badge/Spotify-Mood_Playlists-1DB954?style=for-the-badge&labelColor=111827" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/2FA-Secure_Login-A855F7?style=for-the-badge&labelColor=111827" />
  <img src="https://img.shields.io/badge/Privacy-First-14B8A6?style=for-the-badge&labelColor=111827" />
  <img src="https://img.shields.io/badge/Status-Working_Prototype-84CC16?style=for-the-badge&labelColor=111827" />
</p>

---

## 🌿 Vision

<p align="center">
Create a safe private space where users can understand emotions, reflect daily and improve mental wellness for prosperity
  
</p>

---

## 📌 Problem Statement

Many people struggle to:

* Process emotions privately
* Track mood patterns
* Build journaling consistency
* Receive meaningful support
* Stay mentally balanced in daily life

Traditional journaling lacks intelligence and guidance.

---

## 🚀 Solution

NeuroAid transforms journaling into an intelligent wellness companion using AI-powered emotion detection, personalized self-care recommendations and habit-building systems.

It blends emotional awareness, privacy and daily consistency into one platform.

---

## 🏗️ System Architecture

```text id="e2f78m"
         ┌──────────────────────┐
         │      User Journal    │
         │   Writes Thoughts    │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Flask Backend API  │
         └──────────┬───────────┘
                    │
        ┌───────────┼────────────┐
        ▼                        ▼
┌────────────────┐      ┌────────────────────┐
│ HuggingFace AI │      │ Supabase Database  │
│ Emotion Model  │      │ Entries + Profiles │
└────────────────┘      └────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ Suggestions + Mood Score   │
│ Charts + Spotify Playlists │
└────────────────────────────┘
```

---

## ⚙️ Core Features

### 📔 Smart Journaling

Write entries and receive AI emotion insights instantly.

### 📊 Mood Tracking

7-day charts, history trends and journaling streaks.

### 💡 Personalized Support

Self-care suggestions based on mood and goals.

### 🎶 Mood-Based Music

Spotify playlists matched to emotional state.

### 🙏 Gratitude Logging

Track daily gratitude habits and positivity streaks.

### 🔐 Secure Authentication

Email verification, password hashing and optional 2FA.

### 🌐 Multi-Language Support

Tamil, Hindi, Telugu, Malayalam, Kannada, English.

### 🗃️ Data Portability

Export JSON data or permanently delete account.

---

## 🔄 User Flow

```text id="dhpnxt"
Write Journal Entry
→ AI Emotion Analysis
→ Mood Score Generated
→ Personalized Suggestions
→ Progress Logged
→ Better Daily Awareness
```

---

## 🛠️ Tech Stack

| Layer    | Technology              |
| -------- | ----------------------- |
| Frontend | HTML + CSS + JavaScript |
| Backend  | Python Flask            |
| Database | Supabase PostgreSQL     |
| AI       | Hugging Face NLP Model  |
| Auth     | bcrypt + pyotp          |
| Media    | Spotify API             |
| Email    | SMTP                    |

---

## 📂 Repository Structure

```text id="0nbqxp"
NeuroAid/
├── app.py
├── templates/
├── static/
├── requirements.txt
└── README.md
```

---

## ⚙️ Quick Start

```bash id="68qg0q"
pip install -r requirements.txt
python app.py
```

---

## 🎯 Why It Matters

```text id="y8az66"
❌ Journaling without feedback
❌ No emotional awareness
❌ Inconsistent mental habits

✅ NeuroAid turns reflection into guided growth
```

---

## 🔮 Future Improvements

* Mobile app version
* Voice journaling
* Therapist mode integrations
* AI long-term emotional trends
* Anonymous support communities
* Wearable mood sync

---

## 👨‍💻 Creators

**Barath Kalyan**
Full Stack Developer

**V Krishnakumar**
Backend Developer • AI Systems Builder

---

<p align="center">
Built with ❤️ for mental wellness.
</p>
