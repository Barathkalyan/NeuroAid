document.addEventListener('DOMContentLoaded', () => {
    const quoteText = document.querySelector('.quote-text');
    if (!quoteText) {
        console.error('Quote text element not found');
        return;
    }
    try {
        const quotes = [
            "You are stronger than you know.",
            "Every day is a new opportunity to grow.",
            "Take a deep breath and keep moving forward.",
            "Your mind is a powerful tool—use it wisely.",
            "Small steps lead to big changes.",
            "Embrace your journey with kindness.",
            "You are enough, just as you are.",
            "Progress, not perfection, is the goal.",
            "Find joy in the little moments.",
            "Your resilience is your superpower."
        ];
        const today = new Date();
        const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
        const quoteIndex = dayOfYear % quotes.length;
        quoteText.textContent = `"${quotes[quoteIndex]}"`;
        quoteText.style.display = 'block'; // Ensure visibility
    } catch (error) {
        console.error('Error setting quote:', error);
        quoteText.textContent = '"Keep going, you’ve got this!"';
    }
});