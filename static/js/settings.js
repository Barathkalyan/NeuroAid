document.addEventListener('DOMContentLoaded', () => {
    const themeSelect = document.getElementById('theme');
    const themeStylesheet = document.getElementById('theme-stylesheet');
    const form = document.getElementById('settings-form');
    const exportDataBtn = document.getElementById('export-data-btn');
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    const errorMessage = document.querySelector('.error-message');
    const successMessage = document.querySelector('.success-message');

    // Function to display messages
    const showMessage = (type, message) => {
        if (type === 'error') {
            if (errorMessage) errorMessage.textContent = message;
            else {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'error-message';
                msgDiv.textContent = message;
                form.parentNode.insertBefore(msgDiv, form);
            }
        } else {
            if (successMessage) successMessage.textContent = message;
            else {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'success-message';
                msgDiv.textContent = message;
                form.parentNode.insertBefore(msgDiv, form);
            }
        }
        setTimeout(() => {
            const msg = document.querySelector(`.${type}-message`);
            if (msg) msg.remove();
        }, 5000);
    };

    // Preview theme when dropdown changes
    themeSelect.addEventListener('change', (e) => {
        const selectedTheme = e.target.value;
        themeStylesheet.href = `/static/css/themes/${selectedTheme}.css`;
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const twoFactorEnabled = document.getElementById('two_factor_enabled').checked;

        // Client-side password validation
        if (password && password !== confirmPassword) {
            showMessage('error', 'Passwords do not match!');
            return;
        }

        const formData = new FormData(form);

        try {
            const response = await fetch('/settings', {
                method: 'POST',
                body: formData // Send FormData instead of JSON
            });

            // Check if the response is a redirect
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const result = await response.json();

            if (result.success) {
                showMessage('success', result.message || 'Settings updated successfully!');
                // Update displayed email in header
                const userMenuSpan = document.querySelector('.user-menu span');
                if (userMenuSpan) {
                    userMenuSpan.textContent = formData.get('email').split('@')[0];
                }
                // Update theme stylesheet if changed
                themeStylesheet.href = `/static/css/themes/${formData.get('theme')}.css`;
                // Redirect to /setup_2fa if 2FA is enabled
                if (twoFactorEnabled) {
                    window.location.href = '/setup_2fa';
                }
            } else {
                showMessage('error', result.error || 'Failed to update settings.');
            }
        } catch (error) {
            console.error('Error submitting settings:', error);
            showMessage('error', 'Failed to update settings.');
        }
    });

    // Export Data button
    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/export_data', { method: 'GET' });
                const data = await response.json();
                if (data.success) {
                    const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'neuroaid_user_data.json';
                    a.click();
                    window.URL.revokeObjectURL(url);
                    showMessage('success', 'Data exported successfully!');
                } else {
                    showMessage('error', data.error || 'Failed to export data.');
                }
            } catch (error) {
                console.error('Error exporting data:', error);
                showMessage('error', 'Failed to export data.');
            }
        });
    }

    // Delete Account button
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
                try {
                    const response = await fetch('/delete_account', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await response.json();
                    if (data.success) {
                        showMessage('success', 'Account deleted successfully.');
                        setTimeout(() => {
                            window.location.href = '/logout';
                        }, 2000);
                    } else {
                        showMessage('error', data.error || 'Failed to delete account.');
                    }
                } catch (error) {
                    console.error('Error deleting account:', error);
                    showMessage('error', 'Failed to delete account.');
                }
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
  const toggle2FA = document.getElementById('two_factor_enabled');
  const codeGroup = document.getElementById('disable-2fa-code-group');

  if (toggle2FA && codeGroup) {
    toggle2FA.addEventListener('change', function () {
      if (!this.checked) {
        codeGroup.style.display = 'block'; // Show input when disabling
      } else {
        codeGroup.style.display = 'none';
      }
    });

    // Trigger on page load in case already unchecked
    toggle2FA.dispatchEvent(new Event('change'));
  }
});
