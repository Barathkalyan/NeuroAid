document.addEventListener('DOMContentLoaded', () => {
    const profile = document.querySelector('.profile');
    const dropdownContent = document.querySelector('.dropdown-content');

    if (!profile || !dropdownContent) {
        console.error('Dropdown elements not found');
        return;
    }

    profile.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', (e) => {
        if (!profile.contains(e.target) && !dropdownContent.contains(e.target)) {
            dropdownContent.style.display = 'none';
        }
    });
});