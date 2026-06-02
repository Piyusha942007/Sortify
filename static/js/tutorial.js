// Guided tour using Intro.js
function startTutorial() {
  introJs().setOptions({
    showProgress: true,
    showBullets: false,
    exitOnOverlayClick: false,
    nextLabel: 'Next →',
    prevLabel: '← Back',
    doneLabel: 'Finish',
    overlayOpacity: 0.5,
  }).start();
}

// Little helper toast
function toast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 1400);
}

// Auto-toast after returning from actions that redirect back here
(function () {
  // naive examples; tweak if needed
  if (window.location.search.includes('ran=1')) toast('All rules ran successfully');
})();
