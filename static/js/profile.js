document.addEventListener('DOMContentLoaded', () => {
  // Feedback message function
  const showFeedback = (message, type = 'success') => {
    const feedback = document.createElement('div');
    feedback.className = `feedback feedback-${type}`;
    feedback.textContent = message;
    feedback.style.position = 'fixed';
    feedback.style.top = '16px';
    feedback.style.right = '16px';
    feedback.style.padding = '10px 16px';
    feedback.style.borderRadius = '8px';
    feedback.style.color = '#fff';
    feedback.style.background = type === 'success' ? '#10b981' : '#ef4444';
    feedback.style.zIndex = '1000';
    feedback.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(feedback);
    setTimeout(() => {
      feedback.style.opacity = '0';
      setTimeout(() => feedback.remove(), 300);
    }, 3000);
  };

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
      if (!file) return;

      const formData = new FormData();
      formData.append('profile-pic', file);
      editPictureBtn.disabled = true;
      editPictureBtn.textContent = 'Uploading...';

      try {
        const response = await fetch('/upload_profile_pic', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();
        if (data.success) {
          document.getElementById('profile-pic').src = data.url;
          document.getElementById('header-profile-pic').src = data.url;
          showFeedback('Profile picture updated successfully!');
        } else {
          showFeedback(data.error || 'Failed to upload profile picture.', 'error');
        }
      } catch (error) {
        console.error('Error uploading profile picture:', error);
        showFeedback('Failed to upload profile picture.', 'error');
      } finally {
        editPictureBtn.disabled = false;
        editPictureBtn.textContent = 'Change Picture';
      }
    });
  }

  // Edit field functionality
  const editButtons = document.querySelectorAll('.edit-field-btn');
  if (editButtons.length === 0) {
    console.warn('No edit buttons found for name or username');
  } else {
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
            showFeedback(`Please enter a valid ${field}`, 'error');
            return;
          }

          // Save to backend
          button.disabled = true;
          button.textContent = 'Saving...';
          input.disabled = true;

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
              input.classList.remove('editable');
              button.textContent = 'Edit';
              showFeedback(`${field.charAt(0).toUpperCase() + field.slice(1)} updated successfully!`);
              updateProfileCompletion();
            } else {
              showFeedback(data.error || `Failed to update ${field}.`, 'error');
              input.disabled = false;
              button.disabled = false;
              button.textContent = 'Save';
            }
          } catch (error) {
            console.error(`Error updating ${field}:`, error);
            showFeedback(`Failed to update ${field}.`, 'error');
            input.disabled = false;
            button.disabled = false;
            button.textContent = 'Save';
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
      savePersonalDetailsBtn.textContent = 'Saving...';
      const personalDetails = {
        age: document.getElementById('age-input').value || null,
        gender: document.getElementById('gender-input').value || null,
        location: document.getElementById('location-input').value || null,
        preferred_language: document.getElementById('language-input').value || null
      };

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
          // Update input fields with returned values to ensure consistency
          document.getElementById('age-input').value = data.profile_data?.age || '';
          document.getElementById('gender-input').value = data.profile_data?.gender || '';
          document.getElementById('location-input').value = data.profile_data?.location || '';
          document.getElementById('language-input').value = data.profile_data?.preferred_language || '';
          showFeedback('Personal details saved successfully!');
          updateProfileCompletion();
          savePersonalDetailsBtn.disabled = false;
          savePersonalDetailsBtn.textContent = 'Save';
        } else {
          showFeedback(data.error || 'Failed to save personal details.', 'error');
          savePersonalDetailsBtn.disabled = false;
          savePersonalDetailsBtn.textContent = 'Save';
        }
      } catch (error) {
        console.error('Error saving personal details:', error);
        showFeedback('Failed to save personal details.', 'error');
        savePersonalDetailsBtn.disabled = false;
        savePersonalDetailsBtn.textContent = 'Save';
      }
    });
  }

  // Save mental health goals
  const saveGoalsBtn = document.getElementById('save-goals');
  if (saveGoalsBtn) {
    saveGoalsBtn.addEventListener('click', async () => {
      saveGoalsBtn.disabled = true;
      saveGoalsBtn.textContent = 'Saving...';
      const activities = Array.from(document.querySelectorAll('input[name="activities"]:checked')).map(input => input.value);
      const goals = {
        primary_goal: document.getElementById('primary-goal').value || null,
        engagement_frequency: document.getElementById('frequency').value || null,
        preferred_activities: activities
      };

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
          showFeedback('Mental health goals saved successfully!');
          updateProfileCompletion();
          saveGoalsBtn.disabled = false;
          saveGoalsBtn.textContent = 'Save';
        } else {
          showFeedback(data.error || 'Failed to save mental health goals.', 'error');
          saveGoalsBtn.disabled = false;
          saveGoalsBtn.textContent = 'Save';
        }
      } catch (error) {
        console.error('Error saving mental health goals:', error);
        showFeedback('Failed to save mental health goals.', 'error');
        saveGoalsBtn.disabled = false;
        saveGoalsBtn.textContent = 'Save';
      }
    });
  }

  // Update profile completion dynamically
  const updateProfileCompletion = async () => {
    try {
      const response = await fetch('/api/profile_completion', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        const progressText = document.querySelector('.progress-text');
        const progressCircle = document.querySelector('.progress-ring__circle');
        progressText.textContent = `${data.completion_percentage}% Complete`;
        progressCircle.style.strokeDasharray = `${data.completion_dasharray} 276.46`;
        const ctaMessage = document.querySelector('.cta-message');
        if (ctaMessage && data.completion_percentage === 100) {
          ctaMessage.style.display = 'none';
        }
        const overviewStatus = document.querySelector('.profile-overview .section-status');
        const personalDetailsStatus = document.querySelector('.personal-details .section-status');
        const mentalHealthGoalsStatus = document.querySelector('.mental-health-goals .section-status');
        if (overviewStatus) {
          overviewStatus.style.display = data.overview_complete ? 'inline-block' : 'none';
        }
        if (personalDetailsStatus) {
          personalDetailsStatus.style.display = data.personal_details_complete ? 'inline-block' : 'none';
        }
        if (mentalHealthGoalsStatus) {
          mentalHealthGoalsStatus.style.display = data.mental_health_goals_complete ? 'inline-block' : 'none';
        }
      }
    } catch (error) {
      console.error('Error updating profile completion:', error);
    }
  };
});

// Add feedback styles dynamically
const style = document.createElement('style');
style.textContent = `
  .feedback {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  .feedback-success {
    background: #10b981;
  }
  .feedback-error {
    background: #ef4444;
  }
`;
document.head.appendChild(style);