# 🧠 NeuroAid

**A mental health journaling web application with emotion analysis and personalized support.**

---

## 🪷 Overview

**NeuroAid** is a full-stack mental wellness web app that promotes healthy emotional habits through journaling, mood tracking, and AI-powered suggestions.  
It supports features like user authentication (with 2FA), emotion analysis of journal entries using NLP models, gratitude logging, mood-based music recommendations, and personalized mental health insights.

---

## ✨ Features

- 🔐 **User Authentication** – Sign-up/login with email verification, password reset, and Two-Factor Authentication (2FA).
- 📔 **Journaling with Emotion Detection** – Analyze mood from journal entries using Hugging Face's transformer models.
- 📈 **Mood Tracker** – Visualize weekly mood trends and track journaling streaks.
- 💡 **Personalized Suggestions** – Smart suggestions tailored to the user’s emotional state and goals.
- 🎶 **Mood-Based Music** – Spotify playlist recommendations based on detected mood and language preference.
- 🙏 **Gratitude Journaling** – Daily logging of three gratitude entries with streak and date tracking.
- 🧑‍💻 **Profile Management** – Update personal info, preferences, goals, and upload profile pictures.
- ⚙️ **Settings & Notifications** – Customize theme, language, and reminder timings.
- 📨 **Scheduled Email Reminders** – Daily journaling reminders sent via email.
- 🗃️ **Data Export & Account Deletion** – Export all user data or delete account securely.

---

## 🧑‍💻 Tech Stack

| Layer           | Technologies                                                                 |
|----------------|-------------------------------------------------------------------------------|
| **Frontend**    | HTML, CSS, JavaScript (static templating via Flask)                         |
| **Backend**     | Flask (Python)                                                               |
| **Database**    | Supabase (PostgreSQL)                                                        |
| **Auth & 2FA**  | bcrypt, pyotp, qrcode                                                        |
| **Email**       | SMTP (Gmail via `smtplib`)                                                   |
| **APIs**        | Hugging Face (`j-hartmann/emotion-english-distilroberta-base`), Spotify API |
| **Other Libs**  | `python-dotenv`, `requests`, `schedule`, `storage3`                         |

---

## 🚀 Getting Started

### 📦 Installation

```bash
git clone https://github.com/Barathkalyan/NeuroAid.git
cd NeuroAid
pip install -r requirements.txt
