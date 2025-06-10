async function loadSpotifyEmbed() {
    const playerContainer = document.getElementById('spotify-player');
    try {
        const response = await fetch('/api/recommend_music');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch music');
        }
        const data = await response.json();
        if (data.embedUrl) {
            playerContainer.innerHTML = `
                <h3>Now Playing (Mood Score: ${data.mood})</h3>
                <div id="iframe-wrapper">
                    <iframe style="border-radius:12px" 
                            src="${data.embedUrl}" 
                            width="100%" 
                            height="380" 
                            frameborder="0" 
                            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                            loading="lazy"></iframe>
                </div>`;
        } else {
            playerContainer.innerHTML = `
                <h3>Now Playing</h3>
                <p>No songs found. Try journaling to log your mood!</p>`;
        }
    } catch (error) {
        console.error('Error loading Spotify playlist:', error);
        playerContainer.innerHTML = `
            <h3>Now Playing</h3>
            <p>Error loading playlist: ${error.message}</p>`;
    }
}

async function setCurrentLanguage() {
    const languageSelect = document.getElementById('language-select');
    try {
        const response = await fetch('/api/update_language');
        if (!response.ok) throw new Error('Failed to fetch current language');
        const data = await response.json();
        if (data.language) {
            languageSelect.value = data.language;
        }
    } catch (error) {
        console.error('Error fetching current language:', error);
        languageSelect.value = 'tamil';
    }
}

function startSpeechRecognition() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        const moodMap = {
            'happy': 'happy',
            'calm': 'calm',
            'sad': 'sad',
            'anxious': 'anxious'
        };
        const detectedMood = Object.keys(moodMap).find(mood => transcript.includes(mood));
        if (detectedMood) {
            document.querySelector(`.mood-btn[data-mood="${detectedMood}"]`).click();
        } else {
            document.getElementById('current-mood').textContent = 'Unknown (from speech)';
        }
    };
    recognition.onerror = () => {
        document.getElementById('current-mood').textContent = 'Speech recognition failed';
    };
    recognition.start();
}

document.addEventListener('DOMContentLoaded', () => {
    const languageSelect = document.getElementById('language-select');
    const moodButtons = document.querySelectorAll('.mood-btn');
    const currentMoodDisplay = document.getElementById('current-mood');
    const suggestionsList = document.getElementById('vibe-suggestions-list');

    // Initialize language and load Spotify embed
    setCurrentLanguage().then(() => loadSpotifyEmbed());

    // Handle language change
    languageSelect.addEventListener('change', async () => {
        const language = languageSelect.value;
        try {
            const response = await fetch('/api/update_language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language })
            });
            if (!response.ok) {
                throw new Error('Error updating language');
            }
            await loadSpotifyEmbed();
        } catch (error) {
            console.error('Error updating language:', error);
            document.getElementById('spotify-player').innerHTML = `
                <h3>Now Playing</h3>
                <p>Error updating language: ${error.message}</p>`;
        }
    });

    // Handle mood selection
    moodButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const mood = button.getAttribute('data-mood');
            if (mood !== 'speech') {
                currentMoodDisplay.textContent = mood.charAt(0).toUpperCase() + mood.slice(1);
                
                // Map button moods to app.py mood scores (1-5)
                const moodMap = { happy: 5, calm: 4, sad: 1, anxious: 2 };
                const moodScore = moodMap[mood] || 3;

                // Update suggested activities
                suggestionsList.innerHTML = '<p>Loading suggestions...</p>';
                const suggestions = {
                    happy: ['Go for a walk in nature.', 'Call a friend to share your joy.'],
                    calm: ['Try a 5-minute meditation.', 'Read a relaxing book.'],
                    sad: ['Write down your feelings in your journal.', 'Watch a comforting movie.'],
                    anxious: ['Practice deep breathing exercises.', 'Listen to soothing music.']
                };
                suggestionsList.innerHTML = suggestions[mood].map(s => `<p>${s}</p>`).join('');

                // Refresh Spotify embed based on the latest mood
                await loadSpotifyEmbed();
            }
        });
    });
});