document.addEventListener('DOMContentLoaded', function () {
    // Get the canvas element and set its size for a larger graph
    const canvas = document.getElementById('moodChart');
    canvas.width = 900;  // Increased width
    canvas.height = 650; // Increased height

    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Log the API response for debugging

            const ctx = canvas.getContext('2d');

            // Create a gradient for the line (futuristic glowing effect)
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 650);
            lineGradient.addColorStop(0, '#FF6EC7'); // Neon pink
            lineGradient.addColorStop(1, '#7879F1'); // Neon purple

            // Create a gradient for the fill (light violet to slightly darker)
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 650);
            fillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)'); // Light violet with reduced opacity
            fillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)'); // Slightly darker violet with fade

            // Create the chart with enhanced styling
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Mood',
                        data: data.data,
                        borderColor: lineGradient,
                        borderWidth: 3,
                        fill: true,
                        backgroundColor: fillGradient,
                        tension: 0.4, // Smooth curves
                        pointBackgroundColor: '#FFFFFF',
                        pointBorderColor: '#7879F1',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 8, // Larger on hover for better interaction
                        pointHoverBackgroundColor: '#FF6EC7', // Neon pink on hover
                        pointHoverBorderColor: '#FFFFFF',
                        pointHoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // Allow custom canvas size
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5,
                            min: 1,
                            ticks: {
                                stepSize: 1,
                                color: '#000000', // Black for visibility
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17 // Larger font for readability
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0)', // Transparent grid lines as per your CSS
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#000000', // Black for visibility
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 10
                            }
                        },
                        x: {
                            ticks: {
                                color: '#000000', // Black for visibility
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Day',
                                color: '#000000', // Black for visibility
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 16,
                                    weight: 'bold'
                                },
                                padding: 10
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false // Disable default tooltip since we're using onClick
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutCubic'
                    },
                    elements: {
                        line: {
                            shadowColor: 'rgba(255, 255, 255, 0.3)',
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowOffsetY: 0
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const day = data.labels[element.index];
                            alert(`Day: ${day}`); // Display the day in an alert
                        }
                    }
                }
            });

            // Update number of entries
            const numEntriesElement = document.getElementById('entries-count');
            if (numEntriesElement) {
                numEntriesElement.textContent = `${data.numEntries} entries`; // Match the format in HTML
                console.log('Number of entries updated:', data.numEntries);
            } else {
                console.error('Number of entries element not found. ID: entries-count');
            }

            // Update streak
            const streakElement = document.getElementById('streak-value');
            if (streakElement) {
                streakElement.textContent = `${data.streak} Days`; // Match the format in HTML
                console.log('Streak updated:', data.streak);
            } else {
                console.error('Streak element not found. ID: streak-value');
            }
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            const ctx = canvas.getContext('2d');
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 650);
            lineGradient.addColorStop(0, '#FF6EC7');
            lineGradient.addColorStop(1, '#7879F1');
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 650);
            fillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)');
            fillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)');
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
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: '#FF6EC7',
                        pointHoverBorderColor: '#FFFFFF',
                        pointHoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5,
                            min: 1,
                            ticks: {
                                stepSize: 1,
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0)',
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 10
                            }
                        },
                        x: {
                            ticks: {
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Day',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 16,
                                    weight: 'bold'
                                },
                                padding: 10
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutCubic'
                    },
                    elements: {
                        line: {
                            shadowColor: 'rgba(255, 255, 255, 0.3)',
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowOffsetY: 0
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][element.index];
                            alert(`Day: ${day}`);
                        }
                    }
                }
            });

            // Fallback for number of entries and streak
            const numEntriesElement = document.getElementById('entries-count');
            if (numEntriesElement) {
                numEntriesElement.textContent = '0 entries';
            }

            const streakElement = document.getElementById('streak-value');
            if (streakElement) {
                streakElement.textContent = '0 Days';
            }
        });
});