// gsap-3d.js
// 3D layered perspective: mouse tilt, idle float, and scroll-triggered reveals

(function () {
  // safety: ensure GSAP & ScrollTrigger loaded
  if (typeof gsap === "undefined") {
    console.error("GSAP not loaded");
    return;
  }
  gsap.registerPlugin(ScrollTrigger);

  // Selectors
  const perspective = document.querySelector(".perspective");
  const layers = Array.from(document.querySelectorAll(".layer"));

  // Map a mouse point to rotation and translation for each layer
  function handlePointerMove(e) {
    const bounds = perspective.getBoundingClientRect();
    const cx = bounds.left + bounds.width / 2;
    const cy = bounds.top + bounds.height / 2;
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;

    // normalize [-1,1]
    const nx = dx / (bounds.width / 2);
    const ny = dy / (bounds.height / 2);

    // limit
    const limit = 0.35;
    const rx = Math.max(-limit, Math.min(limit, -ny)); // invert for natural tilt
    const ry = Math.max(-limit, Math.min(limit, nx));

    // apply transforms per layer depth
    layers.forEach((layer) => {
      const depth = Number(layer.dataset.depth) || 0.3;
      const rotX = rx * (15 * depth); // degrees
      const rotY = ry * (22 * depth);

      const translateZ = (depth - 0.35) * 80; // small Z shift per layer
      gsap.to(layer, {
        duration: 0.45,
        ease: "power3.out",
        rotateX: rotX,
        rotateY: rotY,
        z: translateZ
      });
    });
  }

  // Mouse leave: return to neutral
  function handlePointerLeave() {
    layers.forEach((layer) => {
      gsap.to(layer, { duration: 0.9, ease: "elastic.out(1,0.6)", rotateX: 0, rotateY: 0, z: 0 });
    });
  }

  // Idle floating timeline for organic motion
  function startIdleFloat() {
    layers.forEach((layer, i) => {
      const d = 1 + i * 0.6;
      gsap.to(layer, {
        y: "+=" + (8 + i * 4),
        duration: 3 + i,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 0.2 * i
      });
      gsap.to(layer, {
        rotationZ: "+=" + (1 + i * 0.6),
        duration: 6 + i,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 0.2 * i
      });
    });
  }

  // Entrance 3D stagger animation when user scrolls to stage
  function entranceAnimation() {
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: ".perspective-stage",
        start: "top 80%",
        toggleActions: "play none none reverse"
      }
    });

    // cards come forward in 3D with staggered z translation and fade
    tl.fromTo(".layer--back", { z: -220, opacity: 0 }, { z: -90, opacity: 1, duration: 0.9, ease: "power3.out" }, 0);
    tl.fromTo(".layer--mid", { z: -60, opacity: 0 }, { z: -20, opacity: 1, duration: 0.9, ease: "power3.out" }, 0.08);
    tl.fromTo(".layer--front", { z: 10, opacity: 0 }, { z: 60, opacity: 1, duration: 1, ease: "power4.out" }, 0.16);

    // small pop for front card
    tl.fromTo(".card--front", { scale: 0.95 }, { scale: 1.03, duration: 0.45, ease: "back.out(1.4)" }, "-=0.3");
    tl.to(".card--front", { scale: 1, duration: 0.5, ease: "power2.out" });
  }

  // Hook up events
  function attachEvents() {
    // pointermove on desktop
    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseleave", handlePointerLeave);
    // mobile: use device orientation if available (optional)
    if (window.DeviceOrientationEvent) {
      window.addEventListener("deviceorientation", (ev) => {
        // simple mapping of beta/gamma to small tilt
        const gamma = ev.gamma || 0; // left-right [-90,90]
        const beta = ev.beta || 0;   // front-back [-180,180]
        const fakeEvent = { clientX: window.innerWidth / 2 + gamma * 10, clientY: window.innerHeight / 2 - beta * 6 };
        handlePointerMove(fakeEvent);
      });
    }
  }

  // Initialize
  function init() {
    // start idle motion
    startIdleFloat();
    // entrance on scroll
    entranceAnimation();
    // events
    attachEvents();
  }

  // run after small timeout so layout stable
  window.addEventListener("load", () => setTimeout(init, 120));
})();
