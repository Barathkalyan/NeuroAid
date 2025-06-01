document.addEventListener('DOMContentLoaded', function () {
    // Get the canvas element and set its size for a larger graph
    const canvas = document.getElementById('moodChart');
    canvas.width = 800;  // Increase width
    canvas.height = 400; // Increase height

    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Log the API response for debugging

            const ctx = canvas.getContext('2d');

            // Create a gradient for the line (futuristic glowing effect)
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 400);
            lineGradient.addColorStop(0, '#FF6EC7'); // Neon pink
            lineGradient.addColorStop(1, '#7879F1'); // Neon purple

            // Create a gradient for the fill (light violet to slightly darker)
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 400);
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
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14 // Larger font for readability
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 16,
                                    weight: 'bold'
                                },
                                padding: 10
                            }
                        },
                        x: {
                            ticks: {
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                }
                            },
                            grid: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Day',
                                color: '#D3D3D3',
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
                    // Add subtle shadow for modern look
                    elements: {
                        line: {
                            shadowColor: 'rgba(255, 255, 255, 0.3)',
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowOffsetY: 0
                        }
                    },
                    // Handle click events on points
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const day = data.labels[element.index];
                            alert(`Day: ${day}`); // Display the day in an alert
                            // Alternatively, you can update a DOM element:
                            // const dayDisplay = document.getElementById('selected-day');
                            // if (dayDisplay) dayDisplay.textContent = `Selected Day: ${day}`;
                        }
                    }
                }
            });

            // Update number of journals (trying more possible IDs)
            const numJournalsElement = document.getElementById('num-journals') || 
                                      document.getElementById('journal-count') || 
                                      document.getElementById('total-entries') || 
                                      document.getElementById('entries-count') || 
                                      document.getElementById('number-of-journals') || 
                                      document.getElementById('journal-total');
            if (numJournalsElement) {
                numJournalsElement.textContent = data.numEntries || 0;
            } else {
                console.error('Number of journals element not found. Tried IDs: num-journals, journal-count, total-entries, entries-count, number-of-journals, journal-total');
            }

            // Update streak (trying more possible IDs)
            const streakElement = document.getElementById('streak') || 
                                 document.getElementById('streak-count') || 
                                 document.getElementById('current-streak') || 
                                 document.getElementById('streak-days') || 
                                 document.getElementById('user-streak');
            if (streakElement) {
                streakElement.textContent = data.streak || 0;
            } else {
                console.error('Streak element not found. Tried IDs: streak, streak-count, current-streak, streak-days, user-streak');
            }
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);
            const ctx = canvas.getContext('2d');
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 400);
            lineGradient.addColorStop(0, '#FF6EC7');
            lineGradient.addColorStop(1, '#7879F1');
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 400);
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
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 16,
                                    weight: 'bold'
                                },
                                padding: 10
                            }
                        },
                        x: {
                            ticks: {
                                color: '#D3D3D3',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                }
                            },
                            grid: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Day',
                                color: '#D3D3D3',
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

            // Fallback for number of journals and streak
            const numJournalsElement = document.getElementById('num-journals') || 
                                      document.getElementById('journal-count') || 
                                      document.getElementById('total-entries') || 
                                      document.getElementById('entries-count') || 
                                      document.getElementById('number-of-journals') || 
                                      document.getElementById('journal-total');
            if (numJournalsElement) {
                numJournalsElement.textContent = 0;
            }

            const streakElement = document.getElementById('streak') || 
                                 document.getElementById('streak-count') || 
                                 document.getElementById('current-streak') || 
                                 document.getElementById('streak-days') || 
                                 document.getElementById('user-streak');
            if (streakElement) {
                streakElement.textContent = 0;
            }
        });
});