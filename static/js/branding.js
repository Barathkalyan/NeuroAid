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