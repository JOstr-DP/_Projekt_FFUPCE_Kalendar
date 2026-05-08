(() => {
  const overlay = document.getElementById('loading-overlay');
  const forms = document.querySelectorAll('form[data-loading-form="1"]');

  forms.forEach((form) => {
    form.addEventListener('submit', () => {
      if (overlay) {
        overlay.hidden = false;
      }
    });
  });
})();
