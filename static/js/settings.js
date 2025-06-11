document.addEventListener('DOMContentLoaded', () => {
    const themeSelect = document.getElementById('theme');
    const themeStylesheet = document.getElementById('theme-stylesheet');

    // Preview theme when dropdown changes
    themeSelect.addEventListener('change', (e) => {
        const selectedTheme = e.target.value;
        themeStylesheet.href = `/static/css/themes/${selectedTheme}.css`;
    });

    // Client-side validation for password match
    const form = document.getElementById('settings-form');
    form.addEventListener('submit', (e) => {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        if (password && password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match!');
        }
    });

    // Privacy & Security actions
    const exportDataBtn = document.getElementById('export-data-btn');
    const deleteAccountBtn = document.getElementById('delete-account-btn');

    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/export_data', {
                    method: 'GET'
                });
                const data = await response.json();
                if (data.success) {
                    const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'neuroaid_user_data.json';
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error exporting data:', error);
                alert('Failed to export data.');
            }
        });
    }

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
                        alert('Account deleted successfully.');
                        window.location.href = '/logout';
                    } else {
                        alert(data.error);
                    }
                } catch (error) {
                    console.error('Error deleting account:', error);
                    alert('Failed to delete account.');
                }
            }
        });
    }
});