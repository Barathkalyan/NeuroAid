document.addEventListener('DOMContentLoaded', function () {
    const moodCanvas = document.getElementById('moodChart');
    const confidenceCanvas = document.getElementById('confidenceChart');

    function createCharts(data) {
        // --- Mood Chart (Line Chart) ---
        const moodCtx = moodCanvas.getContext('2d');
        const moodLineGradient = moodCtx.createLinearGradient(0, 0, 0, 300);
        moodLineGradient.addColorStop(0, '#FF6EC7');
        moodLineGradient.addColorStop(1, '#7879F1');
        const moodFillGradient = moodCtx.createLinearGradient(0, 0, 0, 300);
        moodFillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)');
        moodFillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)');

        new Chart(moodCtx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Mood',
                    data: data.data,
                    borderColor: moodLineGradient,
                    borderWidth: 3,
                    fill: true,
                    backgroundColor: moodFillGradient,
                    tension: 0.4,
                    pointBackgroundColor: '#FFFFFF',
                    pointBorderColor: '#7879F1',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 40,
                        bottom: 20
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 6,
                        min: 0,
                        ticks: { 
                            font: { family: "'Poppins', sans-serif", size: 12 },
                            padding: 15,
                            callback: function(value) {
                                const moodLabels = {
                                    0: '',
                                    1: 'Very Low',
                                    2: 'Low',
                                    3: 'Neutral',
                                    4: 'Good',
                                    5: 'Great',
                                    6: 'Max'
                                };
                                return moodLabels[value] || value;
                            }
                        },
                        title: { display: true, text: 'Mood Score', font: { size: 14 } },
                        grid: {
                            display: true,
                            drawBorder: true
                        }
                    },
                    x: {
                        ticks: { 
                            font: { family: "'Poppins', sans-serif", size: 10 },
                            maxRotation: 0,
                            minRotation: 0
                        },
                        title: { display: true, text: 'Day', font: { size: 12 } },
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { font: { size: 10 } }
                    },
                    tooltip: { enabled: true }
                }
            }
        });

        // --- Confidence Chart (Bar Chart) ---
        const confidenceCtx = confidenceCanvas.getContext('2d');
        const confidenceBarGradient = confidenceCtx.createLinearGradient(0, 0, 0, 300);
        confidenceBarGradient.addColorStop(0, '#00BFFF');
        confidenceBarGradient.addColorStop(1, '#1E90FF');

        new Chart(confidenceCtx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Confidence',
                    data: data.confidence,
                    backgroundColor: confidenceBarGradient,
                    borderColor: '#FFFFFF',
                    borderWidth: 1,
                    borderRadius: 5,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 40,
                        bottom: 20
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        min: 0,
                        ticks: { font: { family: "'Poppins', sans-serif", size: 12 }, padding: 15 },
                        title: { display: true, text: 'Confidence Score', font: { size: 14 } },
                        grid: {
                            display: true,
                            drawBorder: true
                        }
                    },
                    x: {
                        ticks: { 
                            font: { family: "'Poppins', sans-serif", size: 10 },
                            maxRotation: 0,
                            minRotation: 0
                        },
                        title: { display: true, text: 'Day', font: { size: 12 } },
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: { font: { size: 10 } }
                    },
                    tooltip: { enabled: true }
                }
            }
        });

        // --- Update Streak, Entries, and Average Mood ---
        const streakElement = document.getElementById('streak-value');
        if (streakElement) streakElement.textContent = `${data.streak} Days`;

        const numEntriesElement = document.getElementById('entries-count');
        if (numEntriesElement) numEntriesElement.textContent = `${data.numEntries} entries`;

        const moodElement = document.getElementById('mood');
        if (moodElement) {
            const moodEmojis = {
                'Very Low': '😞',
                'Low': '🙁',
                'Neutral': '😐',
                'Good': '🙂',
                'Great': '😊'
            };
            moodElement.textContent = `${data.avg_mood_description || 'Neutral'} ${moodEmojis[data.avg_mood_description] || ''}`;
        }
    }

    // Fetch data from the server
    fetch('/api/mood_data')
        .then(response => {
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            createCharts(data);
        })
        .catch(error => {
            console.error('Error:', error);
            createCharts({
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                data: [3, 3, 3, 3, 3, 3, 3],
                confidence: [0, 0, 0, 0, 0, 0, 0],
                numEntries: 0,
                streak: 0,
                avg_mood_description: 'Neutral'
            });
        });
});