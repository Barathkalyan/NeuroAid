document.addEventListener('DOMContentLoaded', () => {
    const gratitudeForm = document.getElementById('gratitude-form');
    const gratitudeTimeline = document.getElementById('gratitude-timeline');
    const streakElement = document.getElementById('gratitude-streak');

    // Fetch and display gratitude entries and streak
    function fetchGratitudeEntries() {
        fetch('/api/gratitude')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    gratitudeTimeline.innerHTML = `<p>Error: ${data.error}</p>`;
                    streakElement.textContent = '0 Days';
                    return;
                }

                // Display streak
                streakElement.textContent = `${data.streak} Days`;

                // Display entries
                if (data.entries.length === 0) {
                    gratitudeTimeline.innerHTML = '<p>No gratitude entries yet. Start by adding one above!</p>';
                } else {
                    gratitudeTimeline.innerHTML = data.entries.map(entry => `
                        <div class="timeline-entry">
                            <div class="date">${entry.date}</div>
                            <div class="entry-content">
                                <p>1. ${entry.thing1}</p>
                                <p>2. ${entry.thing2}</p>
                                <p>3. ${entry.thing3}</p>
                            </div>
                        </div>
                    `).join('');
                }
            })
            .catch(error => {
                console.error('Error fetching gratitude entries:', error);
                gratitudeTimeline.innerHTML = '<p>Unable to load entries. Please try again later.</p>';
                streakElement.textContent = '0 Days';
            });
    }

    // Handle form submission
    gratitudeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const thing1 = document.getElementById('thing1').value.trim();
        const thing2 = document.getElementById('thing2').value.trim();
        const thing3 = document.getElementById('thing3').value.trim();

        if (!thing1 || !thing2 || !thing3) {
            alert('Please fill out all fields.');
            return;
        }

        try {
            const response = await fetch('/api/gratitude', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ thing1, thing2, thing3 }),
            });
            const data = await response.json();

            if (data.success) {
                alert('Gratitude entry saved successfully!');
                gratitudeForm.reset();
                fetchGratitudeEntries(); // Refresh entries
            } else {
                alert(`Error: ${data.error || 'Failed to save entry.'}`);
            }
        } catch (error) {
            console.error('Error saving gratitude entry:', error);
            alert('Unable to save entry. Please try again later.');
        }
    });

    // Initial fetch
    fetchGratitudeEntries();
});