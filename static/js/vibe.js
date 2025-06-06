document.addEventListener('DOMContentLoaded', function () {
    let currentLimit = 7;
    let currentGenre = 'tamil-folk';
    let moodData = null;

    // Map mood to genre (handled server-side, kept for reference)
    function mapMoodToGenre(mood) {
        const genres = {
            1: 'sad',
            2: 'melody',
            3: 'folk',
            4: 'pop',
            5: 'dance'
        };
        return genres[Math.round(mood)] || 'folk';
    }

    // Update recommendations UI
    function updateRecommendations(songs) {
        const recommendationsElement = document.getElementById('tamil-music-recommendations');
        recommendationsElement.innerHTML = '';

        if (!songs || songs.length === 0) {
            recommendationsElement.innerHTML = 'No songs found. Try logging your mood!';
            document.getElementById('load-more-btn').style.display = 'none';
            return;
        }

        songs.forEach(song => {
            const songCard = document.createElement('div');
            songCard.className = 'song-card';
            songCard.innerHTML = `
                <p>Song: ${song.trackName}</p>
                <p>Artist: ${song.artistName}</p>
                <p>Language: ${song.language.charAt(0).toUpperCase() + song.language.slice(1)}</p>
                <button class="play-btn neuroaid-btn" data-preview-url="${song.previewUrl}">
                    <i class="ri-play-fill"></i> Play
                </button>
            `;
            recommendationsElement.appendChild(songCard);
        });

        document.getElementById('load-more-btn').style.display = 'block';

        // Add play button functionality
        document.querySelectorAll('.play-btn').forEach(button => {
            button.addEventListener('click', function () {
                const audioPlayer = document.getElementById('audio-player');
                const audioSource = document.getElementById('audio-source');
                const nowPlaying = document.getElementById('now-playing');
                const previewUrl = this.getAttribute('data-preview-url');

                if (!previewUrl) {
                    nowPlaying.textContent = 'No audio available';
                    return;
                }

                audioSource.src = previewUrl;
                audioPlayer.load();
                audioPlayer.play().catch(error => {
                    console.error('Error playing audio:', error);
                    nowPlaying.textContent = 'Error playing song';
                });

                const songCard = this.closest('.song-card');
                const songName = songCard.querySelector('p:first-child').textContent.replace('Song: ', '');
                const artistName = songCard.querySelector('p:nth-child(2)').textContent.replace('Artist: ', '');
                nowPlaying.textContent = `${songName} by ${artistName}`;
            });
        });

        audioPlayer.addEventListener('ended', () => {
            document.getElementById('now-playing').textContent = 'Nothing playing';
        });
    }

    // Fetch recommendations from backend
    function fetchRecommendations(limit) {
        fetch(`/api/recommend_music?limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error:', data.error);
                    document.getElementById('tamil-music-recommendations').innerHTML = 'Unable to fetch songs. Try later!';
                    document.getElementById('load-more-btn').style.display = 'none';
                    return;
                }
                updateRecommendations(data.recommendations);
            })
            .catch(error => {
                console.error('Error fetching recommendations:', error);
                document.getElementById('tamil-music-recommendations').innerHTML = 'Unable to fetch songs. Try later!';
                document.getElementById('load-more-btn').style.display = 'none';
            });
    }

    // Populate mood day selector
    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            moodData = data;
            const moodDaySelect = document.getElementById('mood-day');
            moodDaySelect.innerHTML = '<option value="">Select a day</option>';

            data.labels.forEach((label, index) => {
                if (data.data[index] > 0) {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `${label} (Mood: ${data.data[index].toFixed(1)})`;
                    moodDaySelect.appendChild(option);
                }
            });

            // Fetch initial recommendations
            let latestMood = 0;
            for (let i = data.data.length - 1; i >= 0; i--) {
                if (data.data[i] > 0) {
                    latestMood = data.data[i];
                    break;
                }
            }

            if (latestMood === 0) {
                updateRecommendations([]);
                document.getElementById('tamil-music-recommendations').innerHTML = 'Log your mood to get song recommendations!';
                document.getElementById('load-more-btn').style.display = 'none';
                return;
            }

            currentGenre = mapMoodToGenre(latestMood);
            fetchRecommendations(currentLimit);
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            document.getElementById('tamil-music-recommendations').innerHTML = 'Log your mood to get song recommendations!';
            document.getElementById('load-more-btn').style.display = 'none';
        });

    // Language filter
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', async () => {
            const language = languageSelect.value;
            try {
                const response = await fetch('/api/update_language', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language })
                });
                if (response.ok) {
                    fetchRecommendations(currentLimit);
                } else {
                    console.error('Error updating language');
                }
            } catch (error) {
                console.error('Error updating language:', error);
            }
        });
    }

    // Load More button
    document.getElementById('load-more-btn').addEventListener('click', () => {
        currentLimit += 7;
        fetchRecommendations(currentLimit);
    });
});