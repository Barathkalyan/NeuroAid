document.addEventListener('DOMContentLoaded', () => {
  const quill = new Quill('#editor', {
    theme: 'snow',
    placeholder: 'Write your thoughts here...',
    modules: {
      toolbar: [
        [{ 'header': [1, 2, false] }],
        ['bold', 'italic', 'underline'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        ['link'],
        ['clean']
      ]
    }
  });

  const wordCountElement = document.querySelector('.word-count');
  const journalForm = document.getElementById('journal-form');
  const journalContentInput = document.getElementById('journal-content');

  quill.on('text-change', () => {
    const text = quill.getText().trim();
    const wordCount = text ? text.split(/\s+/).length : 0;
    wordCountElement.textContent = `${wordCount} words`;
  });

    // DELETE ENTRY BUTTONS
  document.querySelectorAll('.delete-entry-btn').forEach(button => {
    button.addEventListener('click', async (event) => {
      const entryId = event.target.getAttribute('data-id');
      if (confirm('Are you sure you want to delete this journal entry?')) {
        try {
          const response = await fetch(`/delete_entry/${entryId}`, {
            method: 'DELETE',
          });

          if (response.ok) {
            // Remove the entry card from DOM
            const card = event.target.closest('.entry-card');
            card.remove();
          } else {
            alert('Failed to delete entry.');
          }
        } catch (err) {
          console.error('Error deleting entry:', err);
          alert('Something went wrong.');
        }
      }
    });
  });


  journalForm.addEventListener('submit', (event) => {
    journalContentInput.value = quill.root.innerHTML;
  });
});