document.addEventListener('DOMContentLoaded', function () {
    const gratitudeForm = document.getElementById('gratitude-form');
    const gratitudeTimeline = document.getElementById('gratitude-timeline');
    const streakElement = document.getElementById('gratitude-streak');

    // Function to fetch and display gratitude entries
    function fetchGratitudeEntries() {
        fetch('/api/gratitude')
            .then(response => response.json())
            .then(data => {
                console.log('Gratitude Entries:', data.entries);
                console.log('Gratitude Streak:', data.streak);

                // Update streak
                streakElement.textContent = `${data.streak} Days`;

                // Display entries in timeline
                if (data.entries.length === 0) {
                    gratitudeTimeline.innerHTML = '<p>No gratitude entries yet. Start by recording three good things today!</p>';
                    return;
                }

                const timelineHTML = data.entries.map(entry => `
                    <div class="timeline-entry">
                        <div class="date">${entry.date}</div>
                        <div class="entry-content">
                            <p><strong>1. What made you smile:</strong> ${entry.thing1}</p>
                            <p><strong>2. What you’re thankful for:</strong> ${entry.thing2}</p>
                            <p><strong>3. What went well:</strong> ${entry.thing3}</p>
                        </div>
                    </div>
                `).join('');
                gratitudeTimeline.innerHTML = timelineHTML;
            })
            .catch(error => {
                console.error('Error fetching gratitude entries:', error);
                gratitudeTimeline.innerHTML = '<p>Unable to load gratitude entries. Please try again later.</p>';
            });
    }

    // Submit new gratitude entry
    gratitudeForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const thing1 = document.getElementById('thing1').value.trim();
        const thing2 = document.getElementById('thing2').value.trim();
        const thing3 = document.getElementById('thing3').value.trim();

        if (!thing1 || !thing2 || !thing3) {
            alert('Please fill in all three fields.');
            return;
        }

        const entry = { thing1, thing2, thing3 };

        fetch('/api/gratitude', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    gratitudeForm.reset();
                    fetchGratitudeEntries(); // Refresh timeline and streak
                } else {
                    alert('Failed to save gratitude entry. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error saving gratitude entry:', error);
                alert('Failed to save gratitude entry. Please try again.');
            });
    });

    // Initial fetch of gratitude entries
    fetchGratitudeEntries();
});