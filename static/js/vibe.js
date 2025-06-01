document.addEventListener('DOMContentLoaded', function () {
    let currentLimit = 7; // Initial number of recommendations
    let currentGenre = '';
    let moodData = [];

    // Function to map mood score to Tamil genre
    function mapMoodToGenre(moodScore) {
        if (moodScore >= 4) return 'tamil pop'; // Happy/Energetic
        else if (moodScore >= 2) return 'tamil acoustic'; // Neutral/Calm
        else return 'tamil ballad'; // Sad/Neutral
    }

    // Function to update the recommendations section
    function updateRecommendations(songs) {
        const recommendationsElement = document.getElementById('tamil-music-recommendations');
        if (recommendationsElement) {
            if (songs.length === 0) {
                recommendationsElement.innerHTML = 'No recommendations available.';
                document.getElementById('load-more-btn').style.display = 'none';
                return;
            }
            const songList = songs.map(song => `
                <div class="song-card">
                    <p><strong>Song:</strong> ${song.trackName}</p>
                    <p><strong>Artist:</strong> ${song.artistName}</p>
                    ${song.previewUrl ? `<button class="play-btn" data-preview-url="${song.previewUrl}">Play Preview</button>` : '<p>No preview available.</p>'}
                </div>
            `).join('');
            recommendationsElement.innerHTML = songList;
            console.log('Recommendations updated:', songs);
            document.getElementById('load-more-btn').style.display = songs.length >= currentLimit ? 'block' : 'none';
            setupMusicPlayer();
        } else {
            console.error('Recommendations element not found. ID: tamil-music-recommendations');
        }
    }

    // Function to set up music player functionality
    function setupMusicPlayer() {
        const playButtons = document.querySelectorAll('.play-btn');
        const audioPlayer = document.getElementById('audio-player');
        const audioSource = document.getElementById('audio-source');
        const nowPlaying = document.getElementById('now-playing');

        playButtons.forEach(button => {
            button.addEventListener('click', function () {
                const previewUrl = this.getAttribute('data-preview-url');
                audioSource.src = previewUrl;
                audioPlayer.load();
                audioPlayer.play().catch(error => {
                    console.error('Error playing audio:', error);
                    nowPlaying.textContent = 'Error playing preview';
                });
                const songCard = this.closest('.song-card');
                const songName = songCard.querySelector('p:first-child').textContent.replace('Song: ', '');
                const artistName = songCard.querySelector('p:nth-child(2)').textContent.replace('Artist: ', '');
                nowPlaying.textContent = `${songName} by ${artistName}`;
            });
        });

        audioPlayer.addEventListener('ended', () => {
            nowPlaying.textContent = 'Nothing playing';
        });
    }

    // Function to populate mood selector
    function populateMoodSelector(data) {
        const moodSelect = document.getElementById('mood-day');
        moodSelect.innerHTML = '<option value="">Select a day</option>';
        data.labels.forEach((label, index) => {
            const mood = data.data[index];
            if (mood > 0) {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${label} (Mood: ${mood})`;
                moodSelect.appendChild(option);
            }
        });

        moodSelect.addEventListener('change', function () {
            const selectedIndex = parseInt(this.value);
            if (!isNaN(selectedIndex)) {
                const selectedMood = data.data[selectedIndex];
                currentGenre = mapMoodToGenre(selectedMood);
                currentLimit = 7; // Reset limit when changing mood
                fetchRecommendations(currentGenre, currentLimit);
            }
        });
    }

    // Function to fetch recommendations
    function fetchRecommendations(genre, limit) {
        fetch(`https://itunes.apple.com/search?term=${genre}&media=music&limit=${limit}`)
            .then(response => response.json())
            .then(musicData => {
                const songs = musicData.results.map(song => ({
                    trackName: song.trackName,
                    artistName: song.artistName,
                    previewUrl: song.previewUrl
                }));
                updateRecommendations(songs);
            })
            .catch(error => {
                console.error('Error fetching music data:', error);
                const recommendationsElement = document.getElementById('tamil-music-recommendations');
                recommendationsElement.innerHTML = 'Unable to fetch Tamil songs. Try listening to some upbeat Tamil pop by Anirudh Ravichander!';
                document.getElementById('load-more-btn').style.display = 'none';
            });
    }

    // Fetch mood data and recommend songs
    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data);
            moodData = data;

            // Populate mood selector
            populateMoodSelector(data);

            // Find the latest non-zero mood score
            let latestMood = 0;
            for (let i = data.data.length - 1; i >= 0; i--) {
                if (data.data[i] > 0) {
                    latestMood = data.data[i];
                    break;
                }
            }

            // If no mood data, show a message
            if (latestMood === 0) {
                updateRecommendations([]);
                const recommendationsElement = document.getElementById('tamil-music-recommendations');
                recommendationsElement.innerHTML = 'Log your mood to get Tamil music recommendations!';
                document.getElementById('load-more-btn').style.display = 'none';
                return;
            }

            // Map mood to genre and fetch recommendations
            currentGenre = mapMoodToGenre(latestMood);
            console.log('Mood:', latestMood, 'Genre:', currentGenre);
            fetchRecommendations(currentGenre, currentLimit);
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            const recommendationsElement = document.getElementById('tamil-music-recommendations');
            recommendationsElement.innerHTML = 'Log your mood to get Tamil music recommendations!';
            document.getElementById('load-more-btn').style.display = 'none';
        });

    // Load More button functionality
    document.getElementById('load-more-btn').addEventListener('click', function () {
        currentLimit += 7; // Fetch 7 more songs
        fetchRecommendations(currentGenre, currentLimit);
    });
});