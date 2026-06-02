// Animate cards in 3D motion
gsap.from(".card", {
  opacity: 0,
  y: 80,
  duration: 1.6,
  stagger: 0.2,
  ease: "power4.out"
});

// Mouse-based parallax effect
document.addEventListener("mousemove", (e) => {
  const x = (e.clientX / window.innerWidth - 0.5) * 30;
  const y = (e.clientY / window.innerHeight - 0.5) * 30;

  gsap.to(".card-rules", { rotationY: x / 4, rotationX: -y / 4, duration: 1 });
  gsap.to(".card-inbox", { rotationY: x / 3, rotationX: -y / 3, duration: 1 });
  gsap.to(".card-insights", { rotationY: x / 5, rotationX: -y / 5, duration: 1 });
});

// Subtle floating animation
gsap.to(".card", {
  y: "+=10",
  duration: 2,
  yoyo: true,
  repeat: -1,
  ease: "sine.inOut",
  stagger: 0.3
});
