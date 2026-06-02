// Micro interactivity: elevate buttons on pointer device
document.addEventListener('pointerdown', (e) => {
  const btn = e.target.closest('.btn-primary, .btn-secondary');
  if(!btn) return;
  btn.style.transform = 'translateY(0)';
  setTimeout(()=> btn.style.transform = '', 120);
});

// Slight entrance animation for cards
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.gmail-hero, .rule-item');
  cards.forEach((c, i) => {
    c.style.opacity = '0';
    c.style.transform = 'translateY(8px)';
    setTimeout(() => {
      c.style.transition = 'opacity .35s ease, transform .35s ease';
      c.style.opacity = '1';
      c.style.transform = 'translateY(0)';
    }, 80 + i * 50);
  });
});
