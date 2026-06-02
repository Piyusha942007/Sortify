gsap.from(".layer-1", {
  y: 60,
  opacity: 0,
  duration: 1.5,
  ease: "power4.out"
});
gsap.from(".layer-2", {
  y: 80,
  opacity: 0,
  duration: 1.8,
  ease: "power4.out"
});
gsap.from(".layer-3", {
  y: 100,
  opacity: 0,
  duration: 2,
  ease: "power4.out"
});

gsap.from(".overlay", {
  opacity: 0,
  y: 30,
  duration: 1.5,
  delay: 0.5,
  ease: "power2.out"
});

// Mouse-based parallax
document.addEventListener("mousemove", (e) => {
  const x = (e.clientX / window.innerWidth - 0.5) * 30;
  const y = (e.clientY / window.innerHeight - 0.5) * 30;
  
  gsap.to(".layer-1", { rotationY: x / 4, rotationX: -y / 4, duration: 1 });
  gsap.to(".layer-2", { rotationY: x / 6, rotationX: -y / 6, duration: 1 });
  gsap.to(".layer-3", { rotationY: x / 8, rotationX: -y / 8, duration: 1 });
});
