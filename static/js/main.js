// Password toggle functionality
document.addEventListener('DOMContentLoaded', () => {
  // Toggle password visibility for login page
  const togglePasswordLogin = document.querySelectorAll('.login-box .toggle-password');
  togglePasswordLogin.forEach(toggle => {
    toggle.addEventListener('click', function () {
      const passwordInput = this.previousElementSibling.previousElementSibling;
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      this.textContent = type === 'password' ? 'Show' : 'Hide';
    });
  });

  // Toggle password visibility for signup page
  const togglePasswordSignup = document.querySelectorAll('.signup-form .toggle-password');
  togglePasswordSignup.forEach(toggle => {
    toggle.addEventListener('click', function () {
      const passwordInput = this.previousElementSibling.previousElementSibling;
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      this.textContent = type === 'password' ? 'Show' : 'Hide';
    });
  });

  // Form submission handling (example)
  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      // Add login validation if needed
    });
  }
  if (signupForm) {
    signupForm.addEventListener('submit', (e) => {
      // Add signup validation if needed
    });
  }
});