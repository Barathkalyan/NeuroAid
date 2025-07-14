document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('verify-2fa-form');
  const submitButton = form?.querySelector('button');
  if (form && submitButton) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const code = document.getElementById('code').value.trim();

      // Client-side validation
      if (!/^\d{6}$/.test(code)) {
        const errorMessage = document.querySelector('.error-message') || document.createElement('p');
        errorMessage.className = 'error-message';
        errorMessage.textContent = 'Please enter a valid 6-digit code';
        errorMessage.style.display = 'block';
        form.parentElement.insertBefore(errorMessage, form);
        return;
      }

      submitButton.classList.add('submitting');
      submitButton.disabled = true;

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
          },
          body: JSON.stringify({ code })
        });
        const data = await response.json();
        if (data.success) {
          const successMessage = document.querySelector('.success-message') || document.createElement('p');
          successMessage.className = 'success-message';
          successMessage.textContent = data.message || '2FA verified successfully!';
          successMessage.style.display = 'block';
          form.parentElement.insertBefore(successMessage, form);
          setTimeout(() => {
            window.location.href = '/dashboard'; // Redirect to dashboard or home
          }, 1000);
        } else {
          const errorMessage = document.querySelector('.error-message') || document.createElement('p');
          errorMessage.className = 'error-message';
          errorMessage.textContent = data.error || 'Invalid 2FA code';
          errorMessage.style.display = 'block';
          form.parentElement.insertBefore(errorMessage, form);
        }
      } catch (error) {
        console.error('Error verifying 2FA:', error);
        const errorMessage = document.querySelector('.error-message') || document.createElement('p');
        errorMessage.className = 'error-message';
        errorMessage.textContent = 'Failed to verify 2FA';
        errorMessage.style.display = 'block';
        form.parentElement.insertBefore(errorMessage, form);
      } finally {
        submitButton.classList.remove('submitting');
        submitButton.disabled = false;
      }
    });
  }
});