document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('setup-2fa-form');
  const submitButton = form?.querySelector('button');
  if (form && submitButton) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      submitButton.classList.add('submitting');
      submitButton.disabled = true;

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''
          },
          body: JSON.stringify({})
        });
        const data = await response.json();
        if (data.success) {
          const qrImage = document.getElementById('qr-image');
          const qrSecret = document.getElementById('qr-secret');
          const qrSection = document.getElementById('qr-section');

          qrImage.src = 'data:image/png;base64,' + data.qr_code;
          qrSecret.textContent = data.secret;
          qrSection.style.display = 'block';

          // Hide form after generating
          form.style.display = 'none';
        }


        else {
          const errorMessage = document.querySelector('.error-message') || document.createElement('p');
          errorMessage.className = 'error-message';
          errorMessage.textContent = data.error || 'Failed to generate QR code';
          errorMessage.style.display = 'block';
          form.parentElement.insertBefore(errorMessage, form);
        }
      } catch (error) {
        console.error('Error generating QR code:', error);
        const errorMessage = document.querySelector('.error-message') || document.createElement('p');
        errorMessage.className = 'error-message';
        errorMessage.textContent = 'Failed to generate QR code';
        errorMessage.style.display = 'block';
        form.parentElement.insertBefore(errorMessage, form);
      } finally {
        submitButton.classList.remove('submitting');
        submitButton.disabled = false;
      }
    });
  }
});