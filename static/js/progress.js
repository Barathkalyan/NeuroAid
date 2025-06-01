document.addEventListener('DOMContentLoaded', function () {
    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Log the API response for debugging

            // Get the canvas context
            const ctx = document.getElementById('moodChart').getContext('2d');

            // Create a gradient for the line (futuristic glowing effect)
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 400);
            lineGradient.addColorStop(0, '#FF6EC7'); // Bright neon pink at the top
            lineGradient.addColorStop(1, '#7879F1'); // Neon purple at the bottom

            // Create a gradient for the fill (light violet to slightly darker)
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 400);
            fillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.6)'); // Light violet with opacity
            fillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.2)'); // Slightly darker violet with fade

            // Create the chart with curves, filled region, and futuristic styling
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Mood',
                        data: data.data,
                        borderColor: lineGradient, // Glowing gradient line
                        borderWidth: 3,
                        fill: true, // Fill the area under the line
                        backgroundColor: fillGradient, // Gradient fill under the curve
                        tension: 0.4, // Smooth curves
                        pointBackgroundColor: '#FFFFFF', // White points for a futuristic look
                        pointBorderColor: '#7879F1', // Neon purple point borders
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5,
                            min: 1,
                            ticks: {
                                stepSize: 1,
                                color: '#D3D3D3', // Light gray for a futuristic look
                                font: {
                                    family: "'Roboto', sans-serif", // Modern font
                                    size: 12
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)', // Subtle grid lines
                            }
                        },
                        x: {
                            ticks: {
                                color: '#D3D3D3',
                                font: {
                                    family: "'Roboto', sans-serif",
                                    size: 12
                                }
                            },
                            grid: {
                                display: false // Remove x-axis grid for a cleaner look
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false // Hide legend for a minimalist futuristic look
                        }
                    },
                    animation: {
                        duration: 1500, // Smooth animation
                        easing: 'easeOutCubic' // Futuristic easing effect
                    }
                }
            });

            // Update number of journals (trying multiple possible IDs)
            const numJournalsElement = document.getElementById('num-journals') || 
                                      document.getElementById('journal-count') || 
                                      document.getElementById('total-entries') || 
                                      document.getElementById('entries-count');
            if (numJournalsElement) {
                numJournalsElement.textContent = data.numEntries || 0;
            } else {
                console.error('Number of journals element not found. Tried IDs: num-journals, journal-count, total-entries, entries-count');
            }

            // Update streak (trying multiple possible IDs)
            const streakElement = document.getElementById('streak') || 
                                 document.getElementById('streak-count') || 
                                 document.getElementById('current-streak');
            if (streakElement) {
                streakElement.textContent = data.streak || 0;
            } else {
                console.error('Streak element not found. Tried IDs: streak, streak-count, current-streak');
            }
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            const ctx = document.getElementById('moodChart').getContext('2d');
            // Fallback chart with the same styling
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 400);
            lineGradient.addColorStop(0, '#FF6EC7');
            lineGradient.addColorStop(1, '#7879F1');
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 400);
            fillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.6)');
            fillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.2)');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Mood',
                        data: [3, 3, 3, 3, 3, 3, 3],
                        borderColor: lineGradient,
                        borderWidth: 3,
                        fill: true,
                        backgroundColor: fillGradient,
                        tension: 0.4,
                        pointBackgroundColor: '#FFFFFF',
                        pointBorderColor: '#7879F1',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5,
                            min: 1,
                            ticks: {
                                stepSize: 1,
                                color: '#D3D3D3',
                                font: {
                                    family: "'Roboto', sans-serif",
                                    size: 12
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                            }
                        },
                        x: {
                            ticks: {
                                color: '#D3D3D3',
                                font: {
                                    family: "'Roboto', sans-serif",
                                    size: 12
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutCubic'
                    }
                }
            });

            // Fallback for number of journals and streak
            const numJournalsElement = document.getElementById('num-journals') || 
                                      document.getElementById('journal-count') || 
                                      document.getElementById('total-entries') || 
                                      document.getElementById('entries-count');
            if (numJournalsElement) {
                numJournalsElement.textContent = 0;
            }

            const streakElement = document.getElementById('streak') || 
                                 document.getElementById('streak-count') || 
                                 document.getElementById('current-streak');
            if (streakElement) {
                streakElement.textContent = 0;
            }
        });
});