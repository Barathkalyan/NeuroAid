document.addEventListener('DOMContentLoaded', () => {
    // Profile picture upload
    const editPictureBtn = document.getElementById('edit-picture-btn');
    if (editPictureBtn) {
        editPictureBtn.addEventListener('click', () => {
            document.getElementById('profile-pic-input').click();
        });
    }

    const profilePicInput = document.getElementById('profile-pic-input');
    if (profilePicInput) {
        profilePicInput.addEventListener('change', async (event) => {
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
                        alert(data.error || 'Failed to upload profile picture.');
                    }
                } catch (error) {
                    console.error('Error uploading profile picture:', error);
                    alert('Failed to upload profile picture.');
                }
            }
        });
    }

    // Edit field functionality
    const editButtons = document.querySelectorAll('.edit-field-btn');
    if (editButtons.length === 0) {
        console.error('No edit buttons found for name or username');
    } else {
        console.log(`Found ${editButtons.length} edit buttons`);
        editButtons.forEach(button => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                const field = button.getAttribute('data-field');
                const input = document.getElementById(`${field}-input`);
                if (!input) {
                    console.error(`Input for ${field} not found`);
                    return;
                }

                const isEditing = !input.classList.contains('editable');
                console.log(`Toggling ${field}: ${isEditing ? 'Start editing' : 'Saving'}`);

                if (isEditing) {
                    // Start editing
                    input.disabled = false;
                    input.classList.add('editable');
                    button.textContent = 'Save';
                    input.focus();
                } else {
                    // Validate input
                    const value = input.value.trim();
                    if (!value) {
                        alert(`Please enter a valid ${field}`);
                        return;
                    }

                    // Disable button and input during save
                    button.disabled = true;
                    input.disabled = true;

                    // Save to backend
                    try {
                        const response = await fetch('/update_profile_field', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                            },
                            body: JSON.stringify({ field, value })
                        });
                        const data = await response.json();
                        if (data.success) {
                            console.log(`${field} saved successfully`);
                            input.classList.remove('editable');
                            button.textContent = 'Edit';
                            window.location.reload();
                        } else {
                            console.error(`Error saving ${field}:`, data.error);
                            alert(data.error || `Failed to update ${field}.`);
                            input.disabled = false;
                            button.disabled = false;
                        }
                    } catch (error) {
                        console.error(`Error updating ${field}:`, error);
                        alert(`Failed to update ${field}.`);
                        input.disabled = false;
                        button.disabled = false;
                    }
                }
            });
        });
    }

    // Save personal details
    const savePersonalDetailsBtn = document.getElementById('save-personal-details');
    if (savePersonalDetailsBtn) {
        savePersonalDetailsBtn.addEventListener('click', async () => {
            savePersonalDetailsBtn.disabled = true;
            const personalDetails = {
                age: document.getElementById('age-input').value || null,
                gender: document.getElementById('gender-input').value || null,
                location: document.getElementById('location-input').value || null,
                preferred_language: document.getElementById('language-input').value || null
            };
            console.log('Saving personal details:', personalDetails);
            try {
                const response = await fetch('/update_personal_details', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    body: JSON.stringify(personalDetails)
                });
                const data = await response.json();
                if (data.success) {
                    console.log('Personal details saved successfully');
                    alert('Personal details saved successfully!');
                    window.location.reload();
                } else {
                    console.error('Error saving personal details:', data.error);
                    alert(data.error || 'Failed to save personal details.');
                    savePersonalDetailsBtn.disabled = false;
                }
            } catch (error) {
                console.error('Error saving personal details:', error);
                alert('Failed to save personal details.');
                savePersonalDetailsBtn.disabled = false;
            }
        });
    }

    // Save mental health goals
    const saveGoalsBtn = document.getElementById('save-goals');
    if (saveGoalsBtn) {
        saveGoalsBtn.addEventListener('click', async () => {
            saveGoalsBtn.disabled = true;
            const activities = Array.from(document.querySelectorAll('input[name="activities"]:checked')).map(input => input.value);
            const goals = {
                primary_goal: document.getElementById('primary-goal').value || null,
                engagement_frequency: document.getElementById('frequency').value || null,
                preferred_activities: activities
            };
            console.log('Saving mental health goals:', goals);
            try {
                const response = await fetch('/update_mental_health_goals', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    body: JSON.stringify(goals)
                });
                const data = await response.json();
                if (data.success) {
                    console.log('Mental health goals saved successfully');
                    alert('Mental health goals saved successfully!');
                    window.location.reload();
                } else {
                    console.error('Error saving mental health goals:', data.error);
                    alert(data.error || 'Failed to save mental health goals.');
                    saveGoalsBtn.disabled = false;
                }
            } catch (error) {
                console.error('Error saving mental health goals:', error);
                alert('Failed to save mental health goals.');
                saveGoalsBtn.disabled = false;
            }
        });
    }
});