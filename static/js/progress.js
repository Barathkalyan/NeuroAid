// Wait for the page to fully load before running the script
document.addEventListener('DOMContentLoaded', function () {
    // Get the canvas elements for the charts
    const moodCanvas = document.getElementById('moodChart');
    const confidenceCanvas = document.getElementById('confidenceChart');

    // Function to create both charts with the fetched data
    function createCharts(data) {
        // --- Mood Chart (Line Chart) ---
        const moodCtx = moodCanvas.getContext('2d');
        // Create a gradient for the line color (pink to purple)
        const moodLineGradient = moodCtx.createLinearGradient(0, 0, 0, 300);
        moodLineGradient.addColorStop(0, '#FF6EC7'); // Neon pink
        moodLineGradient.addColorStop(1, '#7879F1'); // Neon purple
        // Create a gradient for the area under the line
        const moodFillGradient = moodCtx.createLinearGradient(0, 0, 0, 300);
        moodFillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)');
        moodFillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)');

        new Chart(moodCtx, {
            type: 'line', // Line chart for mood
            data: {
                labels: data.labels, // X-axis: days (e.g., ["Jun 15", "Jun 16", ...])
                datasets: [{
                    label: 'Mood',
                    data: data.data, // Y-axis: mood scores (e.g., [3.5, 4.0, ...])
                    borderColor: moodLineGradient,
                    borderWidth: 3,
                    fill: true, // Fill the area under the line
                    backgroundColor: moodFillGradient,
                    tension: 0.4, // Smooth curve
                    pointBackgroundColor: '#FFFFFF',
                    pointBorderColor: '#7879F1',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true, // Adjusts to container size
                maintainAspectRatio: false, // Allows custom height
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5, // Mood score range: 0-5
                        min: 0,
                        ticks: { font: { family: "'Poppins', sans-serif", size: 14 } },
                        title: { display: true, text: 'Mood Score', font: { size: 16 } }
                    },
                    x: {
                        ticks: { font: { family: "'Poppins', sans-serif", size: 14 } },
                        title: { display: true, text: 'Day', font: { size: 14 } }
                    }
                },
                plugins: {
                    legend: { labels: { font: { size: 12 } } },
                    tooltip: { enabled: true } // Show tooltips on hover
                }
            }
        });

        // --- Confidence Chart (Bar Chart) ---
        const confidenceCtx = confidenceCanvas.getContext('2d');
        // Create a gradient for the bars (blue shades)
        const confidenceBarGradient = confidenceCtx.createLinearGradient(0, 0, 0, 300);
        confidenceBarGradient.addColorStop(0, '#00BFFF');
        confidenceBarGradient.addColorStop(1, '#1E90FF');

        new Chart(confidenceCtx, {
            type: 'bar', // Bar chart for confidence
            data: {
                labels: data.labels, // Same days as mood chart
                datasets: [{
                    label: 'Confidence',
                    data: data.confidence, // Y-axis: confidence scores (e.g., [0.7, 0.8, ...])
                    backgroundColor: confidenceBarGradient,
                    borderColor: '#FFFFFF',
                    borderWidth: 1,
                    borderRadius: 5, // Rounded bars
                    barThickness: 30 // Bar width
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1, // Confidence score range: 0-1
                        min: 0,
                        ticks: { font: { family: "'Poppins', sans-serif", size: 14 } },
                        title: { display: true, text: 'Confidence Score', font: { size: 16 } }
                    },
                    x: {
                        ticks: { font: { family: "'Poppins', sans-serif", size: 14 } },
                        title: { display: true, text: 'Day', font: { size: 14 } }
                    }
                },
                plugins: {
                    legend: { labels: { font: { size: 12 } } },
                    tooltip: { enabled: true }
                }
            }
        });

        // --- Update Streak and Entries ---
        const streakElement = document.getElementById('streak-value');
        if (streakElement) {
            streakElement.textContent = `${data.streak} Days`; // e.g., "3 Days"
        }

        const numEntriesElement = document.getElementById('entries-count');
        if (numEntriesElement) {
            numEntriesElement.textContent = `${data.numEntries} entries`; // e.g., "5 entries"
        }
    }

    // Fetch data from the server
    fetch('/api/mood_data')
        .then(response => {
            // Check if the response is okay (status 200-299)
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json(); // Parse the JSON response
        })
        .then(data => {
            console.log('Data received:', data); // Log data for debugging
            createCharts(data); // Create charts with the data
        })
        .catch(error => {
            console.error('Error:', error); // Log any errors
            // Use fallback data if the API fails
            createCharts({
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                data: [3, 3, 3, 3, 3, 3, 3], // Default mood scores
                confidence: [0, 0, 0, 0, 0, 0, 0], // Default confidence scores
                numEntries: 0,
                streak: 0
            });
        });
});