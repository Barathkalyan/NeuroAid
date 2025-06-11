document.addEventListener('DOMContentLoaded', () => {
    // Profile picture upload
    document.getElementById('edit-picture-btn').addEventListener('click', () => {
        document.getElementById('profile-pic-input').click();
    });

    document.getElementById('profile-pic-input').addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('profile-pic', file);
            try {
                const response = await fetch('/upload_profile_pic', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('profile-pic').src = data.url;
                    document.getElementById('header-profile-pic').src = data.url;
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error uploading profile picture:', error);
                alert('Failed to upload profile picture.');
            }
        }
    });

    // Edit field functionality
    document.querySelectorAll('.edit-field-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const field = button.getAttribute('data-field');
            const input = document.getElementById(`${field}-input`);
            const isEditing = input.hasAttribute('readonly');

            if (isEditing) {
                input.removeAttribute('readonly');
                input.focus();
                button.textContent = 'Save';
            } else {
                input.setAttribute('readonly', true);
                button.textContent = 'Edit';

                // Save the updated field to Supabase
                const value = input.value;
                console.log(`Saving ${field}: ${value}`); // Log the data being sent
                try {
                    const response = await fetch('/update_profile_field', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ field, value })
                    });
                    const data = await response.json();
                    if (data.success) {
                        console.log(`${field} saved successfully`);
                    } else {
                        console.error(`Error saving ${field}:`, data.error);
                        alert(data.error);
                    }
                } catch (error) {
                    console.error(`Error updating ${field}:`, error);
                    alert(`Failed to update ${field}.`);
                }
            }
        });
    });

    // Save personal details
    document.getElementById('save-personal-details').addEventListener('click', async () => {
        const personalDetails = {
            age: document.getElementById('age-input').value || null,
            gender: document.getElementById('gender-input').value || null,
            location: document.getElementById('location-input').value || null,
            preferred_language: document.getElementById('language-input').value || null
        };
        console.log('Saving personal details:', personalDetails); // Log the data being sent
        try {
            const response = await fetch('/update_personal_details', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(personalDetails)
            });
            const data = await response.json();
            if (data.success) {
                console.log('Personal details saved successfully');
                alert('Personal details saved successfully!');
                window.location.reload();
            } else {
                console.error('Error saving personal details:', data.error);
                alert(data.error);
            }
        } catch (error) {
            console.error('Error saving personal details:', error);
            alert('Failed to save personal details.');
        }
    });

    // Save mental health goals
    document.getElementById('save-goals').addEventListener('click', async () => {
        const activities = Array.from(document.querySelectorAll('input[name="activities"]:checked')).map(input => input.value);
        const goals = {
            primary_goal: document.getElementById('primary-goal').value || null,
            engagement_frequency: document.getElementById('frequency').value || null,
            preferred_activities: activities
        };
        console.log('Saving mental health goals:', goals); // Log the data being sent
        try {
            const response = await fetch('/update_mental_health_goals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(goals)
            });
            const data = await response.json();
            if (data.success) {
                console.log('Mental health goals saved successfully');
                alert('Mental health goals saved successfully!');
                window.location.reload();
            } else {
                console.error('Error saving mental health goals:', data.error);
                alert(data.error);
            }
        } catch (error) {
            console.error('Error saving mental health goals:', error);
            alert('Failed to save mental health goals.');
        }
    });
});