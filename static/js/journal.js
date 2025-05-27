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

  quill.on('text-change', () => {
    const text = quill.getText().trim();
    const wordCount = text ? text.split(/\s+/).length : 0;
    wordCountElement.textContent = `${wordCount} words`;
  });

  window.saveJournal = function() {
    const content = quill.root.innerHTML;
    console.log("Journal Content:", content);
    alert("Journal saved (check console)");
  };
});