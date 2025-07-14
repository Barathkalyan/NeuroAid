// Password visibility toggle
function togglePassword(passwordId, toggleButton) {
  const passwordInput = document.getElementById(passwordId);
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleButton.textContent = 'Hide';
  } else {
    passwordInput.type = 'password';
    toggleButton.textContent = 'Show';
  }
}

// Handle password toggle for login page
document.addEventListener('DOMContentLoaded', () => {
  const togglePasswordLogin = document.querySelectorAll('.login-box .toggle-password');
  togglePasswordLogin.forEach(toggle => {
    toggle.addEventListener('click', function () {
      const passwordInput = this.previousElementSibling.previousElementSibling;
      togglePassword(passwordInput.id, this);
    });
  });

  // Handle password toggle for signup page
  const togglePasswordSignup = document.querySelectorAll('.signup-form .toggle-password');
  togglePasswordSignup.forEach(toggle => {
    toggle.addEventListener('click', function () {
      const passwordInput = this.previousElementSibling.previousElementSibling;
      togglePassword(passwordInput.id, this);
    });
  });

  document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('email').focus();
});

document.getElementById('login-form').addEventListener('submit', (e) => {
  const button = document.getElementById('login-button');
  button.disabled = true;
  button.querySelector('.spinner').style.display = 'block';
});

  // Handle form submission and error display for login
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      const button = document.getElementById('login-button');
      button.disabled = true;
      button.classList.add('submitting');

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
  }

  // Handle form submission and error display for signup (placeholder)
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', function(event) {
      const button = this.querySelector('button');
      button.disabled = true;
      button.classList.add('submitting');

      const generalError = document.getElementById('general-error');
      if (generalError) {
        const errorText = generalError.textContent;
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm-password');
        const emailError = document.getElementById('email-error') || document.createElement('p');
        const passwordError = document.getElementById('password-error') || document.createElement('p');
        const confirmPasswordError = document.getElementById('confirm-password-error') || document.createElement('p');

        if (errorText.includes('Email')) {
          emailError.textContent = 'Invalid email';
          emailError.style.display = 'block';
          emailInput.classList.add('input-error');
          if (!document.getElementById('email-error')) {
            emailInput.parentNode.appendChild(emailError);
            emailError.className = 'error-message';
            emailError.id = 'email-error';
          }
          event.preventDefault();
        } else if (errorText.includes('Password')) {
          passwordError.textContent = 'Invalid password';
          passwordError.style.display = 'block';
          passwordInput.classList.add('input-error');
          if (!document.getElementById('password-error')) {
            passwordInput.parentNode.appendChild(passwordError);
            passwordError.className = 'error-message';
            passwordError.id = 'password-error';
          }
          event.preventDefault();
        } else if (errorText.includes('Confirm Password')) {
          confirmPasswordError.textContent = 'Passwords do not match';
          confirmPasswordError.style.display = 'block';
          confirmPasswordInput.classList.add('input-error');
          if (!document.getElementById('confirm-password-error')) {
            confirmPasswordInput.parentNode.appendChild(confirmPasswordError);
            confirmPasswordError.className = 'error-message';
            confirmPasswordError.id = 'confirm-password-error';
          }
          event.preventDefault();
        }
        button.disabled = false;
        button.classList.remove('submitting');
      }
    });
  }

  // Clear error styles on input
  ['email', 'password', 'confirm-password'].forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.addEventListener('input', function() {
        this.classList.remove('input-error');
        const errorElement = document.getElementById(`${id}-error`);
        if (errorElement) errorElement.style.display = 'none';
      });
    }
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
});