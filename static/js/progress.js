document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('moodChart');
    canvas.width = 900;
    canvas.height = 650;

    fetch('/api/mood_data')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data);

            // Mood Chart (Chart.js)
            const ctx = canvas.getContext('2d');
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 650);
            lineGradient.addColorStop(0, '#FF6EC7');
            lineGradient.addColorStop(1, '#7879F1');
            const fillGradient = ctx.createLinearGradient(0, 0, 0, 650);
            fillGradient.addColorStop(0, 'rgba(230, 230, 250, 0.5)');
            fillGradient.addColorStop(1, 'rgba(200, 200, 240, 0.1)');

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
                            const day = data.labels[element.index];
                            alert(`Day: ${day}`);
                        }
                    }
                }
            });

            // Confidence Chart (ApexCharts)
            const confidenceOptions = {
                chart: {
                    type: 'line',
                    height: 400,
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800
                    }
                },
                series: [{
                    name: 'Confidence',
                    data: data.confidence
                }],
                xaxis: {
                    categories: data.labels,
                    labels: {
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '14px',
                            colors: '#000000'
                        }
                    },
                    title: {
                        text: 'Day',
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#000000'
                        }
                    }
                },
                yaxis: {
                    min: 0,
                    max: 1,
                    tickAmount: 5,
                    labels: {
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '14px',
                            colors: '#000000'
                        }
                    },
                    title: {
                        text: 'Confidence Score',
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#000000'
                        }
                    }
                },
                stroke: {
                    curve: 'smooth',
                    width: 3
                },
                colors: ['#7879F1'],
                markers: {
                    size: 5,
                    hover: {
                        size: 7
                    }
                },
                tooltip: {
                    style: {
                        fontFamily: "'Poppins', sans-serif"
                    }
                }
            };

            const confidenceChart = new ApexCharts(document.querySelector("#confidenceChart"), confidenceOptions);
            confidenceChart.render();

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

            // Fallback Confidence Chart
            const confidenceOptions = {
                chart: {
                    type: 'line',
                    height: 400,
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800
                    }
                },
                series: [{
                    name: 'Confidence',
                    data: [0, 0, 0, 0, 0, 0, 0]
                }],
                xaxis: {
                    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    labels: {
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '14px',
                            colors: '#000000'
                        }
                    },
                    title: {
                        text: 'Day',
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#000000'
                        }
                    }
                },
                yaxis: {
                    min: 0,
                    max: 1,
                    tickAmount: 5,
                    labels: {
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '14px',
                            colors: '#000000'
                        }
                    },
                    title: {
                        text: 'Confidence Score',
                        style: {
                            fontFamily: "'Poppins', sans-serif",
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#000000'
                        }
                    }
                },
                stroke: {
                    curve: 'smooth',
                    width: 3
                },
                colors: ['#7879F1'],
                markers: {
                    size: 5,
                    hover: {
                        size: 7
                    }
                },
                tooltip: {
                    style: {
                        fontFamily: "'Poppins', sans-serif"
                    }
                }
            };

            const confidenceChart = new ApexCharts(document.querySelector("#confidenceChart"), confidenceOptions);
            confidenceChart.render();
        });
});