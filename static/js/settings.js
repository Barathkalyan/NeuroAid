document.addEventListener('DOMContentLoaded', () => {
    const themeSelect = document.getElementById('theme');
    const themeStylesheet = document.getElementById('theme-stylesheet');

    // Preview theme when dropdown changes
    themeSelect.addEventListener('change', (e) => {
        const selectedTheme = e.target.value;
        themeStylesheet.href = `/static/css/themes/${selectedTheme}.css`;
    });

    // Optional: Client-side validation for password match
    const form = document.getElementById('settings-form');
    form.addEventListener('submit', (e) => {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        if (password && password !== confirmPassword) {
            e.preventDefault();
            alert('Passwords do not match!');
        }
    });
});