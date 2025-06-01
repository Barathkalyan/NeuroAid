document.addEventListener('DOMContentLoaded', function () {
    // Function to map mood score to Tamil genre
    function mapMoodToGenre(moodScore) {
        if (moodScore >= 4) {
            return 'tamil pop'; // Happy/Energetic
        } else if (moodScore >= 2) {
            return 'tamil acoustic'; // Neutral/Calm
        } else {
            return 'tamil ballad'; // Sad/Neutral
        }
    }

    // Function to update the recommendations section
    function updateRecommendations(songs) {
        const recommendationsElement = document.getElementById('tamil-music-recommendations');
        if (recommendationsElement) {
            if (songs.length === 0) {
                recommendationsElement.innerHTML = 'No recommendations available.';
                return;
            }
            const songList = songs.map(song => `<p>Song: ${song.trackName} by ${song.artistName}</p>`).join('');
            recommendationsElement.innerHTML = songList;
            console.log('Recommendations updated:', songs);
        } else {
            console.error('Recommendations element not found. ID: tamil-music-recommendations');
        }
    }

    // Fetch mood data and recommend songs
    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data);

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
                return;
            }

            // Map mood to genre
            const genre = mapMoodToGenre(latestMood);
            console.log('Mood:', latestMood, 'Genre:', genre);

            // Fetch Tamil songs from iTunes Search API
            fetch(`https://itunes.apple.com/search?term=${genre}&media=music&limit=3`)
                .then(response => response.json())
                .then(musicData => {
                    const songs = musicData.results.map(song => ({
                        trackName: song.trackName,
                        artistName: song.artistName
                    }));
                    updateRecommendations(songs);
                })
                .catch(error => {
                    console.error('Error fetching music data:', error);
                    const recommendationsElement = document.getElementById('tamil-music-recommendations');
                    recommendationsElement.innerHTML = 'Unable to fetch Tamil songs. Try listening to some upbeat Tamil pop by Anirudh Ravichander!';
                });
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            const recommendationsElement = document.getElementById('tamil-music-recommendations');
            recommendationsElement.innerHTML = 'Log your mood to get Tamil music recommendations!';
        });
});