const calculateProfileCompletion = (profileData) => {
  const totalFields = 7; // Name, Email, Username, Age, Gender, Location, Language, Primary Goal, Frequency, Activities
  let filledFields = 0;

  // Profile Overview
  if (profileData.name) filledFields++;
  if (profileData.email) filledFields++;
  if (profileData.username) filledFields++;

  // Personal Details
  if (profileData.age) filledFields++;
  if (profileData.gender) filledFields++;
  if (profileData.location) filledFields++;
  if (profileData.language) filledFields++;

  // Mental Health Goals
  if (profileData.primaryGoal) filledFields++;
  if (profileData.frequency) filledFields++;
  if (profileData.activities && profileData.activities.length > 0) filledFields++;

  const percentage = Math.round((filledFields / totalFields) * 100);
  return percentage;
};

const updateProgressBar = (percentage) => {
  const circle = document.querySelector('.progress-ring__circle');
  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;

  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = circumference;

  const offset = circumference - (percentage / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  const progressText = document.querySelector('.progress-text');
  progressText.textContent = `${percentage}% Complete`;
};