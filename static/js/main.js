    // Password visibility toggle
function togglePassword() {
  const passwordInput = document.getElementById('password');
  const toggleButton = document.querySelector('.toggle-password');
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleButton.textContent = 'Hide';
  } else {
    passwordInput.type = 'password';
    toggleButton.textContent = 'Show';
  }
}

// Handle form submission and error display
document.getElementById('login-form').addEventListener('submit', function(event) {
  const button = document.getElementById('login-button');
  button.disabled = true;
  button.classList.add('submitting');

  // Check for specific error messages from server
  const generalError = document.getElementById('general-error');
  if (generalError) {
    const errorText = generalError.textContent;
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');

    if (errorText.includes('User not found') || errorText.includes('Email')) {
      emailError.textContent = 'Email not found';
      emailError.style.display = 'block';
      emailInput.classList.add('input-error');
      event.preventDefault();
      button.disabled = false;
      button.classList.remove('submitting');
    } else if (errorText.includes('Invalid credentials') || errorText.includes('password')) {
      passwordError.textContent = 'Incorrect password';
      passwordError.style.display = 'block';
      passwordInput.classList.add('input-error');
      event.preventDefault();
      button.disabled = false;
      button.classList.remove('submitting');
    }
  }
});

// Clear error styles on input
document.getElementById('email').addEventListener('input', function() {
  this.classList.remove('input-error');
  document.getElementById('email-error').style.display = 'none';
});

document.getElementById('password').addEventListener('input', function() {
  this.classList.remove('input-error');
  document.getElementById('password-error').style.display = 'none';
});

// Branding interactivity
const featureBlocks = document.querySelectorAll('.feature-block');
featureBlocks.forEach(block => {
  const icon = block.querySelector('.feature-icon');
  icon.addEventListener('click', (event) => {
    const ripple = document.createElement('div');
    ripple.classList.add('ripple');
    const rect = icon.getBoundingClientRect();
    const sceneRect = document.querySelector('.branding-scene').getBoundingClientRect();
    ripple.style.left = `${rect.left - sceneRect.left + rect.width / 2 - 50}px`; /* Center ripple */
    ripple.style.top = `${rect.top - sceneRect.top + rect.height / 2 - 50}px`;
    ripple.style.width = '100px';
    ripple.style.height = '100px';
    block.appendChild(ripple);
    block.style.transition = 'none'; // Disable transition for pause
    block.style.transform = 'scale(1.1)';
    setTimeout(() => {
      ripple.remove();
      block.style.transition = 'transform 0.3s ease';
      block.style.transform = 'scale(1)';
    }, 800);
  });

  icon.addEventListener('touchstart', (event) => {
    event.preventDefault();
    icon.classList.add('touched');
    const ripple = document.createElement('div');
    ripple.classList.add('ripple');
    const rect = icon.getBoundingClientRect();
    const sceneRect = document.querySelector('.branding-scene').getBoundingClientRect();
    ripple.style.left = `${rect.left - sceneRect.left + rect.width / 2 - 50}px`;
    ripple.style.top = `${rect.top - sceneRect.top + rect.height / 2 - 50}px`;
    ripple.style.width = '100px';
    ripple.style.height = '100px';
    block.appendChild(ripple);
    block.style.transition = 'none';
    block.style.transform = 'scale(1.1)';
    setTimeout(() => {
      ripple.remove();
      block.style.transition = 'transform 0.3s ease';
      block.style.transform = 'scale(1)';
      icon.classList.remove('touched');
    }, 800);
  });
});

// Dynamic quote changer
const quotes = [
  "Take a moment to breathe deeply.",
  "Your mind deserves peace today.",
  "Connect with your inner strength.",
  "Every step forward is progress.",
  "Embrace the journey of healing."
];
let quoteIndex = 0;
const quoteElement = document.getElementById('quote');

function changeQuote() {
  quoteElement.style.opacity = 0;
  setTimeout(() => {
    quoteIndex = (quoteIndex + 1) % quotes.length;
    quoteElement.textContent = quotes[quoteIndex];
    quoteElement.style.opacity = 1;
  }, 500);
}

setInterval(changeQuote, 5000);
changeQuote(); // Initial call