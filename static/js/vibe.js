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

document.addEventListener('DOMContentLoaded', () => {
    const languageSelect = document.getElementById('language-select');

    setCurrentLanguage().then(() => loadSpotifyEmbed());

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
});