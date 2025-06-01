document.addEventListener('DOMContentLoaded', function () {
    // Mood Chart Canvas
    const moodCanvas = document.getElementById('moodChart');
    moodCanvas.width = 900;
    moodCanvas.height = 650;

    // Confidence Chart Canvas
    const confidenceCanvas = document.getElementById('confidenceChart');
    confidenceCanvas.width = 900;
    confidenceCanvas.height = 650;

    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data);

            // Mood Chart (Area Chart using Line with Fill)
            const moodCtx = moodCanvas.getContext('2d');
            const moodLineGradient = moodCtx.createLinearGradient(0, 0, 0, 650);
            moodLineGradient.addColorStop(0, '#FF6EC7'); // Neon pink
            moodLineGradient.addColorStop(1, '#7879F1'); // Neon purple
            const moodFillGradient = moodCtx.createLinearGradient(0, 0, 0, 650);
            moodFillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)'); // Light violet
            moodFillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)'); // Slightly darker violet

            const moodChart = new Chart(moodCtx, {
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
                            min: 0,
                            ticks: {
                                stepSize: 1,
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 5
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
                            display: true,
                            labels: {
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                },
                                color: '#000000'
                            }
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
                            const day = data.labels[element.index];
                            alert(`Day: ${day}`);
                        }
                    }
                }
            });

            // Confidence Chart (Bar Chart)
            const confidenceCtx = confidenceCanvas.getContext('2d');
            const confidenceBarGradient = confidenceCtx.createLinearGradient(0, 0, 0, 650);
            confidenceBarGradient.addColorStop(0, '#00BFFF'); // Deep sky blue
            confidenceBarGradient.addColorStop(1, '#1E90FF'); // Dodger blue

            const confidenceChart = new Chart(confidenceCtx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Confidence',
                        data: data.confidence,
                        backgroundColor: confidenceBarGradient,
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        borderRadius: 5, // Rounded corners for bars
                        barThickness: 40, // Thinner bars
                        categoryPercentage: 0.5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1,
                            min: 0,
                            ticks: {
                                stepSize: 0.2,
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Confidence Score',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 5
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
                            display: true,
                            labels: {
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                },
                                color: '#000000'
                            }
                        },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutCubic'
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const day = data.labels[element.index];
                            alert(`Day: ${day}`);
                        }
                    }
                }
            });

            // Update number of entries
            const numEntriesElement = document.getElementById('entries-count');
            if (numEntriesElement) {
                numEntriesElement.textContent = `${data.numEntries} entries`;
                console.log('Number of entries updated:', data.numEntries);
            } else {
                console.error('Number of entries element not found. ID: entries-count');
            }

            // Update streak
            const streakElement = document.getElementById('streak-value');
            if (streakElement) {
                streakElement.textContent = `${data.streak} Days`;
                console.log('Streak updated:', data.streak);
            } else {
                console.error('Streak element not found. ID: streak-value');
            }
        })
        .catch(error => {
            console.error('Error fetching mood data:', error);

            // Fallback Mood Chart
            const moodCtx = moodCanvas.getContext('2d');
            const moodLineGradient = moodCtx.createLinearGradient(0, 0, 0, 650);
            moodLineGradient.addColorStop(0, '#FF6EC7');
            moodLineGradient.addColorStop(1, '#7879F1');
            const moodFillGradient = moodCtx.createLinearGradient(0, 0, 0, 650);
            moodFillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)');
            moodFillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)');

            new Chart(moodCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Mood',
                        data: [3, 3, 3, 3, 3, 3, 3],
                        borderColor: moodLineGradient,
                        borderWidth: 3,
                        fill: true,
                        backgroundColor: moodFillGradient,
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
                            min: 0,
                            ticks: {
                                stepSize: 1,
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Mood Score',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 5
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
                            display: true,
                            labels: {
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                },
                                color: '#000000'
                            }
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

            // Fallback Confidence Chart
            const confidenceCtx = confidenceCanvas.getContext('2d');
            const confidenceBarGradient = confidenceCtx.createLinearGradient(0, 0, 0, 650);
            confidenceBarGradient.addColorStop(0, '#00BFFF');
            confidenceBarGradient.addColorStop(1, '#1E90FF');

            new Chart(confidenceCtx, {
                type: 'bar',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Confidence',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: confidenceBarGradient,
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        borderRadius: 5,
                        barThickness: 20
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1,
                            min: 0,
                            ticks: {
                                stepSize: 0.2,
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 17
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)',
                            },
                            title: {
                                display: true,
                                text: 'Confidence Score',
                                color: '#000000',
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 20
                                },
                                padding: 5
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
                            display: true,
                            labels: {
                                font: {
                                    family: "'Poppins', sans-serif",
                                    size: 14
                                },
                                color: '#000000'
                            }
                        },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutCubic'
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