document.addEventListener('DOMContentLoaded', () => {
  // Load profile data from localStorage
  let profileData = JSON.parse(localStorage.getItem('profileData')) || {
    name: 'John Doe',
    email: 'john.doe@example.com',
    username: '@johndoe',
    age: '',
    gender: '',
    location: '',
    language: '',
    primaryGoal: '',
    frequency: '',
    activities: [],
    profilePic: 'https://randomuser.me/api/portraits/men/32.jpg'
  };

  // Initialize UI
  const initializeUI = () => {
    document.getElementById('name-input').value = profileData.name;
    document.getElementById('email-input').value = profileData.email;
    document.getElementById('username-input').value = profileData.username;
    document.getElementById('age-input').value = profileData.age;
    document.getElementById('gender-input').value = profileData.gender;
    document.getElementById('location-input').value = profileData.location;
    document.getElementById('language-input').value = profileData.language;
    document.getElementById('primary-goal').value = profileData.primaryGoal;
    document.getElementById('frequency').value = profileData.frequency;

    const activitiesCheckboxes = document.querySelectorAll('input[name="activities"]');
    activitiesCheckboxes.forEach(checkbox => {
      checkbox.checked = profileData.activities.includes(checkbox.value);
    });

    const profilePic = document.getElementById('profile-pic');
    const headerProfilePic = document.getElementById('header-profile-pic');
    profilePic.src = profileData.profilePic;
    headerProfilePic.src = profileData.profilePic;

    updateProfileCompletion();
  };

  // Update profile completion status
  const updateProfileCompletion = () => {
    const percentage = calculateProfileCompletion(profileData);
    updateProgressBar(percentage);

    // Update status indicators
    const personalDetailsStatus = document.querySelector('.personal-details .status-indicator');
    const goalsStatus = document.querySelector('.mental-health-goals .status-indicator');
    const ctaMessage = document.querySelector('.cta-message p');

    const personalDetailsFilled = profileData.age || profileData.gender || profileData.location || profileData.language;
    personalDetailsStatus.textContent = personalDetailsFilled ? 'Personal Details: Complete' : 'Personal Details: Not Started';
    personalDetailsStatus.classList.toggle('complete', personalDetailsFilled);
    personalDetailsStatus.classList.toggle('incomplete', !personalDetailsFilled);

    const goalsFilled = profileData.primaryGoal || profileData.frequency || profileData.activities.length > 0;
    goalsStatus.textContent = goalsFilled ? 'Goals: Complete' : 'Goals: Not Started';
    goalsStatus.classList.toggle('complete', goalsFilled);
    goalsStatus.classList.toggle('incomplete', !goalsFilled);

    if (percentage < 100) {
      ctaMessage.textContent = 'Complete your profile to unlock personalized features! Add your mental health goals to continue.';
    } else {
      ctaMessage.textContent = 'Great job! Your profile is fully complete. Enjoy a personalized NeuroAid experience.';
    }
  };

  // Edit Profile Fields
  const editFieldButtons = document.querySelectorAll('.edit-field-btn');
  editFieldButtons.forEach(button => {
    button.addEventListener('click', () => {
      const field = button.dataset.field;
      const input = document.getElementById(`${field}-input`);
      const isEditing = !input.readOnly;

      if (isEditing) {
        input.readOnly = true;
        button.textContent = 'Edit';
        profileData[field] = input.value;
        localStorage.setItem('profileData', JSON.stringify(profileData));
        updateProfileCompletion();
      } else {
        input.readOnly = false;
        input.focus();
        button.textContent = 'Save';
      }
    });
  });

  // Profile Picture Upload
  const editPictureBtn = document.getElementById('edit-picture-btn');
  const profilePicInput = document.getElementById('profile-pic-input');
  editPictureBtn.addEventListener('click', () => {
    profilePicInput.click();
  });

  profilePicInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        profileData.profilePic = event.target.result;
        document.getElementById('profile-pic').src = profileData.profilePic;
        document.getElementById('header-profile-pic').src = profileData.profilePic;
        localStorage.setItem('profileData', JSON.stringify(profileData));
      };
      reader.readAsDataURL(file);
    }
  });

  // Save Personal Details
  const savePersonalDetailsBtn = document.getElementById('save-personal-details');
  savePersonalDetailsBtn.addEventListener('click', () => {
    profileData.age = document.getElementById('age-input').value;
    profileData.gender = document.getElementById('gender-input').value;
    profileData.location = document.getElementById('location-input').value;
    profileData.language = document.getElementById('language-input').value;
    localStorage.setItem('profileData', JSON.stringify(profileData));
    updateProfileCompletion();
  });

  // Save Mental Health Goals
  const saveGoalsBtn = document.getElementById('save-goals');
  saveGoalsBtn.addEventListener('click', () => {
    profileData.primaryGoal = document.getElementById('primary-goal').value;
    profileData.frequency = document.getElementById('frequency').value;
    const activitiesCheckboxes = document.querySelectorAll('input[name="activities"]:checked');
    profileData.activities = Array.from(activitiesCheckboxes).map(checkbox => checkbox.value);
    localStorage.setItem('profileData', JSON.stringify(profileData));
    updateProfileCompletion();
  });

  // Privacy & Security Actions (Placeholder Functionality)
  document.getElementById('change-password-btn').addEventListener('click', () => {
    alert('Change Password functionality coming soon!');
  });

  document.getElementById('export-data-btn').addEventListener('click', () => {
    alert('Export Data functionality coming soon!');
  });

  document.getElementById('delete-account-btn').addEventListener('click', () => {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      localStorage.removeItem('profileData');
      alert('Account deleted successfully.');
      window.location.href = 'index.html';
    }
  });

  // Initialize the UI on page load
  initializeUI();
});