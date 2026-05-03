<div align="center">

# 🧠 NeuroAid

**AI-Powered Mental Wellness Journaling Platform**

![Python Flask](https://img.shields.io/badge/Python-Flask-3776AB?style=for-the-badge&labelColor=111827)
![Supabase](https://img.shields.io/badge/Supabase-Backend-22C55E?style=for-the-badge&labelColor=111827)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Emotion_AI-F59E0B?style=for-the-badge&labelColor=111827)
![Spotify](https://img.shields.io/badge/Spotify-Mood_Playlists-1DB954?style=for-the-badge&labelColor=111827)
![2FA](https://img.shields.io/badge/2FA-Secure_Login-A855F7?style=for-the-badge&labelColor=111827)
![Privacy First](https://img.shields.io/badge/Privacy-First-14B8A6?style=for-the-badge&labelColor=111827)
![Status](https://img.shields.io/badge/Status-Working_Prototype-84CC16?style=for-the-badge&labelColor=111827)

*A safe, private space to understand your emotions, reflect daily, and grow mentally.*

</div>

---

## 🌿 Vision

Mental wellness shouldn't be a solo struggle. NeuroAid brings intelligence to journaling — helping users understand their emotional patterns, build healthy habits, and feel genuinely supported every day.

---

## 📌 The Problem

Most people lack the tools to:

- Process emotions privately and without judgment
- Recognize recurring mood patterns over time
- Build a consistent journaling or self-care habit
- Receive meaningful, personalized mental wellness support

Traditional journaling is passive. It stores thoughts but never responds, never guides, never grows with you.

---

## 🚀 The Solution

NeuroAid transforms everyday journaling into an **intelligent wellness companion**. By combining AI-powered emotion detection, personalized self-care recommendations, and habit-building systems, it turns reflection into guided, measurable growth.

---

## 🏗️ System Architecture

```
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

| Feature | Description |
|---|---|
| 📔 **Smart Journaling** | Write entries and receive AI-powered emotion insights instantly |
| 📊 **Mood Tracking** | 7-day charts, historical trends, and journaling streaks |
| 💡 **Personalized Support** | Self-care suggestions tailored to your mood and goals |
| 🎶 **Mood-Based Music** | Spotify playlists dynamically matched to your emotional state |
| 🙏 **Gratitude Logging** | Track daily gratitude habits and positivity streaks |
| 🔐 **Secure Authentication** | Email verification, bcrypt hashing, and optional 2FA |
| 🌐 **Multi-Language Support** | English, Tamil, Hindi, Telugu, Malayalam, Kannada |
| 🗃️ **Data Portability** | Export your data as JSON or permanently delete your account |

---

## 🔄 User Flow

```
Write Journal Entry
  → AI Emotion Analysis
  → Mood Score Generated
  → Personalized Suggestions Delivered
  → Progress Logged
  → Better Daily Emotional Awareness
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python (Flask) |
| Database | Supabase (PostgreSQL) |
| AI / NLP | Hugging Face Emotion Model |
| Authentication | bcrypt + pyotp (2FA) |
| Music | Spotify API |
| Email | SMTP |

---

## 📂 Repository Structure

```
NeuroAid/
├── app.py
├── templates/
├── static/
├── requirements.txt
└── README.md
```

---

## ⚙️ Quick Start

```bash
pip install -r requirements.txt
python app.py
```

---

## 🎯 Why NeuroAid?

| Without NeuroAid | With NeuroAid |
|---|---|
| ❌ Journaling without feedback | ✅ AI emotion insights after every entry |
| ❌ No emotional self-awareness | ✅ Mood scores and trend visualizations |
| ❌ Inconsistent mental habits | ✅ Streaks, reminders, and guided reflection |

---

## 🔮 Roadmap

- [ ] Mobile application (iOS & Android)
- [ ] Voice journaling support
- [ ] Therapist mode integrations
- [ ] Long-term emotional trend analysis via AI
- [ ] Anonymous peer support communities
- [ ] Wearable device mood sync

---

## 👨‍💻 Creators

**Barath Kalyan** — Full Stack Developer

**V Krishnakumar** — Backend Developer & AI Systems Builder

---

<div align="center">

Built with ❤️ for mental wellness.

</div>
