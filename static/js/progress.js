document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('moodChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Mood Score',
                data: [7, 5, 8, 7, 9, 6, 7],
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124, 58, 237, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    title: {
                        display: true,
                        text: 'Mood Score',
                        color: '#2d2d2d',
                        font: { size: 14 }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Day',
                        color: '#2d2d2d',
                        font: { size: 14 }
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#2d2d2d',
                        font: { size: 14 }
                    }
                }
            }
        }
    });
});